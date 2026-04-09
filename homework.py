"""
作业题目管理
老师提前录入题目内容，批改时直接调用，不再让AI重新识别题目
"""
import os
import json
from config import HOMEWORK_DIR


def save_homework(name: str, questions: str, scoring: str = ""):
    """
    保存一次作业的题目。
    name:      作业名称，如 "向量数量积第5-10题"
    questions: 题目内容（文字描述）
    scoring:   评分标准（可选）
    """
    hw = {"name": name, "questions": questions, "scoring": scoring}
    path = os.path.join(HOMEWORK_DIR, f"{name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(hw, f, ensure_ascii=False, indent=2)
    print(f"[已保存] {path}")
    return path


def load_homework(name: str) -> dict:
    """按名称加载作业题目"""
    path = os.path.join(HOMEWORK_DIR, f"{name}.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"找不到作业题目：{path}\n请先用 save_homework() 录入题目")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def list_homework() -> list:
    """列出所有已保存的作业题目"""
    files = [f[:-5] for f in os.listdir(HOMEWORK_DIR) if f.endswith(".json")]
    return sorted(files)


def get_homework_text(name: str) -> str:
    """返回题目的完整文字，用于注入批改prompt"""
    hw = load_homework(name)
    text = f"【作业题目：{hw['name']}】\n\n{hw['questions']}"
    if hw.get("scoring"):
        text += f"\n\n【评分标准】\n{hw['scoring']}"
    return text
