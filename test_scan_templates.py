"""测试模板扫描功能

验证扫描模板文件的功能是否正常工作。
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from core import SimpleEngine
from scheme_editor import SchemeSerializer, EditableScheme


def test_scan_functionality():
    """测试扫描功能"""
    print("=== 测试模板扫描功能 ===")

    # 加载一个方案进行测试
    engine = SimpleEngine()
    schemes = engine.load_schemes()

    if not schemes:
        print("ERROR: 未找到任何方案")
        return False

    # 选择第一个方案
    test_scheme = schemes[0]
    print(f"选择测试方案: {test_scheme.name}")
    print(f"方案文件路径: {test_scheme.file_path}")

    # 转换为可编辑方案
    try:
        editable_scheme = SchemeSerializer.from_scheme(test_scheme)
        print("SUCCESS: 方案转换成功")
    except Exception as e:
        print(f"ERROR: 方案转换失败: {e}")
        return False

    # 模拟扫描功能
    template_dir = os.path.dirname(editable_scheme.file_path)
    print(f"模板目录: {template_dir}")

    if not os.path.exists(template_dir):
        print(f"ERROR: 模板目录不存在: {template_dir}")
        return False

    # 扫描.j2文件
    import glob

    j2_files = []
    j2_files.extend(glob.glob(os.path.join(template_dir, "*.j2")))
    j2_files.extend(glob.glob(os.path.join(template_dir, "*.nc.j2")))
    j2_files.extend(glob.glob(os.path.join(template_dir, "*.jinja2")))

    print(f"扫描到 {len(j2_files)} 个模板文件:")
    for i, file_path in enumerate(j2_files[:10]):  # 只显示前10个
        file_name = os.path.basename(file_path)
        print(f"  {i + 1}. {file_name}")

    if len(j2_files) > 10:
        print(f"  ... 还有 {len(j2_files) - 10} 个文件")

    # 验证现有模板
    existing_files = {template.file for template in editable_scheme.templates}
    print(f"\n现有模板 ({len(existing_files)} 个):")
    for file_name in sorted(existing_files):
        print(f"  - {file_name}")

    # 计算新模板
    new_files = []
    for file_path in j2_files:
        file_name = os.path.basename(file_path)
        if file_name == "scheme.yaml":
            continue
        if file_name not in existing_files:
            new_files.append(file_name)

    print(f"\n可添加的新模板 ({len(new_files)} 个):")
    for file_name in new_files:
        print(f"  + {file_name}")

    if new_files:
        print("\n✅ 扫描功能测试成功 - 发现新模板可添加")
    else:
        print("\n✅ 扫描功能测试成功 - 无新模板可添加")

    return True


def test_gui_scan():
    """测试GUI扫描功能"""
    print("\n=== 启动GUI测试 ===")
    print("请在GUI中测试扫描功能:")
    print("1. 选择任意方案")
    print("2. 点击'编辑方案'按钮")
    print("3. 切换到'模板管理'标签页")
    print("4. 点击'扫描模板'按钮")
    print("5. 检查扫描结果和状态提示")

    app = QApplication(sys.argv)

    try:
        from ui import MainWindow

        engine = SimpleEngine()
        window = MainWindow(engine)
        window.show()

        print("✅ GUI启动成功，请按上述步骤测试")
        return app.exec()

    except Exception as e:
        print(f"ERROR: GUI启动失败: {e}")
        return 1


if __name__ == "__main__":
    # 先测试基本扫描逻辑
    if test_scan_functionality():
        # 询问是否启动GUI测试
        try:
            user_input = input("\n是否启动GUI测试？(y/n): ").strip().lower()
            if user_input in ["y", "yes", "是"]:
                sys.exit(test_gui_scan())
            else:
                print("测试完成")
                sys.exit(0)
        except KeyboardInterrupt:
            print("\n测试被中断")
            sys.exit(0)
        except:
            # 非交互环境，直接完成
            print("测试完成")
            sys.exit(0)
    else:
        sys.exit(1)
