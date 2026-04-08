"""
从手机拉取作业照片到本地 photos/ 目录
"""
import subprocess
import os
import sys
from datetime import datetime
from config import ADB, PHONE_PHOTO_DIR, PHOTOS_DIR


def adb(*args):
    result = subprocess.run([ADB] + list(args), capture_output=True, text=True)
    return result.stdout.strip(), result.returncode


def list_phone_photos(phone_dir=PHONE_PHOTO_DIR):
    """列出手机目录下所有图片文件"""
    out, code = adb("shell", f"ls '{phone_dir}'")
    if code != 0:
        print(f"[错误] 无法访问 {phone_dir}")
        return []
    files = [f.strip() for f in out.splitlines() if f.strip().lower().endswith((".jpg", ".jpeg", ".png"))]
    return files


def pull_photos(phone_dir=PHONE_PHOTO_DIR, local_dir=PHOTOS_DIR, only_new=True):
    """
    从手机拉取照片到本地。
    only_new=True 时只拉取本地没有的文件。
    返回成功拉取的文件列表。
    """
    files = list_phone_photos(phone_dir)
    if not files:
        print("[提示] 手机目录下没有找到图片")
        return []

    print(f"[手机] 找到 {len(files)} 张图片")
    pulled = []

    for fname in files:
        local_path = os.path.join(local_dir, fname)
        if only_new and os.path.exists(local_path):
            continue
        remote_path = f"{phone_dir}/{fname}"
        print(f"  正在拉取: {fname} ...", end=" ", flush=True)
        _, code = adb("pull", remote_path, local_path)
        if code == 0:
            print("OK")
            pulled.append(local_path)
        else:
            print("失败")

    print(f"[完成] 新拉取 {len(pulled)} 张，本地共 {len(os.listdir(local_dir))} 张")
    return pulled


def get_local_photos():
    """返回本地photos目录中所有图片，按文件名排序"""
    files = sorted([
        os.path.join(PHOTOS_DIR, f)
        for f in os.listdir(PHOTOS_DIR)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ])
    return files


if __name__ == "__main__":
    print("=== 从手机拉取作业照片 ===")
    pulled = pull_photos()
    local = get_local_photos()
    print(f"\n本地可用照片共 {len(local)} 张：")
    for p in local:
        print(f"  {os.path.basename(p)}")
