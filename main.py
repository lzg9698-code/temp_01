"""启动入口"""

import sys
from pathlib import Path

# 将 src 目录添加到模块搜索路径
src_path = str(Path(__file__).parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from PyQt6.QtWidgets import QApplication
from core import SimpleEngine
from ui import MainWindow, get_app_icon

def main():
    """主入口"""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setWindowIcon(get_app_icon())
    
    # 创建引擎和窗口
    engine = SimpleEngine()
    window = MainWindow(engine)
    window.show()
    
    return app.exec()

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        # 捕获 Ctrl+C，静默退出
        sys.exit(0)
