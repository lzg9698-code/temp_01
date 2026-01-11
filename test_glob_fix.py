"""测试和修复模板扫描问题"""

import glob
import os


def test_glob_patterns():
    """测试不同的glob模式"""
    template_dir = "templates/drilling"

    print("=== 测试glob模式 ===")

    # 方法1：分别扫描，然后过滤
    j2_files = glob.glob(os.path.join(template_dir, "*.j2"))
    print(f"*.j2: {j2_files}")

    # 过滤掉.nc.j2和.jinja2
    filtered_files = [
        f for f in j2_files if not f.endswith(".nc.j2") and not f.endswith(".jinja2")
    ]
    print(f"过滤后: {filtered_files}")

    # 方法2：使用fnmatch
    import fnmatch

    all_files = os.listdir(template_dir)
    matched_files = []
    for file in all_files:
        if (
            fnmatch.fnmatch(file, "*.j2")
            and not file.endswith(".nc.j2")
            and not file.endswith(".jinja2")
        ):
            matched_files.append(os.path.join(template_dir, file))

    print(f"fnmatch结果: {matched_files}")

    # 方法3：精确匹配
    exact_files = []
    for ext in [".j2"]:
        exact_files.extend(glob.glob(os.path.join(template_dir, f"*{ext}")))

    print(f"精确匹配: {exact_files}")

    # 推荐：使用精确匹配
    return exact_files


def fix_scan_algorithm():
    """修复扫描算法的建议"""
    print("\n=== 修复建议 ===")
    print("使用以下代码替换现有的扫描逻辑：")
    print("""
# 替换现有的扫描逻辑
def scan_template_files(template_dir):
    template_files = []
    
    # 精确匹配不同类型的模板文件
    for ext in ['.j2', '.nc.j2', '.jinja2']:
        pattern = os.path.join(template_dir, f'*{ext}')
        files = glob.glob(pattern)
        template_files.extend(files)
    
    # 移除重复项
    template_files = list(set(template_files))
    template_files.sort()
    
    return template_files
""")


if __name__ == "__main__":
    test_glob_patterns()
    fix_scan_algorithm()
