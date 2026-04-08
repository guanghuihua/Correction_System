"""
识别作业照片内容并生成可读的文字预览PDF
让老师直观看到AI识别出的题目和学生答案
"""
import subprocess
import os
import sys
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from config import OUTPUT_DIR

# 中文字体
FONT_PATHS = [
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/mnt/c/Windows/Fonts/msyh.ttc",
    "/mnt/c/Windows/Fonts/simsun.ttc",
]
CN_FONT = "Helvetica"
for fp in FONT_PATHS:
    if os.path.exists(fp):
        try:
            pdfmetrics.registerFont(TTFont("CNFont", fp))
            CN_FONT = "CNFont"
            break
        except Exception:
            continue

EXTRACT_PROMPT = """你的任务是**原文转录**：把照片中所有可识别的文字内容完整抄写出来，包括：
- 试题题目（完整题干）
- 学生填写的答案和解题过程
- 试卷上的任何批注、分数标记

输出格式要求：
- 每道题用"【第X题】"开头
- 题目内容用"题目："标注
- 学生答案/解题过程用"学生作答："标注
- 如果某部分字迹模糊识别不清，用"[模糊]"标注
- 数学公式尽量用文字描述清楚，例如"sin²x"、"√3"、"π/6"
- 不要做任何评价，只做转录

直接输出转录内容，不要任何开头语或解释。"""


def extract_content(image_path: str) -> str:
    """调用claude以多模态方式提取照片中的文字内容"""
    from grade import _call_claude_with_image
    try:
        return _call_claude_with_image(image_path, EXTRACT_PROMPT, timeout=180)
    except Exception as e:
        return f"[识别失败] {e}"


def make_styles():
    base = dict(fontName=CN_FONT, leading=18)
    return {
        "title": ParagraphStyle("title", fontSize=16, alignment=TA_CENTER,
                                 spaceAfter=6, textColor=colors.HexColor("#1a1a2e"), **base),
        "subtitle": ParagraphStyle("subtitle", fontSize=10, alignment=TA_CENTER,
                                    spaceAfter=12, textColor=colors.HexColor("#888888"), **base),
        "page_header": ParagraphStyle("page_header", fontSize=12, spaceBefore=10, spaceAfter=4,
                                       textColor=colors.HexColor("#0f3460"),
                                       backColor=colors.HexColor("#e8f0fe"), **base),
        "content": ParagraphStyle("content", fontSize=10, spaceAfter=3,
                                   leftIndent=8, **base),
        "note": ParagraphStyle("note", fontSize=9, textColor=colors.HexColor("#888888"),
                                alignment=TA_CENTER, **base),
    }


def generate_preview(image_paths: list, student_name: str = "学生", output_path: str = None) -> str:
    """
    对每张照片做内容识别，生成预览PDF
    """
    if not output_path:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(OUTPUT_DIR, f"识别预览_{ts}.pdf")

    styles = make_styles()
    story = []

    # 封面
    story.append(Spacer(1, 2*cm))
    story.append(Paragraph("作业内容识别预览", styles["title"]))
    story.append(Paragraph(f"学生：{student_name}　共{len(image_paths)}页", styles["subtitle"]))
    story.append(Paragraph(f"生成时间：{datetime.now().strftime('%Y年%m月%d日 %H:%M')}", styles["subtitle"]))
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#16213e")))
    story.append(Paragraph(
        "以下内容为AI对照片的文字识别结果，供老师核验识别准确度。",
        styles["note"]
    ))
    story.append(Spacer(1, 0.5*cm))

    for i, path in enumerate(image_paths):
        fname = os.path.basename(path)
        print(f"[{i+1}/{len(image_paths)}] 识别: {fname} ...", end=" ", flush=True)

        story.append(PageBreak())
        story.append(Paragraph(f"第 {i+1} 页　　{fname}", styles["page_header"]))
        story.append(Spacer(1, 6))

        content = extract_content(path)
        print("OK")

        # 按行拆分，保留结构
        for line in content.splitlines():
            line = line.strip()
            if not line:
                story.append(Spacer(1, 4))
                continue
            # 转义reportlab特殊字符
            line = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            story.append(Paragraph(line, styles["content"]))

    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )
    doc.build(story)
    print(f"\n[预览PDF已生成] {output_path}")
    return output_path


if __name__ == "__main__":
    from fetch_photos import get_local_photos
    photos = get_local_photos()
    if not photos:
        print("photos/ 目录下没有图片")
        sys.exit(1)

    print(f"找到 {len(photos)} 张照片，开始识别...\n")
    pdf = generate_preview(photos, student_name="学生")

    # 复制到Windows桌面
    desktop = "/mnt/c/Users/17683/Desktop/识别预览.pdf"
    import shutil
    shutil.copy(pdf, desktop)
    print(f"已复制到桌面：{desktop}")
