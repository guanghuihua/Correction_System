"""
调用 claude CLI（多模态方式）批改作业照片，返回结构化批改结果
"""
import subprocess
import json
import base64
import os
from pathlib import Path
from config import SUBJECT


GRADE_PROMPT = """你是一位经验丰富的{subject}教师，正在批改学生的解答题作业。

我会发给你该学生作业的全部{n_pages}张照片，请综合所有页面完整批改，不要遗漏任何一道题。
特别注意：题目可能在某一页，答案在另一页，请跨页对照后再判断对错。

请只返回如下JSON格式（不要任何其他文字，不要markdown代码块）：
{{
  "problems": [
    {{
      "problem_number": "第1题",
      "problem_summary": "题目简述（不超过30字）",
      "student_score": 数字或null,
      "full_score": 数字或null,
      "is_correct": true或false,
      "error_type": "无错误" 或 "计算错误" 或 "概念错误" 或 "步骤缺失" 或 "思路错误" 或 "其他",
      "errors": ["错误描述1"],
      "comments": "该题点评（1-2句）"
    }}
  ],
  "total_score": 数字或null,
  "estimated_max": 数字或null,
  "overall_comment": "总体评价（2-3句，指出主要问题和优点）",
  "mastery_level": "优秀" 或 "良好" 或 "中等" 或 "待提高",
  "key_weaknesses": ["主要薄弱点1", "主要薄弱点2"]
}}

注意：如果照片模糊无法识别，overall_comment中说明，mastery_level填"未知"。
"""


def _get_media_type(image_path: str) -> str:
    suffix = Path(image_path).suffix.lower()
    return {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}.get(suffix, "image/jpeg")


def _call_claude_with_image(image_path: str, prompt: str, timeout: int = 120) -> str:
    """将单张图片以base64多模态方式传给claude -p，返回文本输出"""
    return _call_claude_with_images([image_path], prompt, timeout)


def _call_claude_with_images(image_paths: list, prompt: str, timeout: int = 120) -> str:
    """将多张图片一次性打包传给claude -p，返回文本输出"""
    content = []
    for path in image_paths:
        with open(path, "rb") as f:
            img_data = base64.b64encode(f.read()).decode()
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": _get_media_type(path),
                "data": img_data,
            }
        })
    content.append({"type": "text", "text": prompt})

    message = json.dumps({
        "type": "user",
        "message": {"role": "user", "content": content}
    })

    result = subprocess.run(
        ["claude", "-p", "--dangerously-skip-permissions",
         "--input-format", "stream-json",
         "--output-format", "stream-json",
         "--verbose"],
        input=message, capture_output=True, text=True, timeout=timeout
    )

    # 从stream-json输出中提取文本
    text_parts = []
    for line in result.stdout.splitlines():
        try:
            obj = json.loads(line)
            if obj.get("type") == "assistant":
                for block in obj.get("message", {}).get("content", []):
                    if block.get("type") == "text":
                        text_parts.append(block["text"])
        except Exception:
            continue

    output = "".join(text_parts).strip()
    if not output:
        raise ValueError(f"claude无输出. stderr: {result.stderr[:300]}")
    return output


def grade_one(image_path, student_name: str = None) -> dict:
    """
    批改单份作业（支持单张图片路径或多张图片路径列表），返回结构化结果。
    多页作业请传列表，Claude会综合所有页面一起批改。
    """
    if isinstance(image_path, str):
        image_paths = [image_path]
    else:
        image_paths = list(image_path)

    label = os.path.basename(image_paths[0]) if len(image_paths) == 1 else f"{len(image_paths)}页作业"
    print(f"  批改: {label} ...", end=" ", flush=True)

    prompt = GRADE_PROMPT.format(subject=SUBJECT, n_pages=len(image_paths))

    try:
        raw = _call_claude_with_images(image_paths, prompt, timeout=600)

        # 提取JSON
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start >= 0 and end > start:
            raw = raw[start:end]

        data = json.loads(raw)
        data["student_name"] = student_name or os.path.splitext(os.path.basename(image_paths[0]))[0]
        data["image_path"] = image_paths[0]
        data["error"] = None
        print("OK")
        return data

    except json.JSONDecodeError as e:
        print("JSON解析失败")
        return _error_result(student_name, image_paths[0], f"JSON解析失败: {e}\n原始: {raw[:300]}")
    except subprocess.TimeoutExpired:
        print("超时")
        return _error_result(student_name, image_paths[0], "批改超时（>240秒）")
    except Exception as e:
        print("失败")
        return _error_result(student_name, image_paths[0], str(e))


def _error_result(name, path, error_msg):
    return {
        "student_name": name or os.path.basename(path),
        "image_path": path,
        "error": error_msg,
        "problems": [],
        "overall_comment": "批改失败，请人工核查",
        "mastery_level": "未知",
        "key_weaknesses": [],
        "total_score": None,
        "estimated_max": None,
    }


def grade_batch(image_paths: list, student_names: list = None) -> list:
    """批量批改，返回结果列表"""
    results = []
    total = len(image_paths)
    for i, path in enumerate(image_paths):
        name = student_names[i] if student_names and i < len(student_names) else None
        print(f"[{i+1}/{total}]", end=" ")
        result = grade_one(path, name)
        results.append(result)
    return results
