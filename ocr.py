"""
使用 Qwen VL 识别作业照片，返回文字内容
"""
import base64
import os
from pathlib import Path
from openai import OpenAI
from config import QWEN_API_KEY, QWEN_BASE_URL, QWEN_VL_MODEL

client = OpenAI(api_key=QWEN_API_KEY, base_url=QWEN_BASE_URL)

OCR_PROMPT = """请将这张作业照片中的所有内容完整转录，包括：
- 题目编号和题干
- 学生的解题过程和答案
- 所有数学公式（用文字描述，如 sin²x、√3、π/6、向量a=(2,3)）

格式要求：
- 每题用"【第X题】"开头
- 题干用"题目："标注
- 学生作答用"作答："标注
- 字迹模糊处标注"[模糊]"
- 只转录，不评价

直接输出转录内容。"""


def _encode(image_path: str) -> tuple[str, str]:
    suffix = Path(image_path).suffix.lower()
    mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}.get(suffix, "image/jpeg")
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode(), mime


def ocr_pages(image_paths: list[str]) -> str:
    """
    用 Qwen VL 识别多张照片，返回合并的文字内容。
    多页一次性发送，保留跨页上下文。
    """
    content = []
    for i, path in enumerate(image_paths, 1):
        data, mime = _encode(path)
        if len(image_paths) > 1:
            content.append({"type": "text", "text": f"[第{i}页]"})
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:{mime};base64,{data}"}
        })
    content.append({"type": "text", "text": OCR_PROMPT})

    resp = client.chat.completions.create(
        model=QWEN_VL_MODEL,
        messages=[{"role": "user", "content": content}],
        max_tokens=4096,
    )
    return resp.choices[0].message.content.strip()


def ocr_one(image_path: str) -> str:
    return ocr_pages([image_path])
