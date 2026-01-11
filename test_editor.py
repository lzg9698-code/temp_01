"""测试方案编辑器模块

验证编辑器模块的基本功能。
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication


def test_editor():
    """测试编辑器功能"""
    app = QApplication(sys.argv)

    try:
        # 测试编辑器模块导入
        from scheme_editor import SchemeEditorDialog, EditableScheme

        print("SUCCESS: 编辑器模块导入成功")

        # 创建主窗口
        from core import SimpleEngine
        from ui import MainWindow

        engine = SimpleEngine()
        window = MainWindow(engine)
        window.show()

        print("SUCCESS: 应用程序启动成功！")
        print("TEST: 要测试编辑器功能：")
        print("   1. 选择任意方案")
        print("   2. 点击'编辑方案'按钮")
        print("   3. 在弹窗中编辑方案")

        # 运行应用
        return app.exec()

    except ImportError as e:
        print(f"ERROR: 模块导入失败: {e}")
        return 1
    except Exception as e:
        print(f"ERROR: 启动失败: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(test_editor())
