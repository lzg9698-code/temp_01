"""超简单启动 - 无配置，无初始化"""

import sys
from PyQt6.QtWidgets import QApplication

from core import SimpleEngine
from ui import MainWindow

def main():
    """主入口"""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # 创建引擎和窗口
    engine = SimpleEngine()
    window = MainWindow(engine)
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
