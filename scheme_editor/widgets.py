"""方案编辑器UI组件

提供可视化编辑scheme.yaml的用户界面。
"""

import os
from typing import Optional, Dict, Any
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QWidget,
    QLabel,
    QLineEdit,
    QTextEdit,
    QComboBox,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QFormLayout,
    QGroupBox,
    QCheckBox,
    QDoubleSpinBox,
    QSpinBox,
    QMessageBox,
    QFileDialog,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QDialogButtonBox,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

from .models import (
    EditableScheme,
    TemplateDef,
    ParameterDef,
    ParameterGroup,
    ParameterType,
)
from .serializers import SchemeSerializer


class BasicInfoWidget(QWidget):
    """基本信息编辑页面"""

    def __init__(self, scheme: EditableScheme, parent=None):
        super().__init__(parent)
        self.scheme = scheme
        self.setup_ui()
        self.load_scheme_data()

    def setup_ui(self):
        layout = QFormLayout(self)

        # 方案名称
        self.name_edit = QLineEdit()
        self.name_edit.textChanged.connect(self.on_name_changed)
        layout.addRow("方案名称:", self.name_edit)

        # 方案描述
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(100)
        self.description_edit.textChanged.connect(self.on_description_changed)
        layout.addRow("方案描述:", self.description_edit)

        layout.addRow(QWidget())  # 添加空白空间

    def load_scheme_data(self):
        """加载方案数据"""
        self.name_edit.setText(self.scheme.name)
        self.description_edit.setText(self.scheme.description)

    def on_name_changed(self, text: str):
        """名称变更处理"""
        self.scheme.name = text

    def on_description_changed(self):
        """描述变更处理"""
        self.scheme.description = self.description_edit.toPlainText()


class TemplatesWidget(QWidget):
    """模板管理页面"""

    def __init__(self, scheme: EditableScheme, parent=None):
        super().__init__(parent)
        self.scheme = scheme
        self.setup_ui()
        self.load_templates()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # 模板列表
        self.template_list = QListWidget()
        self.template_list.currentItemChanged.connect(self.on_template_selected)
        layout.addWidget(QLabel("模板列表:"))
        layout.addWidget(self.template_list)

        # 模板详情
        details_group = QGroupBox("模板详情")
        details_layout = QFormLayout(details_group)

        self.name_edit = QLineEdit()
        self.name_edit.textChanged.connect(self.on_template_name_changed)
        details_layout.addRow("模板名称:", self.name_edit)

        self.file_edit = QLineEdit()
        self.file_edit.textChanged.connect(self.on_template_file_changed)
        details_layout.addRow("模板文件:", self.file_edit)

        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(60)
        self.description_edit.textChanged.connect(self.on_template_description_changed)
        details_layout.addRow("模板描述:", self.description_edit)

        layout.addWidget(details_group)

        # 操作按钮
        button_layout = QHBoxLayout()

        self.add_btn = QPushButton("扫描模板")
        self.add_btn.clicked.connect(self.scan_templates)
        button_layout.addWidget(self.add_btn)

        self.remove_btn = QPushButton("删除模板")
        self.remove_btn.clicked.connect(self.remove_template)
        button_layout.addWidget(self.remove_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.status_label)

    def load_templates(self):
        """加载模板列表"""
        self.template_list.clear()
        for template in self.scheme.templates:
            item = QListWidgetItem(f"{template.name} - {template.file}")
            item.setData(Qt.ItemDataRole.UserRole, template)
            self.template_list.addItem(item)

    def on_template_selected(self, current: QListWidgetItem, previous: QListWidgetItem):
        """模板选择处理"""
        if current:
            template = current.data(Qt.ItemDataRole.UserRole)
            if template:
                self.name_edit.setText(template.name)
                self.file_edit.setText(template.file)
                self.description_edit.setText(template.description)
                self.remove_btn.setEnabled(True)
            else:
                self.remove_btn.setEnabled(False)
        else:
            self.clear_template_form()
            self.remove_btn.setEnabled(False)

    def clear_template_form(self):
        """清空模板表单"""
        self.name_edit.clear()
        self.file_edit.clear()
        self.description_edit.clear()

    def on_template_name_changed(self, text: str):
        """模板名称变更处理"""
        current_item = self.template_list.currentItem()
        if current_item:
            template = current_item.data(Qt.ItemDataRole.UserRole)
            if template:
                template.name = text
                current_item.setText(f"{text} - {template.file}")

    def on_template_file_changed(self, text: str):
        """模板文件变更处理"""
        current_item = self.template_list.currentItem()
        if current_item:
            template = current_item.data(Qt.ItemDataRole.UserRole)
            if template:
                template.file = text
                current_item.setText(f"{template.name} - {text}")

    def on_template_description_changed(self):
        """模板描述变更处理"""
        current_item = self.template_list.currentItem()
        if current_item:
            template = current_item.data(Qt.ItemDataRole.UserRole)
            if template:
                template.description = self.description_edit.toPlainText()

    def scan_templates(self):
        """扫描模板文件"""
        self.status_label.setText("正在扫描模板文件...")
        self.status_label.setStyleSheet("color: blue; font-weight: bold;")

        # 获取模板包目录
        template_dir = None
        if self.scheme.file_path:
            template_dir = os.path.dirname(self.scheme.file_path)

        if not template_dir or not os.path.exists(template_dir):
            self.status_label.setText("无法确定模板目录位置")
            self.status_label.setStyleSheet("color: red;")
            QMessageBox.warning(self, "警告", "无法确定模板目录位置")
            return

        # 扫描.j2文件
        try:
            import glob

            j2_files = glob.glob(os.path.join(template_dir, "*.j2"))
            j2_files.extend(glob.glob(os.path.join(template_dir, "*.nc.j2")))
            j2_files.extend(glob.glob(os.path.join(template_dir, "*.jinja2")))

            if not j2_files:
                self.status_label.setText(f"目录 {template_dir} 中未找到模板文件")
                self.status_label.setStyleSheet("color: orange;")
                QMessageBox.information(
                    self, "扫描结果", f"在目录 {template_dir} 中未找到模板文件"
                )
                return

            # 获取已存在的模板文件列表
            existing_files = {template.file for template in self.scheme.templates}

            # 处理找到的文件
            new_templates = []
            skipped_files = []

            for file_path in j2_files:
                file_name = os.path.basename(file_path)

                # 跳过scheme.yaml文件
                if file_name == "scheme.yaml":
                    continue

                if file_name in existing_files:
                    skipped_files.append(file_name)
                    continue

                # 创建模板对象
                template_name = (
                    os.path.splitext(file_name)[0]
                    .replace("_", " ")
                    .replace("-", " ")
                    .title()
                )
                template = TemplateDef(
                    name=template_name,
                    file=file_name,
                    description=f"自动扫描的模板: {file_name}",
                )

                try:
                    self.scheme.add_template(template)
                    new_templates.append(template_name)
                except ValueError as e:
                    skipped_files.append(f"{file_name} ({e})")

            # 重新加载模板列表
            self.load_templates()

            # 更新状态
            self.status_label.setText(
                f"扫描完成：发现 {len(j2_files)} 个文件，新增 {len(new_templates)} 个模板"
            )
            self.status_label.setStyleSheet("color: green; font-weight: bold;")

            # 显示扫描结果
            result_message = f"扫描完成！\n\n"
            if new_templates:
                result_message += f"新添加模板 ({len(new_templates)}个):\n"
                for name in new_templates:
                    result_message += f"  ✓ {name}\n"

            if skipped_files:
                result_message += f"\n已存在模板 ({len(skipped_files)}个):\n"
                for name in skipped_files:
                    result_message += f"  - {name}\n"

            QMessageBox.information(self, "扫描结果", result_message)

            # 如果有新模板，选第一个
            if new_templates and self.template_list.count() > 0:
                self.template_list.setCurrentRow(0)

        except Exception as e:
            self.status_label.setText(f"扫描失败: {str(e)}")
            self.status_label.setStyleSheet("color: red;")
            QMessageBox.critical(self, "错误", f"扫描模板文件失败:\n{e}")

    def remove_template(self):
        """删除模板"""
        current_item = self.template_list.currentItem()
        if current_item:
            template = current_item.data(Qt.ItemDataRole.UserRole)
            if template:
                reply = QMessageBox.question(
                    self,
                    "确认删除",
                    f"确定要删除模板 '{template.name}' 吗？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )

                if reply == QMessageBox.StandardButton.Yes:
                    self.scheme.remove_template(template.name)
                    self.load_templates()
                    self.clear_template_form()


class ParametersWidget(QWidget):
    """参数配置页面"""

    def __init__(self, scheme: EditableScheme, parent=None):
        super().__init__(parent)
        self.scheme = scheme
        self.setup_ui()
        self.load_parameter_groups()

    def setup_ui(self):
        layout = QHBoxLayout(self)

        # 左侧：参数组列表
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("参数组:"))

        self.group_list = QListWidget()
        self.group_list.currentItemChanged.connect(self.on_group_selected)
        left_layout.addWidget(self.group_list)

        # 参数组操作按钮
        group_btn_layout = QHBoxLayout()

        self.add_group_btn = QPushButton("添加组")
        self.add_group_btn.clicked.connect(self.add_parameter_group)
        group_btn_layout.addWidget(self.add_group_btn)

        self.remove_group_btn = QPushButton("删除组")
        self.remove_group_btn.clicked.connect(self.remove_parameter_group)
        group_btn_layout.addWidget(self.remove_group_btn)

        left_layout.addLayout(group_btn_layout)

        # 右侧：参数编辑
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("参数详情:"))

        # 参数表格
        self.param_table = QTableWidget()
        self.param_table.setColumnCount(4)
        self.param_table.setHorizontalHeaderLabels(["参数名", "类型", "默认值", "描述"])
        self.param_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.param_table.itemChanged.connect(self.on_parameter_changed)
        right_layout.addWidget(self.param_table)

        # 参数操作按钮
        param_btn_layout = QHBoxLayout()

        self.add_param_btn = QPushButton("添加参数")
        self.add_param_btn.clicked.connect(self.add_parameter)
        param_btn_layout.addWidget(self.add_param_btn)

        self.remove_param_btn = QPushButton("删除参数")
        self.remove_param_btn.clicked.connect(self.remove_parameter)
        param_btn_layout.addWidget(self.remove_param_btn)

        right_layout.addLayout(param_btn_layout)

        # 组装布局
        left_widget = QWidget()
        left_widget.setLayout(left_layout)
        right_widget = QWidget()
        right_widget.setLayout(right_layout)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([200, 600])

        layout.addWidget(splitter)

    def load_parameter_groups(self):
        """加载参数组列表"""
        self.group_list.clear()
        for group in self.scheme.parameter_groups:
            item = QListWidgetItem(f"{group.name} ({len(group.parameters)}个参数)")
            item.setData(Qt.ItemDataRole.UserRole, group)
            self.group_list.addItem(item)

    def on_group_selected(self, current: QListWidgetItem, previous: QListWidgetItem):
        """参数组选择处理"""
        if current:
            group = current.data(Qt.ItemDataRole.UserRole)
            if group:
                self.load_parameters(group)
                self.remove_group_btn.setEnabled(True)
            else:
                self.remove_group_btn.setEnabled(False)
        else:
            self.param_table.setRowCount(0)
            self.remove_group_btn.setEnabled(False)

    def load_parameters(self, group: ParameterGroup):
        """加载参数表格"""
        self.param_table.setRowCount(len(group.parameters))

        for row, param in enumerate(group.parameters):
            # 参数名
            name_item = QTableWidgetItem(param.name)
            name_item.setData(Qt.ItemDataRole.UserRole, param)
            self.param_table.setItem(row, 0, name_item)

            # 类型
            type_item = QTableWidgetItem(param.type.value)
            self.param_table.setItem(row, 1, type_item)

            # 默认值
            default_item = QTableWidgetItem(
                str(param.default) if param.default is not None else ""
            )
            self.param_table.setItem(row, 2, default_item)

            # 描述
            desc_item = QTableWidgetItem(param.description)
            self.param_table.setItem(row, 3, desc_item)

    def on_parameter_changed(self, item: QTableWidgetItem):
        """参数变更处理"""
        if not item:
            return

        row = item.row()
        col = item.column()

        name_item = self.param_table.item(row, 0)
        if not name_item:
            return

        param = name_item.data(Qt.ItemDataRole.UserRole)
        if not param:
            return

        if col == 0:  # 参数名
            param.name = item.text()
        elif col == 1:  # 类型
            try:
                param.type = ParameterType(item.text())
            except ValueError:
                param.type = ParameterType.STRING
                item.setText(ParameterType.STRING.value)
        elif col == 2:  # 默认值
            text = item.text()
            param.default = text if text else None
        elif col == 3:  # 描述
            param.description = item.text()

    def add_parameter_group(self):
        """添加参数组"""
        group = ParameterGroup(name="新参数组")

        try:
            self.scheme.add_parameter_group(group)
            self.load_parameter_groups()

            # 选中新添加的组
            for i in range(self.group_list.count()):
                item = self.group_list.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == group:
                    self.group_list.setCurrentItem(item)
                    break
        except ValueError as e:
            QMessageBox.warning(self, "错误", str(e))

    def remove_parameter_group(self):
        """删除参数组"""
        current_item = self.group_list.currentItem()
        if current_item:
            group = current_item.data(Qt.ItemDataRole.UserRole)
            if group:
                reply = QMessageBox.question(
                    self,
                    "确认删除",
                    f"确定要删除参数组 '{group.name}' 吗？\n这将删除该组中的所有参数。",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )

                if reply == QMessageBox.StandardButton.Yes:
                    self.scheme.remove_parameter_group(group.name)
                    self.load_parameter_groups()
                    self.param_table.setRowCount(0)

    def add_parameter(self):
        """添加参数"""
        current_item = self.group_list.currentItem()
        if current_item:
            group = current_item.data(Qt.ItemDataRole.UserRole)
            if group:
                param = ParameterDef(
                    name="新参数", type=ParameterType.STRING, description="新参数描述"
                )

                try:
                    group.add_parameter(param)
                    self.load_parameters(group)
                    self.load_parameter_groups()  # 更新参数组显示
                except ValueError as e:
                    QMessageBox.warning(self, "错误", str(e))

    def remove_parameter(self):
        """删除参数"""
        current_item = self.group_list.currentItem()
        if current_item:
            group = current_item.data(Qt.ItemDataRole.UserRole)
            if group:
                current_row = self.param_table.currentRow()
                if current_row >= 0:
                    name_item = self.param_table.item(current_row, 0)
                    if name_item:
                        param_name = name_item.text()
                        group.remove_parameter(param_name)
                        self.load_parameters(group)
                        self.load_parameter_groups()  # 更新参数组显示


class PreviewWidget(QWidget):
    """YAML预览页面"""

    def __init__(self, scheme: EditableScheme, parent=None):
        super().__init__(parent)
        self.scheme = scheme
        self.setup_ui()
        self.setup_timer()
        self.update_preview()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # 预览区域
        self.preview_edit = QTextEdit()
        self.preview_edit.setReadOnly(True)
        self.preview_edit.setFont(QFont("Consolas", 10))
        layout.addWidget(QLabel("YAML预览:"))
        layout.addWidget(self.preview_edit)

        # 操作按钮
        button_layout = QHBoxLayout()

        self.refresh_btn = QPushButton("刷新预览")
        self.refresh_btn.clicked.connect(self.update_preview)
        button_layout.addWidget(self.refresh_btn)

        self.copy_btn = QPushButton("复制YAML")
        self.copy_btn.clicked.connect(self.copy_yaml)
        button_layout.addWidget(self.copy_btn)

        self.validate_btn = QPushButton("验证格式")
        self.validate_btn.clicked.connect(self.validate_yaml)
        button_layout.addWidget(self.validate_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: green;")
        layout.addWidget(self.status_label)

    def setup_timer(self):
        """设置定时器，自动更新预览"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_preview)
        self.timer.start(2000)  # 每2秒更新一次

    def update_preview(self):
        """更新YAML预览"""
        try:
            yaml_content = SchemeSerializer.to_yaml(self.scheme)
            self.preview_edit.setPlainText(yaml_content)
            self.status_label.setText("预览已更新")
            self.status_label.setStyleSheet("color: green;")
        except Exception as e:
            self.status_label.setText(f"预览错误: {e}")
            self.status_label.setStyleSheet("color: red;")

    def copy_yaml(self):
        """复制YAML内容"""
        yaml_content = self.preview_edit.toPlainText()
        if yaml_content:
            from PyQt6.QtWidgets import QApplication

            clipboard = QApplication.clipboard()
            clipboard.setText(yaml_content)
            QMessageBox.information(self, "成功", "YAML内容已复制到剪贴板")

    def validate_yaml(self):
        """验证YAML格式"""
        yaml_content = self.preview_edit.toPlainText()
        if not yaml_content:
            QMessageBox.warning(self, "警告", "YAML内容为空")
            return

        is_valid, message = SchemeSerializer.validate_yaml(yaml_content)
        if is_valid:
            QMessageBox.information(self, "验证结果", "YAML格式有效")
            self.status_label.setText("格式有效")
            self.status_label.setStyleSheet("color: green;")
        else:
            QMessageBox.warning(self, "验证结果", f"YAML格式错误:\n{message}")
            self.status_label.setText("格式错误")
            self.status_label.setStyleSheet("color: red;")


class SchemeEditorDialog(QDialog):
    """方案编辑器主对话框"""

    def __init__(self, scheme, parent=None):
        super().__init__(parent)
        self.original_scheme = scheme
        self.editable_scheme = None
        self.setup_ui()
        self.load_scheme_data()
        self.resize(800, 600)

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # 设置为模态对话框
        self.setModal(True)

        # 窗口标题
        self.setWindowTitle("方案编辑器")

        # 标签页
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Reset
            | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.save_scheme)
        button_box.rejected.connect(self.reject)

        # 添加自定义按钮
        self.import_btn = QPushButton("导入")
        self.import_btn.clicked.connect(self.import_scheme)
        button_box.addButton(self.import_btn, QDialogButtonBox.ButtonRole.ActionRole)

        self.export_btn = QPushButton("导出")
        self.export_btn.clicked.connect(self.export_scheme)
        button_box.addButton(self.export_btn, QDialogButtonBox.ButtonRole.ActionRole)

        layout.addWidget(button_box)

    def load_scheme_data(self):
        """加载方案数据"""
        try:
            self.editable_scheme = SchemeSerializer.from_scheme(self.original_scheme)

            # 添加标签页
            self.basic_info_widget = BasicInfoWidget(self.editable_scheme, self)
            self.tab_widget.addTab(self.basic_info_widget, "基本信息")

            self.templates_widget = TemplatesWidget(self.editable_scheme, self)
            self.tab_widget.addTab(self.templates_widget, "模板管理")

            self.parameters_widget = ParametersWidget(self.editable_scheme, self)
            self.tab_widget.addTab(self.parameters_widget, "参数配置")

            self.preview_widget = PreviewWidget(self.editable_scheme, self)
            self.tab_widget.addTab(self.preview_widget, "YAML预览")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载方案失败:\n{e}")

    def save_scheme(self):
        """保存方案"""
        try:
            # 验证方案
            is_valid, errors = self.editable_scheme.validate()
            if not is_valid:
                QMessageBox.warning(
                    self,
                    "验证错误",
                    "方案验证失败:\n" + "\n".join(f"- {error}" for error in errors),
                )
                return

            # 保存到文件
            if self.editable_scheme.file_path:
                SchemeSerializer.to_yaml_file(
                    self.editable_scheme, self.editable_scheme.file_path
                )
                QMessageBox.information(self, "成功", "方案已保存")
                self.accept()
            else:
                # 选择保存位置
                file_path, _ = QFileDialog.getSaveFileName(
                    self,
                    "保存方案",
                    f"{self.editable_scheme.name}.yaml",
                    "YAML Files (*.yaml);;All Files (*)",
                )
                if file_path:
                    SchemeSerializer.to_yaml_file(self.editable_scheme, file_path)
                    QMessageBox.information(self, "成功", "方案已保存")
                    self.accept()

        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存方案失败:\n{e}")

    def reset_scheme(self):
        """重置方案"""
        reply = QMessageBox.question(
            self,
            "确认重置",
            "确定要重置所有更改吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.load_scheme_data()

    def import_scheme(self):
        """导入方案"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入方案", "", "YAML Files (*.yaml);;All Files (*)"
        )

        if file_path:
            try:
                imported_scheme = SchemeSerializer.from_yaml_file(file_path)
                self.editable_scheme = imported_scheme

                # 重新加载所有标签页
                self.tab_widget.clear()
                self.load_scheme_data()

                QMessageBox.information(self, "成功", "方案已导入")

            except Exception as e:
                QMessageBox.critical(self, "错误", f"导入方案失败:\n{e}")

    def export_scheme(self):
        """导出方案"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出方案",
            f"{self.editable_scheme.name}.yaml",
            "YAML Files (*.yaml);;All Files (*)",
        )

        if file_path:
            try:
                SchemeSerializer.to_yaml_file(self.editable_scheme, file_path)
                QMessageBox.information(self, "成功", "方案已导出")

            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出方案失败:\n{e}")
