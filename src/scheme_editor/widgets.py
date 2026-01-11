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
from .utils import TemplateUtils
from parameter_manager import get_parameter_manager


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
        self.name_edit.setText(str(self.scheme.name))
        self.description_edit.setText(str(self.scheme.description))

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

        self.output_name_edit = QLineEdit()
        self.output_name_edit.setPlaceholderText("留空则使用模板名")
        self.output_name_edit.textChanged.connect(self.on_output_name_changed)
        details_layout.addRow("输出文件名:", self.output_name_edit)

        self.output_ext_edit = QLineEdit()
        self.output_ext_edit.setPlaceholderText("例如: nc, txt, mpf")
        self.output_ext_edit.textChanged.connect(self.on_output_ext_changed)
        details_layout.addRow("输出后缀:", self.output_ext_edit)

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
                self.name_edit.setText(str(template.name))
                self.file_edit.setText(str(template.file))
                self.description_edit.setText(str(template.description))
                self.output_name_edit.setText(str(template.output_name))
                self.output_ext_edit.setText(str(template.output_ext))
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
        self.output_name_edit.clear()
        self.output_ext_edit.clear()

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

    def on_output_name_changed(self, text: str):
        """输出文件名变更处理"""
        current_item = self.template_list.currentItem()
        if current_item:
            template = current_item.data(Qt.ItemDataRole.UserRole)
            if template:
                template.output_name = text

    def on_output_ext_changed(self, text: str):
        """输出后缀变更处理"""
        current_item = self.template_list.currentItem()
        if current_item:
            template = current_item.data(Qt.ItemDataRole.UserRole)
            if template:
                template.output_ext = text

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

            # 扫描.j2文件（包含.j2、.nc.j2、.jinja2等所有变体）
            j2_files = glob.glob(os.path.join(template_dir, "*.j2"))

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
            if clipboard:
                clipboard.setText(yaml_content)
                QMessageBox.information(self, "成功", "YAML内容已复制到剪贴板")
            else:
                QMessageBox.warning(self, "警告", "无法访问剪贴板")

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


class ParameterScanWidget(QWidget):
    """参数扫描页面"""

    def __init__(self, scheme: EditableScheme, parent=None):
        super().__init__(parent)
        self.scheme = scheme
        self.param_manager = get_parameter_manager()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # 说明文字
        info_label = QLabel(
            "扫描当前方案所有模板中使用的变量，并识别缺失的参数定义。\n"
            "您可以将缺失的变量快速添加到全局参数库中。"
        )
        info_label.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(info_label)

        # 扫描按钮
        self.scan_btn = QPushButton("开始扫描模板变量")
        self.scan_btn.setMinimumHeight(40)
        self.scan_btn.clicked.connect(self.scan_variables)
        layout.addWidget(self.scan_btn)

        # 结果列表
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(4)
        self.result_table.setHorizontalHeaderLabels(["变量名", "状态", "目标分组", "操作"])
        self.result_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.result_table)

        # 底部操作
        self.status_label = QLabel("就绪")
        layout.addWidget(self.status_label)

    def scan_variables(self):
        """扫描变量逻辑"""
        self.status_label.setText("正在扫描模板...")
        self.result_table.setRowCount(0)

        # 1. 提取所有模板中的变量
        all_vars = set()
        template_dir = (
            os.path.dirname(self.scheme.file_path) if self.scheme.file_path else None
        )

        if not template_dir:
            QMessageBox.warning(self, "警告", "方案文件路径未知，无法扫描模板")
            return

        for template in self.scheme.templates:
            file_path = os.path.join(template_dir, template.file)
            if os.path.exists(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        vars = TemplateUtils.extract_variables(content)
                        all_vars.update(vars)
                except Exception as e:
                    print(f"读取模板 {template.file} 失败: {e}")

        # 2. 获取当前已定义的变量
        library = self.param_manager.library
        defined_vars = set()
        for group in library.groups.values():
            defined_vars.update(group.parameters.keys())

        for macro in self.scheme.macros:
            if isinstance(macro, dict) and "name" in macro:
                defined_vars.add(macro["name"])

        # 3. 找出缺失的变量
        # a. 完全缺失：不在参数库，也不在宏定义中
        # b. 引用缺失：在参数库中，但其所属的分组未被当前方案引用
        
        library = self.param_manager.library
        missing_vars_data = [] # 存储 (变量名, 状态, 建议分组)
        
        # 获取当前方案已引用的所有参数名
        referenced_params = set()
        for g_name in self.scheme.referenced_groups:
            group = library.get_group(g_name)
            if group:
                referenced_params.update(group.parameters.keys())
        
        for var_name in sorted(list(all_vars)):
            # 排除已定义的宏
            if any(isinstance(m, dict) and m.get("name") == var_name for m in self.scheme.macros):
                continue
            
            # 检查是否已在方案引用的参数中
            if var_name in referenced_params:
                continue
                
            # 检查是否在参数库的其他分组中
            found_group = None
            for g_name, group in library.groups.items():
                if var_name in group.parameters:
                    found_group = g_name
                    break
            
            if found_group:
                missing_vars_data.append((var_name, f"未引用组: {found_group}", found_group))
            else:
                missing_vars_data.append((var_name, "完全缺失", ""))

        # 4. 显示结果
        self.result_table.setRowCount(len(missing_vars_data))
        for i, (var_name, status, suggest_group) in enumerate(missing_vars_data):
            self.result_table.setItem(i, 0, QTableWidgetItem(var_name))
            self.result_table.setItem(i, 1, QTableWidgetItem(status))

            # 目标分组
            group_combo = QComboBox()
            group_names = sorted(list(library.groups.keys()))
            group_combo.addItems(group_names)
            
            if suggest_group:
                idx = group_combo.findText(suggest_group)
                if idx >= 0:
                    group_combo.setCurrentIndex(idx)
            else:
                # 尝试根据名称猜测分组
                if any(x in var_name.lower() for x in ["tool", "dia", "cutter"]):
                    idx = group_combo.findText("刀具参数")
                    if idx >= 0: group_combo.setCurrentIndex(idx)
                elif any(x in var_name.lower() for x in ["pos", "x", "y", "z"]):
                    idx = group_combo.findText("位置参数")
                    if idx >= 0: group_combo.setCurrentIndex(idx)

            self.result_table.setCellWidget(i, 2, group_combo)

            # 操作按钮
            btn_text = "添加引用" if "未引用组" in status else "添加到库"
            add_btn = QPushButton(btn_text)
            add_btn.clicked.connect(
                lambda checked, v=var_name, s=status: self.handle_missing_var(v, s)
            )
            self.result_table.setCellWidget(i, 3, add_btn)

        self.status_label.setText(f"扫描完成，发现 {len(missing_vars_data)} 个待处理变量")

    def handle_missing_var(self, var_name: str, status: str):
        """处理缺失变量：添加引用或添加到库"""
        if "未引用组" in status:
            # 提取组名
            group_name = status.split(": ")[1]
            if group_name not in self.scheme.referenced_groups:
                self.scheme.referenced_groups.append(group_name)
                QMessageBox.information(self, "成功", f"已将参数组 '{group_name}' 添加到方案引用中")
                # 刷新扫描结果
                self.scan_variables()
        else:
             self.add_to_library(var_name)

    def add_to_library(self, var_name: str):
        """将变量添加到参数库"""
        # 查找当前变量所在的行，因为行索引可能会随删除操作改变
        row = -1
        for r in range(self.result_table.rowCount()):
            item = self.result_table.item(r, 0)
            if item and item.text() == var_name:
                row = r
                break
        
        if row == -1:
            return

        group_combo = self.result_table.cellWidget(row, 2)
        if not group_combo:
            return
        group_name = group_combo.currentText()

        # 导入必要的类
        try:
            from gui.param_manager import ParameterEditDialog
            from models import GlobalParameter, ParameterType as ModelParamType
        except ImportError as e:
            QMessageBox.critical(self, "错误", f"导入组件失败: {e}")
            return

        # 创建一个临时的参数定义对象
        new_param = GlobalParameter(
            name=var_name,
            type=ModelParamType.NUMBER,
            description=f"从模板扫描到的变量: {var_name}",
            required=False,  # 默认设为非必填，避免保存时因缺少默认值失败
        )

        dialog = ParameterEditDialog(new_param, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # 保存到库
            try:
                success = self.param_manager.add_parameter_to_group(group_name, new_param)
                
                if success:
                    # 更新方案的引用组
                    if group_name not in self.scheme.referenced_groups:
                        self.scheme.referenced_groups.append(group_name)

                    # 从表格中移除已添加的行
                    for r in range(self.result_table.rowCount()):
                        item = self.result_table.item(r, 0)
                        if item and item.text() == var_name:
                            self.result_table.removeRow(r)
                            break

                    QMessageBox.information(
                        self, "成功", f"参数 '{var_name}' 已添加到组 '{group_name}'"
                    )
                else:
                    QMessageBox.critical(self, "错误", f"添加参数失败，请检查参数定义是否完整（如必填项是否有默认值）")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"添加参数失败: {e}")


class SchemeEditorDialog(QDialog):
    """方案编辑器主对话框"""

    def __init__(self, scheme: EditableScheme, parent=None):
        super().__init__(parent)
        self.original_scheme = scheme
        self.editable_scheme: Optional[EditableScheme] = None
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

            self.scan_widget = ParameterScanWidget(self.editable_scheme, self)
            self.tab_widget.addTab(self.scan_widget, "参数扫描")

            self.preview_widget = PreviewWidget(self.editable_scheme, self)
            self.tab_widget.addTab(self.preview_widget, "YAML预览")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载方案失败:\n{e}")

    def save_scheme(self):
        """保存方案"""
        if not self.editable_scheme:
            QMessageBox.critical(self, "错误", "没有可保存的方案数据")
            return

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
        if not self.editable_scheme:
            QMessageBox.critical(self, "错误", "没有可导出的方案数据")
            return

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
