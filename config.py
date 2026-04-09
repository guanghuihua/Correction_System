import os

# ADB路径
ADB = "/mnt/c/Users/17683/AppData/Local/Microsoft/WinGet/Packages/Google.PlatformTools_Microsoft.Winget.Source_8wekyb3d8bbwe/platform-tools/adb.exe"

# 手机上的作业照片目录（默认相机文件夹）
PHONE_PHOTO_DIR = "/sdcard/DCIM/Camera"

# 本地工作目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PHOTOS_DIR = os.path.join(BASE_DIR, "photos")       # 从手机拉取的原始照片
OUTPUT_DIR = os.path.join(BASE_DIR, "output")       # 生成的PDF报告

# Claude API Key（从环境变量读取，或直接填写）
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# Qwen API（OCR识别：qwen-vl-max-latest）
QWEN_API_KEY = os.environ.get("QWEN_API_KEY", "sk-9b0a954533e643d8a045c3b34a3f46dc")
QWEN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
QWEN_VL_MODEL = "qwen-vl-max-latest"    # 视觉模型，用于OCR/识别预览

# Qwen API（批改：qwen-max，快速准确）
QWEN_GRADE_API_KEY = os.environ.get("QWEN_GRADE_API_KEY", "sk-c48ae0574dfd45ba83dd03b71a6b4b0a")
QWEN_GRADE_MODEL = "qwen-max"           # 用于作业批改

# 作业题目目录（老师预先录入题目，批改时直接使用）
HOMEWORK_DIR = os.path.join(BASE_DIR, "homework")
os.makedirs(HOMEWORK_DIR, exist_ok=True)

# 批改配置
SUBJECT = "高中数学"
MAX_SCORE = 150          # 试卷总分（可改）
PASS_SCORE = 90          # 及格分

# 创建必要目录
os.makedirs(PHOTOS_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
