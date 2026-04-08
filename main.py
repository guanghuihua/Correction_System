"""
作业批改系统 - 主入口

用法：
  micromamba run -n base python main.py                    # 从手机拉照片 + 批改 + 生成报告
  micromamba run -n base python main.py --local            # 只用本地photos/目录中已有的照片
  micromamba run -n base python main.py --names 张三 李四   # 手动指定学生姓名（按文件名顺序）
  micromamba run -n base python main.py --title "第3次作业"  # 自定义报告标题
"""
import argparse
import os
import sys
from fetch_photos import pull_photos, get_local_photos
from grade import grade_batch
from report import generate_report
from config import ANTHROPIC_API_KEY


def main():
    parser = argparse.ArgumentParser(description="AI作业批改系统")
    parser.add_argument("--local", action="store_true", help="不从手机拉取，直接用本地photos/目录")
    parser.add_argument("--names", nargs="*", help="学生姓名列表（按文件名顺序）")
    parser.add_argument("--title", default=None, help="报告标题")
    parser.add_argument("--limit", type=int, default=None, help="最多批改N份（测试用）")
    args = parser.parse_args()

    print("=" * 50)
    print("  AI 作业批改系统")
    print("=" * 50)

    # 1. 获取照片
    if not args.local:
        print("\n[步骤1] 从手机拉取照片...")
        pull_photos()
    else:
        print("\n[步骤1] 使用本地照片（跳过手机同步）")

    photos = get_local_photos()
    if not photos:
        print("[错误] photos/ 目录下没有图片，请先拍照或拉取照片")
        sys.exit(1)

    if args.limit:
        photos = photos[:args.limit]

    print(f"\n将批改 {len(photos)} 份作业：")
    for i, p in enumerate(photos):
        name = args.names[i] if args.names and i < len(args.names) else os.path.splitext(os.path.basename(p))[0]
        print(f"  {i+1}. {name}  ({os.path.basename(p)})")

    confirm = input("\n确认开始批改？(y/n): ").strip().lower()
    if confirm != "y":
        print("已取消")
        sys.exit(0)

    # 2. 批改
    print("\n[步骤2] 开始AI批改...")
    results = grade_batch(photos, args.names)

    # 3. 生成报告
    print("\n[步骤3] 生成PDF报告...")
    pdf_path = generate_report(results, title=args.title)

    print("\n" + "=" * 50)
    print(f"批改完成！")
    print(f"报告位置: {pdf_path}")
    print("=" * 50)

    # 打印简要统计
    from collections import Counter
    mastery = Counter(r.get("mastery_level", "未知") for r in results if not r.get("error"))
    print("\n掌握程度分布：")
    for level in ["优秀", "良好", "中等", "待提高"]:
        if level in mastery:
            print(f"  {level}: {mastery[level]} 人")

    failed = [r for r in results if r.get("error")]
    if failed:
        print(f"\n[注意] {len(failed)} 份批改失败，请人工核查：")
        for r in failed:
            print(f"  - {r['student_name']}: {r['error']}")


if __name__ == "__main__":
    main()
