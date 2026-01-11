"""工具函数

提供编辑器相关的通用工具函数。
"""

from typing import List, Dict, Any, Optional
import os


class FileUtils:
    """文件操作工具类"""

    @staticmethod
    def ensure_directory(file_path: str) -> None:
        """确保文件目录存在"""
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

    @staticmethod
    def backup_file(file_path: str, backup_suffix: str = ".backup") -> bool:
        """备份文件"""
        try:
            if os.path.exists(file_path):
                backup_path = file_path + backup_suffix
                with open(file_path, "r", encoding="utf-8") as src:
                    with open(backup_path, "w", encoding="utf-8") as dst:
                        dst.write(src.read())
                return True
        except Exception:
            pass
        return False


class FormatUtils:
    """格式化工具类"""

    @staticmethod
    def format_yaml(yaml_content: str) -> str:
        """格式化YAML内容"""
        try:
            import yaml

            data = yaml.safe_load(yaml_content)
            return yaml.dump(
                data,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
                indent=2,
            )
        except Exception:
            return yaml_content

    @staticmethod
    def truncate_text(text: str, max_length: int = 50) -> str:
        """截断文本"""
        if len(text) <= max_length:
            return text
        return text[: max_length - 3] + "..."

    @staticmethod
    def format_error(error: str) -> str:
        """格式化错误信息"""
        # 移除过长的技术细节
        if len(error) > 200:
            return error[:197] + "..."
        return error


class UIUtils:
    """UI工具类"""

    @staticmethod
    def show_info_message(parent, title: str, message: str) -> None:
        """显示信息消息"""
        from PyQt6.QtWidgets import QMessageBox

        QMessageBox.information(parent, title, message)

    @staticmethod
    def show_warning_message(parent, title: str, message: str) -> None:
        """显示警告消息"""
        from PyQt6.QtWidgets import QMessageBox

        QMessageBox.warning(parent, title, message)

    @staticmethod
    def show_error_message(parent, title: str, message: str) -> None:
        """显示错误消息"""
        from PyQt6.QtWidgets import QMessageBox

        QMessageBox.critical(parent, title, message)

    @staticmethod
    def ask_confirmation(parent, title: str, message: str) -> bool:
        """请求确认"""
        from PyQt6.QtWidgets import QMessageBox

        reply = QMessageBox.question(
            parent,
            title,
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        return reply == QMessageBox.StandardButton.Yes

    @staticmethod
    def get_file_path(
        parent, title: str, file_filter: str, save: bool = False
    ) -> Optional[str]:
        """获取文件路径"""
        from PyQt6.QtWidgets import QFileDialog

        if save:
            file_path, _ = QFileDialog.getSaveFileName(parent, title, "", file_filter)
        else:
            file_path, _ = QFileDialog.getOpenFileName(parent, title, "", file_filter)

        return file_path if file_path else None


class StyleUtils:
    """样式工具类"""

    @staticmethod
    def get_error_style() -> str:
        """获取错误样式"""
        return "color: red; font-weight: bold;"

    @staticmethod
    def get_success_style() -> str:
        """获取成功样式"""
        return "color: green; font-weight: bold;"

    @staticmethod
    def get_warning_style() -> str:
        """获取警告样式"""
        return "color: orange; font-weight: bold;"

    @staticmethod
    def get_table_style() -> str:
        """获取表格样式"""
        return """
        QTableWidget {
            gridline-color: #cccccc;
            background-color: white;
            alternate-background-color: #f9f9f9;
        }
        QTableWidget::item {
            padding: 5px;
        }
        QHeaderView::section {
            background-color: #e6e6e6;
            padding: 5px;
            font-weight: bold;
            border: 1px solid #cccccc;
        }
        """


class Constants:
    """常量类"""

    # 文件过滤器
    YAML_FILTER = "YAML Files (*.yaml);;All Files (*)"
    TEMPLATE_FILTER = "Template Files (*.nc.j2 *.j2 *.jinja2);;All Files (*)"

    # 窗口尺寸
    DIALOG_WIDTH = 800
    DIALOG_HEIGHT = 600

    # 验证消息
    VALIDATION_SUCCESS = "验证通过"
    VALIDATION_FAILED = "验证失败"

    # 默认值
    DEFAULT_TEMPLATE_NAME = "新模板"
    DEFAULT_TEMPLATE_FILE = "new_template.nc.j2"
    DEFAULT_PARAMETER_NAME = "新参数"
    DEFAULT_GROUP_NAME = "新参数组"
