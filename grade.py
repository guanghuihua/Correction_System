"""
批改流程：
  1. qwen-vl-max → OCR识别学生手写内容
  2. qwen-max    → 对照预设题目批改（不需要重新理解题目）
"""
import json
import os
from openai import OpenAI
from config import QWEN_BASE_URL, QWEN_GRADE_API_KEY, QWEN_GRADE_MODEL, SUBJECT
from ocr import ocr_pages

grade_client = OpenAI(api_key=QWEN_GRADE_API_KEY, base_url=QWEN_BASE_URL)

# 有题目时使用（老师预设）
GRADE_PROMPT_WITH_HW = """你是一位{subject}教师，请批改学生作业。

{homework_text}

---
【学生作答内容（OCR识别，共{n_pages}页）】
{ocr_text}

---
请逐题对照题目批改学生答案，只返回如下JSON（不要任何其他文字）：
{{
  "problems": [
    {{
      "problem_number": "第X题",
      "problem_summary": "题目简述（不超过20字）",
      "student_score": 数字或null,
      "full_score": 数字或null,
      "is_correct": true或false,
      "error_type": "无错误" 或 "计算错误" 或 "概念错误" 或 "步骤缺失" 或 "思路错误" 或 "其他",
      "errors": ["错误描述"],
      "comments": "点评（1句）"
    }}
  ],
  "total_score": 数字或null,
  "estimated_max": 数字或null,
  "overall_comment": "总体评价（2句）",
  "mastery_level": "优秀" 或 "良好" 或 "中等" 或 "待提高",
  "key_weaknesses": ["薄弱点1", "薄弱点2"]
}}"""

# 无题目时使用（AI自行判断题目）
GRADE_PROMPT_NO_HW = """你是一位{subject}教师，请批改学生作业。

【学生作答内容（OCR识别，共{n_pages}页）】
{ocr_text}

请逐题批改，只返回如下JSON（不要任何其他文字）：
{{
  "problems": [
    {{
      "problem_number": "第X题",
      "problem_summary": "题目简述（不超过20字）",
      "student_score": 数字或null,
      "full_score": 数字或null,
      "is_correct": true或false,
      "error_type": "无错误" 或 "计算错误" 或 "概念错误" 或 "步骤缺失" 或 "思路错误" 或 "其他",
      "errors": ["错误描述"],
      "comments": "点评（1句）"
    }}
  ],
  "total_score": 数字或null,
  "estimated_max": 数字或null,
  "overall_comment": "总体评价（2句）",
  "mastery_level": "优秀" 或 "良好" 或 "中等" 或 "待提高",
  "key_weaknesses": ["薄弱点1", "薄弱点2"]
}}"""


def _extract_json(raw: str) -> str:
    """从模型输出中提取JSON字符串"""
    # 去掉 markdown 代码块
    if "```" in raw:
        for block in raw.split("```"):
            block = block.strip().lstrip("json").strip()
            if block.startswith("{"):
                raw = block
                break
    # 提取最外层 JSON 对象
    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start >= 0 and end > start:
        return raw[start:end]
    return raw


def grade_one(image_path, student_name: str = None, homework_name: str = None) -> dict:
    """
    批改单份作业。
    image_path:    单张路径或路径列表
    student_name:  学生姓名
    homework_name: 作业题目名称（已用 homework.save_homework() 保存的），
                   传入后批改更准确且省token；不传则AI自行判断题目
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
    if homework_name:
        from homework import get_homework_text
        try:
            hw_text = get_homework_text(homework_name)
            prompt = GRADE_PROMPT_WITH_HW.format(
                subject=SUBJECT, homework_text=hw_text,
                n_pages=len(image_paths), ocr_text=ocr_text,
            )
        except FileNotFoundError as e:
            print(f"\n[警告] {e}，改用无题目模式")
            prompt = GRADE_PROMPT_NO_HW.format(
                subject=SUBJECT, n_pages=len(image_paths), ocr_text=ocr_text,
            )
    else:
        prompt = GRADE_PROMPT_NO_HW.format(
            subject=SUBJECT, n_pages=len(image_paths), ocr_text=ocr_text,
        )

    try:
        resp = grade_client.chat.completions.create(
            model=QWEN_GRADE_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=3000,
        )
        raw = resp.choices[0].message.content.strip()
        raw = _extract_json(raw)
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


def grade_batch(image_paths: list, student_names: list = None,
                homework_name: str = None) -> list:
    results = []
    for i, path in enumerate(image_paths):
        name = student_names[i] if student_names and i < len(student_names) else None
        print(f"[{i+1}/{len(image_paths)}]", end=" ")
        results.append(grade_one(path, name, homework_name=homework_name))
    return results
