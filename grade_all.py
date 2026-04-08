"""批改全部13个学生的向量数量积作业（第5-10题）"""
import sys, shutil
sys.path.insert(0, '/home/guanghui/documents/correction_system')
from grade import grade_one
from report import generate_report

P = '/home/guanghui/documents/correction_system/photos_small'

students = [
    ("陈钧",   [f"{P}/IMG_20260408_154703.jpg", f"{P}/IMG_20260408_154709.jpg"]),
    ("学生2",  [f"{P}/IMG_20260408_154730.jpg"]),
    ("学生3",  [f"{P}/IMG_20260408_154832.jpg", f"{P}/IMG_20260408_154837.jpg"]),
    ("学生4",  [f"{P}/IMG_20260408_154856.jpg", f"{P}/IMG_20260408_154901.jpg", f"{P}/IMG_20260408_154910.jpg"]),
    ("学生5",  [f"{P}/IMG_20260408_154925.jpg", f"{P}/IMG_20260408_154929.jpg"]),
    ("学生6",  [f"{P}/IMG_20260408_154948.jpg", f"{P}/IMG_20260408_154954.jpg"]),
    ("学生7",  [f"{P}/IMG_20260408_155008.jpg", f"{P}/IMG_20260408_155017.jpg"]),
    ("学生8",  [f"{P}/IMG_20260408_155027.jpg", f"{P}/IMG_20260408_155032.jpg"]),
    ("学生9",  [f"{P}/IMG_20260408_155058.jpg", f"{P}/IMG_20260408_155105.jpg"]),
    ("学生10", [f"{P}/IMG_20260408_155144.jpg", f"{P}/IMG_20260408_155154.jpg", f"{P}/IMG_20260408_155159.jpg"]),
    ("学生11", [f"{P}/IMG_20260408_155221.jpg", f"{P}/IMG_20260408_155228.jpg"]),
    ("学生12", [f"{P}/IMG_20260408_155248.jpg", f"{P}/IMG_20260408_155251.jpg", f"{P}/IMG_20260408_155257.jpg", f"{P}/IMG_20260408_155301.jpg"]),
    ("学生13", [f"{P}/IMG_20260408_155308.jpg", f"{P}/IMG_20260408_155315.jpg"]),
]

results = []
for name, photos in students:
    print(f"\n[{students.index((name,photos))+1}/13] {name} ({len(photos)}页)")
    r = grade_one(photos, student_name=name)
    results.append(r)

pdf = generate_report(results, title="向量数量积作业批改报告（第5-10题）")
shutil.copy(pdf, "/mnt/c/Users/17683/Desktop/批改报告_向量作业.pdf")
print("\n已复制到桌面：批改报告_向量作业.pdf")
