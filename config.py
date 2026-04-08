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

# 批改配置
SUBJECT = "高中数学"
MAX_SCORE = 150          # 试卷总分（可改）
PASS_SCORE = 90          # 及格分

# 创建必要目录
os.makedirs(PHOTOS_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
