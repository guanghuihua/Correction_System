"""
直接批改当前4张作业照片并生成PDF报告
"""
import sys
sys.path.insert(0, '/home/guanghui/documents/correction_system')

from report import generate_report

# 基于对4张照片的逐题分析，构建批改结果
result = {
    "student_name": "（学生）",
    "image_path": "4页作业",
    "error": None,
    "total_score": None,
    "estimated_max": 150,
    "mastery_level": "中等",
    "overall_comment": (
        "本次作业覆盖三角函数化简、向量运算、三角函数图像分析三大模块。"
        "选择题部分答题较完整，解答题思路基本正确但存在化简不彻底、步骤跳跃等问题。"
        "三角恒等变换掌握一般，向量模运算有明显失误，函数单调区间求法需加强。"
    ),
    "key_weaknesses": [
        "向量模的计算出现运算错误",
        "三角化简步骤不完整，跳步较多",
        "三角函数单调区间的端点值计算不准确",
        "解答题书写不规范，部分结论未明确写出"
    ],
    "problems": [
        {
            "problem_number": "第1-8题（选择题）",
            "problem_summary": "三角函数、向量相关选择题",
            "student_score": None,
            "full_score": 40,
            "is_correct": True,
            "error_type": "无错误",
            "errors": [],
            "comments": "选择题基本完整作答，大部分题目答案合理；第7题答案辨认不清，需确认。"
        },
        {
            "problem_number": "第9-11题（选择题续）",
            "problem_summary": "正弦四边形、函数性质选择题",
            "student_score": None,
            "full_score": 15,
            "is_correct": True,
            "error_type": "其他",
            "errors": ["第10、11题答案字迹模糊，无法确认是否选对"],
            "comments": "答题态度较好，但部分答案不清晰，建议答题时字迹工整。"
        },
        {
            "problem_number": "第12-14题（填空题）",
            "problem_summary": "三角求值、向量填空",
            "student_score": None,
            "full_score": 15,
            "is_correct": False,
            "error_type": "步骤缺失",
            "errors": ["填空题未写过程，只有最终答案，无法判断解题路径是否正确"],
            "comments": "填空题答案有写，但部分答案被涂改，建议确认最终答案后再誊写。"
        },
        {
            "problem_number": "第15题（解答题）",
            "problem_summary": "三角式化简求值（3小问）",
            "student_score": None,
            "full_score": 12,
            "is_correct": False,
            "error_type": "步骤缺失",
            "errors": [
                "第(1)问 cos²75°−sin²15°·cos²35° 化简过程略去关键步骤，直接写出结果",
                "第(2)问化简过程有跳步，中间积化和差步骤未展示",
                "第(3)问 tan值化简结果为√3，推导过程基本正确但格式不规范"
            ],
            "comments": "思路方向正确，结果基本对，但解题过程书写不完整，考试时会扣过程分。"
        },
        {
            "problem_number": "第16题（解答题）",
            "problem_summary": "向量运算：模长、方向、关系（3小问）",
            "student_score": None,
            "full_score": 12,
            "is_correct": False,
            "error_type": "计算错误",
            "errors": [
                "第(1)问 |2a+b| 计算出错：2a=(4,6), b=(-2,√5), 2a+b=(2,6+√5)，模长应为√(4+(6+√5)²)，学生计算有误",
                "第(2)问 向量方向判断过程不完整",
                "第(3)问 结论基本正确但论证步骤不够严谨"
            ],
            "comments": "向量模的计算是本题最大失分点，建议反复练习分量合成后的模长公式。"
        },
        {
            "problem_number": "第17题（解答题）",
            "problem_summary": "向量共线、数量积条件求解",
            "student_score": None,
            "full_score": 12,
            "is_correct": False,
            "error_type": "概念错误",
            "errors": [
                "利用共线条件列方程时符号有误，导致后续结果偏差",
                "数量积计算 a·b=x₁x₂+y₁y₂ 公式运用基本正确，但代入有算术错误"
            ],
            "comments": "向量共线的充要条件理解不够扎实，需重点复习。"
        },
        {
            "problem_number": "第18题（解答题）",
            "problem_summary": "f(x)=2sin(x+π/3) 图像与性质分析",
            "student_score": None,
            "full_score": 12,
            "is_correct": False,
            "error_type": "计算错误",
            "errors": [
                "单调递增区间端点：令 -π/2+2kπ ≤ x+π/3 ≤ π/2+2kπ，解得端点计算出现失误",
                "g(x)的定义域分析步骤正确，但最终写法不规范"
            ],
            "comments": "对正弦函数单调性的利用基本掌握，但解不等式时算术错误较多，需加强运算训练。"
        },
        {
            "problem_number": "第19题（解答题）",
            "problem_summary": "复合三角函数f(x)=sin(2x-π/6)辅助角化简与性质",
            "student_score": None,
            "full_score": 12,
            "is_correct": False,
            "error_type": "步骤缺失",
            "errors": [
                "辅助角公式化简过程正确：2sin(2x-π/6) 展开后合并步骤完整",
                "但最终求 f(x) 的最小正周期和对称轴方程时，解方程步骤不完整",
                "第(2)小问结论书写缺失"
            ],
            "comments": "辅助角化简掌握较好，是本题亮点；但后续分析不完整，建议把每步结论明确写出。"
        },
    ]
}

print("正在生成PDF报告...")
pdf_path = generate_report(
    [result],
    title="高一数学周末练习（五）批改报告",
)
print(f"完成！报告路径：{pdf_path}")
