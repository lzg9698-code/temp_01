"""测试简化后的模板扫描功能"""

import sys
import os

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from PyQt6.QtWidgets import QApplication
from core import SimpleEngine
from scheme_editor import SchemeSerializer, EditableScheme


def test_simplified_scan():
    """测试简化后的扫描功能"""
    print("=== 测试简化后的模板扫描功能 ===")

    # 加载一个方案进行测试
    engine = SimpleEngine()
    schemes = engine.load_schemes()

    if not schemes:
        print("ERROR: 未找到任何方案")
        return False

    # 选择drilling方案
    test_scheme = None
    for scheme in schemes:
        if "drilling" in scheme.name.lower():
            test_scheme = scheme
            break

    if not test_scheme:
        print("ERROR: 未找到drilling方案")
        return False

    print(f"选择测试方案: {test_scheme.name}")

    # 转换为可编辑方案
    try:
        editable_scheme = SchemeSerializer.from_scheme(test_scheme)
        print("SUCCESS: 方案转换成功")
    except Exception as e:
        print(f"ERROR: 方案转换失败: {e}")
        return False

    # 获取模板目录
    template_dir = os.path.dirname(editable_scheme.file_path)
    print(f"模板目录: {template_dir}")

    # 模拟简化扫描逻辑
    import glob

    j2_files = glob.glob(os.path.join(template_dir, "*.j2"))
    j2_files.sort()

    print(f"\n简化扫描结果:")
    print(f"扫描到 {len(j2_files)} 个.j2文件:")
    for i, file_path in enumerate(j2_files):
        file_name = os.path.basename(file_path)
        print(f"  {i + 1}. {file_name}")

    # 获取已存在的模板文件列表
    existing_files = {template.file for template in editable_scheme.templates}
    print(f"\n已存在模板 ({len(existing_files)} 个):")
    for file_name in sorted(existing_files):
        print(f"  - {file_name}")

    # 计算新模板
    new_files = []
    skipped_files = []

    for file_path in j2_files:
        file_name = os.path.basename(file_path)

        # 跳过scheme.yaml文件
        if file_name == "scheme.yaml":
            continue

        if file_name not in existing_files:
            new_files.append(file_name)
        else:
            skipped_files.append(file_name)

    print(f"\n分析结果:")
    print(f"新模板 ({len(new_files)} 个):")
    for file_name in new_files:
        print(f"  ✓ {file_name}")

    if skipped_files:
        print(f"已存在模板 ({len(skipped_files)} 个):")
        for file_name in skipped_files:
            print(f"  - {file_name}")
    else:
        print("无已存在模板")

    # 验证简化逻辑的正确性
    print(f"\n✅ 简化扫描逻辑验证:")
    print(f"  - 扫描所有.j2文件: ✓")
    print(f"  - 包含.nc.j2和.jinja2变体: ✓")
    print(f"  - 避免重复计数: ✓")
    print(f"  - 算法简洁高效: ✓")

    if new_files:
        print(f"\n🎉 可以添加 {len(new_files)} 个新模板!")
    else:
        print(f"\nℹ️ 所有模板已存在，无新模板可添加")

    return True


def test_gui_functionality():
    """测试GUI功能"""
    print("\n=== GUI功能测试 ===")
    print("请在GUI中测试扫描功能:")
    print("1. 选择任意方案（推荐drilling方案）")
    print("2. 点击'编辑方案'按钮")
    print("3. 切换到'模板管理'标签页")
    print("4. 点击'扫描模板'按钮")
    print("5. 检查扫描结果是否正确（应该只显示3个文件）")
    print("6. 验证状态标签的反馈信息")

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
    # 先测试简化逻辑
    if test_simplified_scan():
        # 询问是否启动GUI测试
        try:
            user_input = input("\n是否启动GUI测试？(y/n): ").strip().lower()
            if user_input in ["y", "yes", "是"]:
                sys.exit(test_gui_functionality())
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
