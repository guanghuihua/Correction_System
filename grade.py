"""
批改流程：
  1. qwen-vl-max-latest → OCR识别图片，提取文字
  2. qwen3.6-plus       → 根据文字推理批改，输出JSON
"""
import json
import os
from openai import OpenAI
from config import (QWEN_BASE_URL, QWEN_GRADE_API_KEY,
                    QWEN_GRADE_MODEL, SUBJECT)
from ocr import ocr_pages

grade_client = OpenAI(api_key=QWEN_GRADE_API_KEY, base_url=QWEN_BASE_URL)

GRADE_PROMPT = """你是一位经验丰富的{subject}教师，请批改以下学生作业。

作业内容（共{n_pages}页，已OCR识别）：
{ocr_text}

要求：
- 逐题批改，不遗漏任何题目
- 注意跨页对照题目与答案
- 对每题判断是否正确，指出具体错误

只返回如下JSON（不要任何其他文字，不要markdown代码块）：
{{
  "problems": [
    {{
      "problem_number": "第X题",
      "problem_summary": "题目简述（不超过30字）",
      "student_score": 数字或null,
      "full_score": 数字或null,
      "is_correct": true或false,
      "error_type": "无错误" 或 "计算错误" 或 "概念错误" 或 "步骤缺失" 或 "思路错误" 或 "其他",
      "errors": ["错误描述"],
      "comments": "点评（1-2句）"
    }}
  ],
  "total_score": 数字或null,
  "estimated_max": 数字或null,
  "overall_comment": "总体评价（2-3句）",
  "mastery_level": "优秀" 或 "良好" 或 "中等" 或 "待提高",
  "key_weaknesses": ["薄弱点1", "薄弱点2"]
}}"""


def grade_one(image_path, student_name: str = None) -> dict:
    """
    批改单份作业（单张路径或路径列表）。
    Step1: Qwen VL OCR → Step2: qwen3.6-plus 批改
    """
    image_paths = [image_path] if isinstance(image_path, str) else list(image_path)
    name = student_name or os.path.splitext(os.path.basename(image_paths[0]))[0]

    # Step 1: OCR
    print(f"  识别({len(image_paths)}页)...", end=" ", flush=True)
    try:
        ocr_text = ocr_pages(image_paths)
    except Exception as e:
        print("OCR失败")
        return _error_result(name, image_paths[0], f"Qwen OCR失败: {e}")

    # Step 2: 批改
    print("批改...", end=" ", flush=True)
    prompt = GRADE_PROMPT.format(
        subject=SUBJECT,
        n_pages=len(image_paths),
        ocr_text=ocr_text,
    )
    try:
        resp = grade_client.chat.completions.create(
            model=QWEN_GRADE_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
        )
        raw = resp.choices[0].message.content.strip()

        # 去掉 <think>...</think> 推理过程（思考模型）
        while "<think>" in raw and "</think>" in raw:
            s = raw.find("<think>")
            e = raw.find("</think>") + len("</think>")
            raw = (raw[:s] + raw[e:]).strip()

        # 去掉 markdown 代码块
        if "```" in raw:
            for line in raw.split("```"):
                line = line.strip().lstrip("json").strip()
                if line.startswith("{"):
                    raw = line
                    break

        # 提取最外层 JSON 对象
        start = raw.find("{"); end = raw.rfind("}") + 1
        if start >= 0 and end > start:
            raw = raw[start:end]

        data = json.loads(raw)
        data["student_name"] = name
        data["image_path"] = image_paths[0]
        data["error"] = None
        print("OK")
        return data

    except json.JSONDecodeError as e:
        print("JSON解析失败")
        return _error_result(name, image_paths[0], f"JSON解析失败: {e}\n原始: {raw[:300]}")
    except Exception as e:
        print("失败")
        return _error_result(name, image_paths[0], str(e))


def _error_result(name, path, error_msg):
    return {
        "student_name": name, "image_path": path, "error": error_msg,
        "problems": [], "overall_comment": "批改失败，请人工核查",
        "mastery_level": "未知", "key_weaknesses": [],
        "total_score": None, "estimated_max": None,
    }


def grade_batch(image_paths: list, student_names: list = None) -> list:
    results = []
    for i, path in enumerate(image_paths):
        name = student_names[i] if student_names and i < len(student_names) else None
        print(f"[{i+1}/{len(image_paths)}]", end=" ")
        results.append(grade_one(path, name))
    return results
