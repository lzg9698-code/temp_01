"""参数管理器UI组件

提供全局参数库的可视化管理界面。
"""

import os
import sys
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QAction
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QListWidget,
    QListWidgetItem,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QPushButton,
    QGroupBox,
    QFormLayout,
    QLineEdit,
    QTextEdit,
    QComboBox,
    QCheckBox,
    QDoubleSpinBox,
    QSpinBox,
    QMessageBox,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QTabWidget,
    QFileDialog,
    QMenuBar,
    QStatusBar,
)
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from parameter_manager import get_parameter_manager
from models import (
    GlobalParameter,
    GlobalParameterGroup,
    ParameterType,
)


# 类型映射
TYPE_DISPLAY = {
    ParameterType.STRING: "字符串",
    ParameterType.NUMBER: "数值",
    ParameterType.INTEGER: "整数",
    ParameterType.BOOLEAN: "布尔值",
    ParameterType.SELECT: "下拉列表",
}


class NoScrollDoubleSpinBox(QDoubleSpinBox):
    """禁用滚轮和上下箭头的 DoubleSpinBox"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)

    def wheelEvent(self, event):
        event.ignore()


class ParameterEditDialog(QDialog):
    """参数编辑对话框"""

    def __init__(
        self,
        param: Optional[GlobalParameter] = None,
        group_names: List[str] = None,
        current_group: str = None,
        parent=None,
    ):
        super().__init__(parent)
        self.param = param
        self.group_names = group_names or []
        self.current_group = current_group
        self.setup_ui()
        self.load_parameter_data()

    def setup_ui(self):
        self.setWindowTitle("编辑参数" if self.param else "新建参数")
        self.setModal(True)
        self.resize(400, 300)

        layout = QFormLayout(self)

        # 参数名
        self.name_edit = QLineEdit()
        layout.addRow("参数名:", self.name_edit)

        # 参数组
        self.group_combo = QComboBox()
        self.group_combo.addItems(self.group_names)
        if self.current_group and self.current_group in self.group_names:
            self.group_combo.setCurrentText(self.current_group)
        layout.addRow("参数组:", self.group_combo)

        # 参数类型
        self.type_combo = QComboBox()
        for p_type, display in TYPE_DISPLAY.items():
            self.type_combo.addItem(display, p_type)
        self.type_combo.currentIndexChanged.connect(self.on_type_changed)
        layout.addRow("参数类型:", self.type_combo)

        # 默认值
        self.default_edit = QLineEdit()
        layout.addRow("默认值:", self.default_edit)

        # 最小值
        self.min_spin = NoScrollDoubleSpinBox()
        self.min_spin.setMinimum(-999999.0)
        self.min_spin.setMaximum(999999.0)
        self.min_spin.setDecimals(3)
        layout.addRow("最小值:", self.min_spin)

        # 最大值
        self.max_spin = NoScrollDoubleSpinBox()
        self.max_spin.setMinimum(-999999.0)
        self.max_spin.setMaximum(999999.0)
        self.max_spin.setDecimals(3)
        layout.addRow("最大值:", self.max_spin)

        # 单位
        self.unit_edit = QLineEdit()
        layout.addRow("单位:", self.unit_edit)

        # 描述
        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(80)
        layout.addRow("描述:", self.desc_edit)

        # 必填
        self.required_check = QCheckBox()
        layout.addRow("必填:", self.required_check)

        # 选项编辑器（select类型专用）
        self.options_group = QGroupBox("选项列表")
        options_layout = QVBoxLayout(self.options_group)
        
        # 选项列表
        self.options_list = QListWidget()
        self.options_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.options_list.currentItemChanged.connect(self.on_option_selected)
        options_layout.addWidget(self.options_list)
        
        # 选项编辑区
        edit_layout = QHBoxLayout()
        self.opt_label_edit = QLineEdit()
        self.opt_label_edit.setPlaceholderText("显示名称 (Label)")
        edit_layout.addWidget(self.opt_label_edit)
        
        self.opt_value_edit = QLineEdit()
        self.opt_value_edit.setPlaceholderText("实际值 (Value)")
        edit_layout.addWidget(self.opt_value_edit)

        self.opt_type_combo = QComboBox()
        self.opt_type_combo.addItems(["String", "Number", "Integer", "Boolean"])
        self.opt_type_combo.setFixedWidth(80)
        edit_layout.addWidget(self.opt_type_combo)
        
        options_layout.addLayout(edit_layout)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        self.add_opt_btn = QPushButton("添加")
        self.add_opt_btn.clicked.connect(self.add_option)
        btn_layout.addWidget(self.add_opt_btn)
        
        self.update_opt_btn = QPushButton("更新")
        self.update_opt_btn.clicked.connect(self.update_option)
        self.update_opt_btn.setEnabled(False)
        btn_layout.addWidget(self.update_opt_btn)
        
        self.remove_opt_btn = QPushButton("删除")
        self.remove_opt_btn.clicked.connect(self.remove_option)
        self.remove_opt_btn.setEnabled(False)
        btn_layout.addWidget(self.remove_opt_btn)

        self.set_default_btn = QPushButton("设为默认")
        self.set_default_btn.clicked.connect(self.set_current_as_default)
        self.set_default_btn.setEnabled(False)
        btn_layout.addWidget(self.set_default_btn)
        
        options_layout.addLayout(btn_layout)
        
        layout.addRow(self.options_group)

        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)

    def load_parameter_data(self):
        """加载参数数据"""
        if not self.param:
            return

        self.name_edit.setText(self.param.name)
        
        # 设置类型
        display_text = TYPE_DISPLAY.get(self.param.type, "字符串")
        self.type_combo.setCurrentText(display_text)

        if self.param.default is not None:
            self.default_edit.setText(str(self.param.default))

        if self.param.min_value is not None:
            self.min_spin.setValue(self.param.min_value)

        if self.param.max_value is not None:
            self.max_spin.setValue(self.param.max_value)

        self.unit_edit.setText(self.param.unit)
        self.desc_edit.setText(self.param.description)
        self.required_check.setChecked(self.param.required)

        # Clear existing items first to avoid duplication if called multiple times
        self.options_list.clear()
        if self.param.options:
            for opt in self.param.options:
                if isinstance(opt, dict) and "label" in opt and "value" in opt:
                    val = opt['value']
                    type_str = "String"
                    if isinstance(val, int): type_str = "Integer"
                    elif isinstance(val, float): type_str = "Number"
                    elif isinstance(val, bool): type_str = "Boolean"
                    
                    item = QListWidgetItem(f"{opt['label']} ({val}) [{type_str}]")
                    item.setData(Qt.ItemDataRole.UserRole, opt)
                else:
                    item = QListWidgetItem(f"{str(opt)} (String)")
                    item.setData(Qt.ItemDataRole.UserRole, {"label": str(opt), "value": str(opt)})
                self.options_list.addItem(item)

        self.on_type_changed()

    def on_option_selected(self, current: QListWidgetItem, previous: QListWidgetItem):
        """选项选择处理"""
        if current:
            data = current.data(Qt.ItemDataRole.UserRole)
            self.opt_label_edit.setText(str(data["label"]))
            
            val = data["value"]
            self.opt_value_edit.setText(str(val))
            
            # Set type combo based on value type
            if isinstance(val, bool):
                self.opt_type_combo.setCurrentText("Boolean")
            elif isinstance(val, int):
                self.opt_type_combo.setCurrentText("Integer")
            elif isinstance(val, float):
                self.opt_type_combo.setCurrentText("Number")
            else:
                self.opt_type_combo.setCurrentText("String")
                
            self.update_opt_btn.setEnabled(True)
            self.remove_opt_btn.setEnabled(True)
            self.set_default_btn.setEnabled(True)
        else:
            self.opt_label_edit.clear()
            self.opt_value_edit.clear()
            self.update_opt_btn.setEnabled(False)
            self.remove_opt_btn.setEnabled(False)
            self.set_default_btn.setEnabled(False)

    def set_current_as_default(self):
        """将当前选中项设为默认值"""
        current_item = self.options_list.currentItem()
        if current_item:
            data = current_item.data(Qt.ItemDataRole.UserRole)
            self.default_edit.setText(str(data["value"]))

    def _parse_value(self, text: str, type_str: str) -> Any:
        try:
            if type_str == "Integer":
                return int(text)
            elif type_str == "Number":
                return float(text)
            elif type_str == "Boolean":
                return text.lower() in ("true", "1", "yes", "on")
            else:
                return text
        except:
            return text

    def add_option(self):
        """添加选项"""
        label = self.opt_label_edit.text().strip()
        value_text = self.opt_value_edit.text().strip()
        type_str = self.opt_type_combo.currentText()
        
        if not label:
            QMessageBox.warning(self, "警告", "显示名称不能为空")
            return
            
        if not value_text:
            value_text = label  # 如果没有值，默认与标签相同
            
        value = self._parse_value(value_text, type_str)
            
        opt_data = {"label": label, "value": value}
        item = QListWidgetItem(f"{label} ({value}) [{type_str}]")
        item.setData(Qt.ItemDataRole.UserRole, opt_data)
        self.options_list.addItem(item)
        
        # 清空输入
        self.opt_label_edit.clear()
        self.opt_value_edit.clear()

    def update_option(self):
        """更新选项"""
        current_item = self.options_list.currentItem()
        if not current_item:
            return
            
        label = self.opt_label_edit.text().strip()
        value_text = self.opt_value_edit.text().strip()
        type_str = self.opt_type_combo.currentText()
        
        if not label:
            QMessageBox.warning(self, "警告", "显示名称不能为空")
            return
            
        if not value_text:
            value_text = label

        value = self._parse_value(value_text, type_str)

        opt_data = {"label": label, "value": value}
        current_item.setText(f"{label} ({value}) [{type_str}]")
        current_item.setData(Qt.ItemDataRole.UserRole, opt_data)

    def remove_option(self):
        """删除选项"""
        current_row = self.options_list.currentRow()
        if current_row >= 0:
            self.options_list.takeItem(current_row)

    def on_type_changed(self):
        """类型变更处理"""
        param_type = self.type_combo.currentData()
        if not isinstance(param_type, ParameterType):
            return

        # 根据类型显示/隐藏相关字段
        show_min_max = param_type in [ParameterType.NUMBER, ParameterType.INTEGER]
        show_unit = param_type in [ParameterType.NUMBER, ParameterType.INTEGER]
        show_options = param_type == ParameterType.SELECT
        show_default = True

        # 控制字段显示
        for i in range(self.layout().rowCount()):
            label = self.layout().itemAt(i, QFormLayout.ItemRole.LabelRole)
            widget = self.layout().itemAt(i, QFormLayout.ItemRole.FieldRole)

            if label and widget:
                label_text = label.widget().text()

                if "最小值" in label_text or "最大值" in label_text:
                    widget.widget().setVisible(show_min_max)
                    label.widget().setVisible(show_min_max)
                elif "单位" in label_text:
                    widget.widget().setVisible(show_unit)
                    label.widget().setVisible(show_unit)
                elif "选项" in label_text or "选项列表" in label_text: # Handle both old label and new group box title scenarios if needed, currently matching logic is a bit rigid in on_type_changed potentially.
                    # Wait, the iteration logic in on_type_changed iterates form rows.
                    # My new widget is a GroupBox added via addRow, but addRow(QWidget) puts it in FieldRole with empty Label?
                    # Or addRow(widget) creates a spanning widget.
                    # Let's check how I added it: layout.addRow(self.options_group)
                    # This means it might not have a LabelRole item.
                    pass

        # Dedicated logic for options group visibility since it's a spanning widget likely
        self.options_group.setVisible(show_options)

    def get_parameter(self) -> Tuple[Optional[GlobalParameter], str]:
        """获取编辑后的参数和组名"""
        try:
            name = self.name_edit.text().strip()
            group_name = self.group_combo.currentText()
            
            if not name:
                QMessageBox.warning(self, "错误", "参数名不能为空")
                return None, group_name

            param_type = self.type_combo.currentData()
            if not isinstance(param_type, ParameterType):
                param_type = ParameterType.STRING

            # 解析默认值
            default_value = None
            default_text = self.default_edit.text().strip()
            if default_text:
                if param_type == ParameterType.NUMBER:
                    default_value = float(default_text)
                elif param_type == ParameterType.INTEGER:
                    default_value = int(default_text)
                elif param_type == ParameterType.BOOLEAN:
                    default_value = default_text.lower() in ("true", "1", "yes", "on")
                else:
                    default_value = default_text

            # 解析选项
            options = []
            if param_type == ParameterType.SELECT:
                for i in range(self.options_list.count()):
                    item = self.options_list.item(i)
                    options.append(item.data(Qt.ItemDataRole.UserRole))

            # 创建参数对象
            param = GlobalParameter(
                name=name,
                type=param_type,
                default=default_value,
                min_value=self.min_spin.value()
                if self.min_spin.value() != -999999.0
                else None,
                max_value=self.max_spin.value()
                if self.max_spin.value() != 999999.0
                else None,
                unit=self.unit_edit.text().strip(),
                description=self.desc_edit.toPlainText().strip(),
                required=self.required_check.isChecked(),
                options=options,
            )

            return param, group_name

        except ValueError as e:
            QMessageBox.warning(self, "错误", f"参数值格式错误: {e}")
            return None, ""



class ParameterGroupEditDialog(QDialog):
    """参数组编辑对话框"""

    def __init__(
        self,
        group: Optional[GlobalParameterGroup] = None,
        existing_names: List[str] = None,
        parent=None,
    ):
        super().__init__(parent)
        self.group = group
        self.existing_names = existing_names or []
        # 如果是编辑模式，允许保留当前名称
        if self.group and self.group.name in self.existing_names:
            self.existing_names = [n for n in self.existing_names if n != self.group.name]
            
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("编辑参数组" if self.group else "新建参数组")
        self.setModal(True)
        self.resize(300, 200)

        layout = QFormLayout(self)

        # 组名
        self.name_edit = QLineEdit()
        if self.group:
            self.name_edit.setText(self.group.name)
        layout.addRow("组名:", self.name_edit)

        # 描述
        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(80)
        if self.group:
            self.desc_edit.setText(self.group.description)
        layout.addRow("描述:", self.desc_edit)

        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)

    def validate_and_accept(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "错误", "参数组名不能为空")
            return

        if name in self.existing_names:
            QMessageBox.warning(self, "错误", "参数组名已存在")
            return

        self.accept()

    def get_group_data(self) -> Tuple[str, str]:
        """获取编辑后的数据"""
        return self.name_edit.text().strip(), self.desc_edit.toPlainText().strip()


class ParameterManagerWindow(QMainWindow):
    """参数管理器主窗口"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.manager = get_parameter_manager()
        self.setup_ui()
        self.setup_menu()
        self.setup_status_bar()
        self.load_parameter_groups()

    def setup_ui(self):
        """设置用户界面"""
        self.setWindowTitle("全局参数管理器")
        self.resize(1000, 700)

        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QHBoxLayout(central_widget)

        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # 左侧：参数组管理
        left_widget = self.create_group_widget()
        splitter.addWidget(left_widget)

        # 右侧：参数编辑
        right_widget = self.create_parameter_widget()
        splitter.addWidget(right_widget)

        # 设置分割器比例
        splitter.setSizes([300, 700])

    def create_group_widget(self):
        """创建参数组管理部件"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 参数组列表
        layout.addWidget(QLabel("参数组:"))
        self.group_list = QListWidget()
        self.group_list.currentItemChanged.connect(self.on_group_selected)
        layout.addWidget(self.group_list)

        # 参数组操作按钮
        group_btn_layout = QHBoxLayout()

        self.add_group_btn = QPushButton("新建组")
        self.add_group_btn.clicked.connect(self.add_parameter_group)
        group_btn_layout.addWidget(self.add_group_btn)

        self.edit_group_btn = QPushButton("编辑组")
        self.edit_group_btn.clicked.connect(self.edit_parameter_group)
        group_btn_layout.addWidget(self.edit_group_btn)

        self.remove_group_btn = QPushButton("删除组")
        self.remove_group_btn.clicked.connect(self.remove_parameter_group)
        group_btn_layout.addWidget(self.remove_group_btn)

        layout.addLayout(group_btn_layout)

        # 参数组信息
        info_group = QGroupBox("组信息")
        info_layout = QFormLayout(info_group)

        self.group_name_label = QLabel("-")
        info_layout.addRow("组名:", self.group_name_label)

        self.group_desc_label = QLabel("-")
        info_layout.addRow("描述:", self.group_desc_label)

        self.group_param_count_label = QLabel("-")
        info_layout.addRow("参数数量:", self.group_param_count_label)

        layout.addWidget(info_group)

        return widget

    def create_parameter_widget(self):
        """创建参数编辑部件"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 参数表格
        layout.addWidget(QLabel("参数列表:"))
        self.param_table = QTableWidget()
        self.param_table.setColumnCount(7)
        self.param_table.setHorizontalHeaderLabels(
            ["参数名", "类型", "默认值", "最小值", "最大值", "单位", "描述"]
        )
        self.param_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.param_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.param_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

        header = self.param_table.horizontalHeader()
        if header:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.param_table.itemDoubleClicked.connect(self.edit_parameter)
        self.param_table.itemSelectionChanged.connect(self.on_parameter_selected)
        layout.addWidget(self.param_table)

        # 参数操作按钮
        param_btn_layout = QHBoxLayout()

        self.add_param_btn = QPushButton("新建参数")
        self.add_param_btn.clicked.connect(self.add_parameter)
        param_btn_layout.addWidget(self.add_param_btn)

        self.edit_param_btn = QPushButton("编辑参数")
        self.edit_param_btn.clicked.connect(self.edit_parameter)
        param_btn_layout.addWidget(self.edit_param_btn)

        self.remove_param_btn = QPushButton("删除参数")
        self.remove_param_btn.clicked.connect(self.remove_parameter)
        param_btn_layout.addWidget(self.remove_param_btn)

        param_btn_layout.addStretch()
        layout.addLayout(param_btn_layout)

        return widget

    def setup_menu(self):
        """设置菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件")

        import_action = QAction("导入方案参数", self)
        import_action.triggered.connect(self.import_from_scheme)
        file_menu.addAction(import_action)

        file_menu.addSeparator()

        save_action = QAction("保存", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_library)
        file_menu.addAction(save_action)

        reload_action = QAction("重新加载", self)
        reload_action.setShortcut("F5")
        reload_action.triggered.connect(self.reload_library)
        file_menu.addAction(reload_action)

        file_menu.addSeparator()

        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 工具菜单
        tools_menu = menubar.addMenu("工具")

        validate_action = QAction("验证参数库", self)
        validate_action.triggered.connect(self.validate_library)
        tools_menu.addAction(validate_action)

        info_action = QAction("库信息", self)
        info_action.triggered.connect(self.show_library_info)
        tools_menu.addAction(info_action)

    def setup_status_bar(self):
        """设置状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")

    def load_parameter_groups(self):
        """加载参数组列表"""
        self.group_list.clear()

        group_names = self.manager.get_group_names()
        for group_name in group_names:
            item = QListWidgetItem(group_name)
            self.group_list.addItem(item)

        if group_names:
            self.group_list.setCurrentRow(0)
            self.update_group_display()

    def on_group_selected(self, current: QListWidgetItem, previous: QListWidgetItem):
        """参数组选择处理"""
        if current:
            group_name = current.text()
            self.load_parameters(group_name)
            self.update_group_display()
        else:
            self.param_table.setRowCount(0)
            self.clear_group_display()

    def load_parameters(self, group_name: str):
        """加载参数表格"""
        group = self.manager.get_group(group_name)
        if not group:
            return

        self.param_table.setRowCount(len(group.parameters))

        for row, (param_name, param) in enumerate(group.parameters.items()):
            # 参数名
            name_item = QTableWidgetItem(param_name)
            name_item.setData(Qt.ItemDataRole.UserRole, param)
            self.param_table.setItem(row, 0, name_item)

            # 类型
            display_type = TYPE_DISPLAY.get(param.type, param.type.value)
            type_item = QTableWidgetItem(display_type)
            self.param_table.setItem(row, 1, type_item)

            # 默认值
            default_item = QTableWidgetItem(
                str(param.default) if param.default is not None else ""
            )
            self.param_table.setItem(row, 2, default_item)

            # 最小值
            min_item = QTableWidgetItem(
                str(param.min_value) if param.min_value is not None else ""
            )
            self.param_table.setItem(row, 3, min_item)

            # 最大值
            max_item = QTableWidgetItem(
                str(param.max_value) if param.max_value is not None else ""
            )
            self.param_table.setItem(row, 4, max_item)

            # 单位
            unit_item = QTableWidgetItem(param.unit)
            self.param_table.setItem(row, 5, unit_item)

            # 描述
            desc_item = QTableWidgetItem(param.description)
            self.param_table.setItem(row, 6, desc_item)

    def update_group_display(self):
        """更新参数组信息显示"""
        current_item = self.group_list.currentItem()
        if not current_item:
            self.clear_group_display()
            return

        group_name = current_item.text()
        group = self.manager.get_group(group_name)

        if group:
            self.group_name_label.setText(group.name)
            self.group_desc_label.setText(group.description)
            self.group_param_count_label.setText(str(len(group.parameters)))
        else:
            self.clear_group_display()

    def clear_group_display(self):
        """清空参数组显示"""
        self.group_name_label.setText("-")
        self.group_desc_label.setText("-")
        self.group_param_count_label.setText("-")

    def on_parameter_selected(self):
        """参数选择处理"""
        has_selection = self.param_table.currentRow() >= 0
        self.edit_param_btn.setEnabled(has_selection)
        self.remove_param_btn.setEnabled(has_selection)

    def add_parameter_group(self):
        """添加参数组"""
        dialog = ParameterGroupEditDialog(existing_names=self.manager.get_group_names(), parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name, desc = dialog.get_group_data()
            try:
                new_group = GlobalParameterGroup(name=name, description=desc)
                self.manager.add_group(new_group)
                self.load_parameter_groups()
                
                # 选中新创建的组
                items = self.group_list.findItems(name, Qt.MatchFlag.MatchExactly)
                if items:
                    self.group_list.setCurrentItem(items[0])
                    
                self.status_bar.showMessage(f"已创建参数组: {name}")
            except ValueError as e:
                QMessageBox.warning(self, "错误", str(e))

    def edit_parameter_group(self):
        """编辑参数组"""
        current_item = self.group_list.currentItem()
        if not current_item:
            return

        group_name = current_item.text()
        group = self.manager.get_group(group_name)
        if not group:
            return

        dialog = ParameterGroupEditDialog(
            group=group, 
            existing_names=self.manager.get_group_names(), 
            parent=self
        )
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_name, new_desc = dialog.get_group_data()
            
            # 如果名称改变，需要特殊处理
            if new_name != group_name:
                # 1. 移除旧组
                # 注意：这里有一个潜在问题，如果manager没有重命名方法，我们需要手动处理
                # remove_group不会返回组对象，所以我们要小心
                # 更好的方式可能是先添加新组，再移动参数，再删除旧组
                
                # 暂时简单的实现：如果改名，视为新组，但保留参数
                # 然而 parameters 是dict引用，所以可以共享？
                # GlobalParameterGroup.parameters 是 Dict[str, GlobalParameter]
                
                # 创建新组，复制参数
                new_group = GlobalParameterGroup(
                    name=new_name, 
                    description=new_desc, 
                    parameters=group.parameters # 引用传递，保持参数
                )
                
                try:
                    self.manager.add_group(new_group)
                    self.manager.remove_group(group_name)
                    
                    self.load_parameter_groups()
                    # 选中新组
                    items = self.group_list.findItems(new_name, Qt.MatchFlag.MatchExactly)
                    if items:
                        self.group_list.setCurrentItem(items[0])
                        
                    self.status_bar.showMessage(f"已重命名参数组: {group_name} -> {new_name}")
                except ValueError as e:
                    QMessageBox.warning(self, "错误", f"重命名失败: {e}")
            else:
                # 仅更新描述
                group.description = new_desc
                self.update_group_display()
                self.status_bar.showMessage(f"已更新参数组: {group_name}")

    def remove_parameter_group(self):
        """删除参数组"""
        current_item = self.group_list.currentItem()
        if not current_item:
            return

        group_name = current_item.text()
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除参数组 '{group_name}' 吗？\\n这将删除该组中的所有参数。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.manager.remove_group(group_name):
                self.load_parameter_groups()
                self.status_bar.showMessage(f"已删除参数组: {group_name}")
            else:
                QMessageBox.warning(self, "错误", "删除参数组失败")

    def add_parameter(self):
        """添加参数"""
        current_item = self.group_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "错误", "请先选择一个参数组")
            return

        group_name = current_item.text()

        dialog = ParameterEditDialog(group_names=self.manager.get_group_names(), current_group=group_name, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            param, target_group = dialog.get_parameter()
            if param and self.manager.add_parameter_to_group(target_group, param):
                # If added to a different group than currently viewed, maybe just notify
                if target_group == group_name:
                    self.load_parameters(group_name)
                self.update_group_display()
                self.status_bar.showMessage(f"已添加参数: {param.name} 到组 {target_group}")

    def edit_parameter(self):
        """编辑参数"""
        current_row = self.param_table.currentRow()
        if current_row < 0:
            return

        name_item = self.param_table.item(current_row, 0)
        old_param = name_item.data(Qt.ItemDataRole.UserRole)
        old_name = old_param.name

        current_item = self.group_list.currentItem()
        group_name = current_item.text()

        dialog = ParameterEditDialog(old_param, group_names=self.manager.get_group_names(), current_group=group_name, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_param, new_group_name = dialog.get_parameter()
            if new_param:
                if new_group_name == group_name:
                    # Same group, just update
                    if self.manager.update_parameter_in_group(
                        group_name, old_name, new_param
                    ):
                        self.load_parameters(group_name)
                        self.status_bar.showMessage(f"已更新参数: {new_param.name}")
                    else:
                        QMessageBox.warning(self, "错误", "更新参数失败")
                else:
                    # Group changed, move parameter
                    if self.manager.move_parameter(group_name, new_group_name, old_name, new_param):
                             # Move success
                             self.load_parameter_groups() # Group counts changed maybe
                             self.load_parameters(group_name) # Refresh current view (param should disappear)
                             self.status_bar.showMessage(f"已移动参数 {new_param.name} 到组 {new_group_name}")
                    else:
                         QMessageBox.warning(self, "错误", f"移动参数失败: 未能移动到新组 '{new_group_name}'")

    def remove_parameter(self):
        """删除参数"""
        current_row = self.param_table.currentRow()
        if current_row < 0:
            return

        name_item = self.param_table.item(current_row, 0)
        param_name = name_item.text()
        current_item = self.group_list.currentItem()
        group_name = current_item.text()

        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除参数 '{param_name}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.manager.remove_parameter_from_group(group_name, param_name):
                self.load_parameters(group_name)
                self.update_group_display()
                self.status_bar.showMessage(f"已删除参数: {param_name}")

    def import_from_scheme(self):
        """从方案导入参数"""
        # TODO: 实现从方案导入参数
        QMessageBox.information(self, "提示", "导入方案参数功能待实现")

    def save_library(self):
        """保存参数库"""
        if self.manager.save_library():
            self.status_bar.showMessage("参数库已保存")
        else:
            QMessageBox.warning(self, "错误", "保存参数库失败")

    def reload_library(self):
        """重新加载参数库"""
        if self.manager.load_library():
            self.load_parameter_groups()
            self.status_bar.showMessage("参数库已重新加载")
        else:
            QMessageBox.warning(self, "错误", "重新加载参数库失败")

    def validate_library(self):
        """验证参数库"""
        is_valid, errors = self.manager.validate_library()

        if is_valid:
            QMessageBox.information(self, "验证结果", "参数库验证通过")
        else:
            error_text = "\\n".join(f"- {error}" for error in errors)
            QMessageBox.warning(self, "验证结果", f"参数库验证失败:\\n{error_text}")

    def show_library_info(self):
        """显示库信息"""
        info = self.manager.get_library_info()

        info_text = f"""
参数库信息:
- 文件路径: {info.get("file_path", "N/A")}
- 参数组数量: {info.get("total_groups", 0)}
- 参数总数: {info.get("total_parameters", 0)}
- 参数类型分布: {info.get("parameter_types", {})}
"""
        QMessageBox.information(self, "库信息", info_text.strip())


def show_parameter_manager(parent=None):
    """显示参数管理器

    Args:
        parent: 父窗口
    """
    window = ParameterManagerWindow(parent)
    window.show()
    return window


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # 初始化参数管理器
    from config import config

    manager = get_parameter_manager()
    manager.initialize(config.CONFIG_DIR)

    window = ParameterManagerWindow()
    window.show()

    sys.exit(app.exec())
