"""
生成PDF批改报告（含每位学生详情 + 全班分析）
"""
import os
from datetime import datetime
from collections import Counter
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from config import OUTPUT_DIR, SUBJECT, PASS_SCORE

# 注册中文字体
FONT_PATHS = [
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
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

# A4可用宽度 = 210mm - 左2cm - 右2cm = 17cm
PAGE_W = 17 * cm

MASTERY_COLOR = {
    "优秀":  colors.HexColor("#2e7d32"),
    "良好":  colors.HexColor("#1565c0"),
    "中等":  colors.HexColor("#e65100"),
    "待提高": colors.HexColor("#c62828"),
    "未知":  colors.grey,
}


# ── 样式 ────────────────────────────────────────────────────────────────────

def make_styles():
    def ps(name, **kw):
        kw.setdefault("leading", 16)
        return ParagraphStyle(name, fontName=CN_FONT, **kw)

    return {
        "title":       ps("title",    fontSize=18, alignment=TA_CENTER,
                          spaceAfter=6,  textColor=colors.HexColor("#1a1a2e")),
        "subtitle":    ps("subtitle", fontSize=11, alignment=TA_CENTER,
                          spaceAfter=12, textColor=colors.HexColor("#666666")),
        "h1":          ps("h1",       fontSize=13, spaceBefore=14, spaceAfter=6,
                          textColor=colors.HexColor("#16213e")),
        "h2":          ps("h2",       fontSize=11, spaceBefore=10, spaceAfter=4,
                          textColor=colors.HexColor("#0f3460")),
        "body":        ps("body",     fontSize=10, spaceAfter=4),
        "small":       ps("small",    fontSize=9,  textColor=colors.HexColor("#555555")),
        "tag_err":     ps("tag_err",  fontSize=10, textColor=colors.HexColor("#c62828")),
        # 表格内专用（无 spaceBefore/spaceAfter，行距紧凑）
        "cell":        ps("cell",     fontSize=9,  leading=13),
        "cell_hdr":    ps("cell_hdr", fontSize=9,  leading=13,
                          textColor=colors.white),
        "cell_center": ps("cell_center", fontSize=9, leading=13,
                          alignment=TA_CENTER),
        "cell_red":    ps("cell_red", fontSize=9,  leading=13,
                          textColor=colors.HexColor("#c62828")),
        "cell_green":  ps("cell_green", fontSize=9, leading=13,
                          textColor=colors.HexColor("#2e7d32")),
    }


def P(text, style):
    """快捷包装：把字符串转成表格内可换行的Paragraph"""
    text = str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return Paragraph(text, style)


# ── 通用表格样式 ─────────────────────────────────────────────────────────────

def base_table_style(has_header=True, alt_color=colors.HexColor("#f5f5f5")):
    cmds = [
        ("FONTNAME",      (0, 0), (-1, -1), CN_FONT),
        ("FONTSIZE",      (0, 0), (-1, -1), 9),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("ALIGN",         (0, 0), (-1, -1), "LEFT"),
        ("GRID",          (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
    ]
    if has_header:
        cmds += [
            ("BACKGROUND",  (0, 0), (-1, 0), colors.HexColor("#16213e")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, alt_color]),
        ]
    return TableStyle(cmds)


# ── 学生报告 ─────────────────────────────────────────────────────────────────

def build_student_section(result: dict, styles: dict) -> list:
    story = []
    s = styles
    name    = result.get("student_name", "未知")
    mastery = result.get("mastery_level", "未知")
    m_color = MASTERY_COLOR.get(mastery, colors.grey)
    overall = result.get("overall_comment", "")
    problems= result.get("problems", [])
    weaknesses = result.get("key_weaknesses", [])
    error   = result.get("error")

    story.append(Paragraph(f"学生：{name}", s["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cccccc")))
    story.append(Spacer(1, 6))

    if error:
        story.append(Paragraph(f"[批改失败] {error}", s["tag_err"]))
        story.append(Spacer(1, 12))
        return story

    # 概览行：掌握程度 + 得分
    total   = result.get("total_score")
    est_max = result.get("estimated_max")
    score_str = (f"{total}/{est_max}" if (total is not None and est_max is not None)
                 else str(total) if total is not None else "—")

    def label_p(text, color=colors.HexColor("#555555")):
        return Paragraph(f'<font color="{color.hexval() if hasattr(color,"hexval") else color}">{text}</font>', s["cell"])

    mastery_p = Paragraph(
        f'<font color="#{m_color.hexColor() if hasattr(m_color,"hexColor") else "000000"}">{mastery}</font>',
        s["cell"]
    )
    # 简化：直接用带颜色的style
    mastery_cell = P(mastery, ParagraphStyle("mc", fontName=CN_FONT, fontSize=10,
                                              leading=14, textColor=m_color))

    info_t = Table(
        [["掌握程度", mastery_cell, "得分", P(score_str, s["cell"])]],
        colWidths=[2.8*cm, 3*cm, 2*cm, 3*cm],
    )
    info_t.setStyle(TableStyle([
        ("FONTNAME",      (0, 0), (-1, -1), CN_FONT),
        ("FONTSIZE",      (0, 0), (0, 0), 9),
        ("FONTSIZE",      (2, 0), (2, 0), 9),
        ("TEXTCOLOR",     (0, 0), (0, 0), colors.HexColor("#555555")),
        ("TEXTCOLOR",     (2, 0), (2, 0), colors.HexColor("#555555")),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW",     (0, 0), (-1, -1), 0.4, colors.HexColor("#eeeeee")),
    ]))
    story.append(info_t)
    story.append(Spacer(1, 6))

    # 总体评价 & 薄弱点
    story.append(Paragraph(f"总体评价：{overall}", s["body"]))
    if weaknesses:
        story.append(Paragraph("主要薄弱点：" + "、".join(weaknesses), s["small"]))
    story.append(Spacer(1, 8))

    # 逐题详情表
    if problems:
        story.append(Paragraph("逐题批改：", s["h2"]))

        # 列宽：题号 | 简述 | 得分 | 错误类型 | 点评与错误详情
        col_w = [1.8*cm, 3.5*cm, 1.6*cm, 2.3*cm, 7.8*cm]

        rows = [[
            P("题目",     s["cell_hdr"]),
            P("简述",     s["cell_hdr"]),
            P("得分",     s["cell_hdr"]),
            P("错误类型", s["cell_hdr"]),
            P("点评",     s["cell_hdr"]),
        ]]
        err_rows = []  # 记录有错误的行号（从1开始）

        for i, p in enumerate(problems, start=1):
            sc = f"{p.get('student_score','—')}/{p.get('full_score','—')}"
            err_type = p.get("error_type", "—")
            comments = p.get("comments", "")
            errors   = p.get("errors", [])
            # 把errors拼到点评后面，用换行分隔
            detail = comments
            if errors:
                detail += "\n• " + "\n• ".join(errors)

            is_wrong = not p.get("is_correct", True)
            if is_wrong:
                err_rows.append(i)
                err_style = s["cell_red"]
            else:
                err_style = s["cell"]

            rows.append([
                P(p.get("problem_number", ""), s["cell"]),
                P(p.get("problem_summary", ""), s["cell"]),
                P(sc, s["cell_center"]),
                P(err_type, err_style),
                P(detail, s["cell"]),
            ])

        pt = Table(rows, colWidths=col_w, repeatRows=1)
        ts = base_table_style()
        # 表头居中
        ts.add("ALIGN", (0, 0), (-1, 0), "CENTER")
        pt.setStyle(ts)
        story.append(pt)

    story.append(Spacer(1, 20))
    return story


# ── 全班分析 ─────────────────────────────────────────────────────────────────

def build_class_analysis(results: list, styles: dict) -> list:
    story = []
    s = styles

    story.append(PageBreak())
    story.append(Paragraph("全班完成情况分析", s["title"]))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#16213e")))
    story.append(Spacer(1, 12))

    valid  = [r for r in results if not r.get("error")]
    graded = len(valid)

    # ① 掌握程度分布
    mastery_counts = Counter(r.get("mastery_level", "未知") for r in valid)
    story.append(Paragraph("掌握程度分布", s["h1"]))

    dist_rows = [[P("等级", s["cell_hdr"]), P("人数", s["cell_hdr"]), P("占比", s["cell_hdr"])]]
    for level in ["优秀", "良好", "中等", "待提高", "未知"]:
        cnt = mastery_counts.get(level, 0)
        if cnt == 0:
            continue
        pct = f"{cnt/graded*100:.1f}%" if graded > 0 else "—"
        dist_rows.append([P(level, s["cell"]), P(str(cnt), s["cell_center"]), P(pct, s["cell_center"])])
    dist_rows.append([P("合计", s["cell"]), P(str(graded), s["cell_center"]), P("100%", s["cell_center"])])

    dt = Table(dist_rows, colWidths=[4*cm, 3*cm, 3*cm])
    ts = base_table_style()
    ts.add("BACKGROUND", (0, len(dist_rows)-1), (-1, len(dist_rows)-1), colors.HexColor("#eeeeee"))
    dt.setStyle(ts)
    story.append(dt)
    story.append(Spacer(1, 14))

    # ② 全班共同薄弱点
    all_weaknesses = []
    for r in valid:
        all_weaknesses.extend(r.get("key_weaknesses", []))
    weakness_counts = Counter(all_weaknesses).most_common(8)

    if weakness_counts:
        story.append(Paragraph("全班共同薄弱点（出现频率排序）", s["h1"]))
        wk_rows = [[P("薄弱点", s["cell_hdr"]), P("涉及人数", s["cell_hdr"])]]
        for w, cnt in weakness_counts:
            wk_rows.append([P(w, s["cell"]), P(str(cnt), s["cell_center"])])
        wt = Table(wk_rows, colWidths=[13*cm, 4*cm])
        wt.setStyle(base_table_style())
        story.append(wt)
        story.append(Spacer(1, 14))

    # ③ 得分统计
    scores = [r.get("total_score") for r in valid if r.get("total_score") is not None]
    if scores:
        avg = sum(scores) / len(scores)
        story.append(Paragraph("得分统计", s["h1"]))
        col_w5 = [PAGE_W / 5] * 5
        sc_rows = [
            [P("参与人数", s["cell_hdr"]), P("平均分", s["cell_hdr"]),
             P("最高分",   s["cell_hdr"]), P("最低分", s["cell_hdr"]),
             P("及格人数", s["cell_hdr"])],
            [P(str(len(scores)), s["cell_center"]),
             P(f"{avg:.1f}",     s["cell_center"]),
             P(str(max(scores)), s["cell_center"]),
             P(str(min(scores)), s["cell_center"]),
             P(str(sum(1 for sc in scores if sc >= PASS_SCORE)), s["cell_center"])],
        ]
        st = Table(sc_rows, colWidths=col_w5)
        st.setStyle(base_table_style())
        story.append(st)
        story.append(Spacer(1, 14))

    # ④ 需重点关注的学生
    needs_attention = [r for r in valid if r.get("mastery_level") in ("待提高", "中等")]
    if needs_attention:
        story.append(Paragraph("建议重点关注的学生", s["h1"]))
        att_rows = [[P("姓名", s["cell_hdr"]), P("掌握程度", s["cell_hdr"]), P("主要薄弱点", s["cell_hdr"])]]
        for r in needs_attention:
            att_rows.append([
                P(r.get("student_name", "—"), s["cell"]),
                P(r.get("mastery_level", "—"), s["cell"]),
                P("、".join(r.get("key_weaknesses", [])[:3]) or "—", s["cell"]),
            ])
        att_t = Table(att_rows, colWidths=[3*cm, 3*cm, 11*cm])
        ts = base_table_style(alt_color=colors.HexColor("#fff3e0"))
        att_t.setStyle(ts)
        story.append(att_t)

    return story


# ── 主入口 ────────────────────────────────────────────────────────────────────

def generate_report(results: list, title: str = None, output_path: str = None) -> str:
    if not output_path:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(OUTPUT_DIR, f"批改报告_{ts}.pdf")

    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )

    styles = make_styles()
    story = []

    # 封面
    story.append(Spacer(1, 2*cm))
    story.append(Paragraph(title or f"{SUBJECT}作业批改报告", styles["title"]))
    story.append(Paragraph(f"生成时间：{datetime.now().strftime('%Y年%m月%d日 %H:%M')}", styles["subtitle"]))
    story.append(Paragraph(f"共 {len(results)} 份作业", styles["subtitle"]))
    story.append(Spacer(1, 1*cm))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#16213e")))
    story.append(Spacer(1, 0.5*cm))

    for result in results:
        story.extend(build_student_section(result, styles))

    story.extend(build_class_analysis(results, styles))

    doc.build(story)
    print(f"\n[报告已生成] {output_path}")
    return output_path
