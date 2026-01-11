import sys
import typing
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QLabel,
    QTextEdit,
    QLineEdit,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
    QFormLayout,
    QGroupBox,
    QSplitter,
    QPushButton,
    QMessageBox,
    QScrollArea,
    QFileDialog,
    QDialog,
    QTabWidget,
    QGridLayout,
    QTabBar,
)
from PyQt6.QtCore import Qt, pyqtSignal, QRegularExpression
from PyQt6.QtGui import (
    QSyntaxHighlighter,
    QTextCharFormat,
    QColor,
    QFont,
    QFontDatabase,
    QIcon,
    QPixmap,
    QPainter,
    QPen,
)

from core import SimpleEngine
from models import Solution, Template, RenderResult

# =============================================================================
# 0. AppResources - 应用资源 (图标等)
# =============================================================================

def get_app_icon() -> QIcon:
    """生成一个简易的 NC 生成器矢量图标"""
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    # 绘制背景 (圆角矩形，深灰色)
    painter.setBrush(QColor("#2c3e50"))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(4, 4, 56, 56, 12, 12)
    
    # 绘制 "NC" 字样
    font = QFont("Arial", 24, QFont.Weight.Bold)
    painter.setFont(font)
    
    # 绘制 N (橙色)
    painter.setPen(QColor("#e67e22"))
    painter.drawText(10, 42, "N")
    
    # 绘制 C (蓝色)
    painter.setPen(QColor("#3498db"))
    painter.drawText(34, 42, "C")
    
    # 绘制底部线条
    painter.setPen(QPen(QColor("#ecf0f1"), 2))
    painter.drawLine(12, 48, 52, 48)
    
    painter.end()
    return QIcon(pixmap)


# =============================================================================
# 1. NCHighlighter - NC代码语法高亮
# =============================================================================


class NCHighlighter(QSyntaxHighlighter):
    """
    G-code/NC syntax highlighter for QTextEdit.
    Implementation based on specific color rules and priorities.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []

        # 1. 注释 (Grey) - 最高优先级
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("gray"))
        comment_format.setFontItalic(True)

        # 2. G 代码 (Orange)
        g_format = QTextCharFormat()
        g_format.setForeground(QColor("#e67e22"))
        g_format.setFontWeight(QFont.Weight.Bold)

        # 3. M 代码 (Red)
        m_format = QTextCharFormat()
        m_format.setForeground(QColor("#e74c3c"))
        m_format.setFontWeight(QFont.Weight.Bold)

        # 4. 坐标轴 (Green)
        axis_format = QTextCharFormat()
        axis_format.setForeground(QColor("#27ae60"))

        # 5. 参数 (Blue)
        param_format = QTextCharFormat()
        param_format.setForeground(QColor("#2980b9"))

        # 6. 关键字 (Purple)
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#8e44ad"))
        keyword_format.setFontWeight(QFont.Weight.Bold)

        # 7. Jinja2 模板 (Pink) - 最低优先级
        jinja_format = QTextCharFormat()
        jinja_format.setForeground(QColor("#d33682"))

        # 按优先级排列规则 (列表顺序决定匹配顺序)
        # 注意：为了解决 XMW_1 被拆分的问题，关键字规则的优先级应该高于坐标轴规则
        rules = [
            # 1. 优先匹配注释：匹配从分号开始到行尾的所有内容，或者 Jinja2 注释
            (r";.*|{#.*?#}", comment_format, False),
            # 2. 常用指令关键字 (高优先级，防止复杂变量名被拆分)
            (
                r"\b(L\d+|DC|I|J|K|DECKEL|PROBE|I_STEP|STEP_\d+|S1|S4|I_SPX|I_SPY|I_SPZ|I_SPX2|I_SPY2|I_SPZ2|XMW_1|YMW_1|ZMW_1|CMW_1|AROT|ROT|TRANS|ATRANS|I_R9|ANG|OR|NOT|RND|WAITM|GOTOF|GOTOB|IF|THEN|ELSE|ENDIF|LOOP|ENDLOOP|WHILE|ENDWHILE|STOPRE|DIAMON|DIAMOF|SETMS|GROUP_BEGIN|GROUP_END|MSG|GX73|GZ73|GZ273|M17|RET|DIACYC|CYCLE\d+|SETAL|R\d+|T\d+|D\d+)\b",
                keyword_format,
                True,
            ),
            # 3. G 代码
            (r"\bG\d+(?:\.\d+)?\b", g_format, True),
            # 4. M 代码
            (r"\bM\d+(?:\.\d+)?\b", m_format, True),
            # 5. 坐标轴：支持 [+\-]?
            (r"\b[XYZCUVW][+\-]?\d*\.?\d*", axis_format, True),
            # 6. 参数
            (r"\b[FTPH][+\-]?\d*\.?\d*", param_format, True),
            # 7. Jinja2 模板标签
            (r"\{\{.*?\}\}|\{\%.*?\%\}|\{\#.*?\#\}", jinja_format, False),
        ]

        for pattern, fmt, case_insensitive in rules:
            option = QRegularExpression.PatternOption.NoPatternOption
            if case_insensitive:
                option = QRegularExpression.PatternOption.CaseInsensitiveOption
            self.highlighting_rules.append((QRegularExpression(pattern, option), fmt))

    def highlightBlock(self, text: str | None):
        if not text:
            return
        
        # 为了处理优先级，我们按顺序应用规则
        # 注意：QSyntaxHighlighter 的 setFormat 会覆盖之前的格式，
        # 所以低优先级的应该先应用，高优先级的后应用。
        # 但通常我们希望高优先级的规则（如注释）不被覆盖。
        # 这里我们反转规则列表，让高优先级（注释）最后应用。
        for pattern, fmt in reversed(self.highlighting_rules):
            iterator = pattern.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)



# =============================================================================
# 2. SolutionWidget - 方案选择组件
# =============================================================================


class SolutionWidget(QWidget):
    """
    Widget for selecting a generation solution.
    """

    solution_selected = pyqtSignal(Solution)  # Emits the full Solution object
    open_param_manager = pyqtSignal()     # Emits when parameter manager button is clicked
    scheme_edited = pyqtSignal()          # 方案编辑完成信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self._solutions: list[Solution] = []
        self._current_solution: Solution | None = None  # 当前选择的方案
        self._item_widgets: dict[str, QWidget] = {} # sol_id -> widget
        self._info_widgets: dict[str, QWidget] = {} # sol_id -> info_widget
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Title
        title = QLabel("1. 选择方案")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title)

        # Scroll area for solution list
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(2)
        
        self.scroll.setWidget(self.list_container)
        layout.addWidget(self.scroll)

        layout.addStretch()

    def set_solutions(self, solutions: list[Solution]):
        """Populate the list with solution data."""
        # Clear existing
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self._solutions = solutions
        self._item_widgets.clear()
        self._info_widgets.clear()

        for sol in solutions:
            item_container = QWidget()
            item_layout = QVBoxLayout(item_container)
            item_layout.setContentsMargins(0, 0, 0, 0)
            item_layout.setSpacing(0)

            # Header Button
            btn = QPushButton(sol.name)
            btn.setCheckable(True)
            btn.setFixedHeight(40)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding-left: 15px;
                    border: none;
                    border-radius: 4px;
                    background-color: #f5f5f5;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
                QPushButton:checked {
                    background-color: #0078D7;
                    color: white;
                    font-weight: bold;
                }
            """)
            
            # Info Area (Hidden by default)
            info_widget = QWidget()
            info_widget.setVisible(False)
            info_widget.setStyleSheet("background-color: #fafafa; border-bottom: 1px solid #eee;")
            info_layout = QFormLayout(info_widget)
            info_layout.setContentsMargins(25, 10, 10, 10)
            info_layout.setSpacing(5)
            
            v_label = QLabel(sol.version or "1.0.0")
            v_label.setStyleSheet("color: #0078D7; font-weight: bold;")
            info_layout.addRow("版本:", v_label)
            
            d_label = QLabel(sol.description or "无描述")
            d_label.setWordWrap(True)
            d_label.setStyleSheet("color: #666; font-style: italic;")
            info_layout.addRow("描述:", d_label)

            item_layout.addWidget(btn)
            item_layout.addWidget(info_widget)
            
            self.list_layout.addWidget(item_container)
            self._item_widgets[sol.id] = btn
            self._info_widgets[sol.id] = info_widget

            # Connect click
            btn.clicked.connect(lambda checked, s=sol: self._on_solution_clicked(s))

        self.list_layout.addStretch()

        # Select first by default if any
        if solutions:
            if self._current_solution:
                # Try to restore selection
                found = False
                for s in solutions:
                    if s.id == self._current_solution.id:
                        self._on_solution_clicked(s)
                        found = True
                        break
                if not found:
                    self._on_solution_clicked(solutions[0])
            else:
                self._on_solution_clicked(solutions[0])

    def _on_solution_clicked(self, solution: Solution):
        """Handle solution selection."""
        self._current_solution = solution
        
        # Update UI states
        for sol_id, btn in self._item_widgets.items():
            is_selected = (sol_id == solution.id)
            btn.blockSignals(True)
            btn.setChecked(is_selected)
            btn.blockSignals(False)
            
            # Toggle info visibility
            info = self._info_widgets[sol_id]
            info.setVisible(is_selected)

        self.solution_selected.emit(solution)

    def on_edit_solution(self):
        """编辑当前方案"""
        if self._current_solution:
            try:
                from scheme_editor import SchemeEditorDialog

                # TODO: Update SchemeEditorDialog to handle Solution
                editor = SchemeEditorDialog(self._current_solution, self)

                # 设置与主窗口相同的位置和大小
                main_window = self.parent()
                while main_window and not isinstance(main_window, QMainWindow):
                    main_window = main_window.parent()

                if main_window:
                    editor.setGeometry(main_window.geometry())

                if editor.exec() == QDialog.DialogCode.Accepted:
                    # 编辑完成，发出信号
                    self.scheme_edited.emit()

            except Exception as e:
                QMessageBox.critical(self, "错误", f"打开编辑器失败:\n{e}")


# =============================================================================
# 3. ParamWidget - 参数输入组件
# =============================================================================


class NoScrollSpinBox(QSpinBox):
    """禁用滚轮和上下箭头的 SpinBox，并支持回车信号"""
    returnPressed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)

    def wheelEvent(self, event):
        event.ignore()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.returnPressed.emit()
        else:
            super().keyPressEvent(event)


class NoScrollDoubleSpinBox(QDoubleSpinBox):
    """禁用滚轮和上下箭头的 DoubleSpinBox，并支持回车信号"""
    returnPressed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)

    def wheelEvent(self, event):
        event.ignore()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.returnPressed.emit()
        else:
            super().keyPressEvent(event)


class ParamWidget(QWidget):
    """
    Dynamic parameter input widget based on schema.
    """

    params_changed = pyqtSignal(dict)  # Emits dictionary of current values
    validation_changed = pyqtSignal(bool)  # Emits True if all valid, False otherwise

    def __init__(self, parent=None):
        super().__init__(parent)
        self.input_widgets = {}  # Map param_key -> widget
        self.ordered_widgets = [] # List of widgets in display order
        self.param_defs = {}
        self._is_valid = True
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Title
        title = QLabel("2. 配置参数")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        main_layout.addWidget(title)

        # Scroll Area for Form
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        self.form_container = QWidget()
        self.form_layout = QVBoxLayout(self.form_container)
        self.form_layout.setContentsMargins(0, 0, 15, 0) # 增加右侧边距，避免被滚动条遮挡
        self.form_layout.setSpacing(10)

        scroll.setWidget(self.form_container)
        main_layout.addWidget(scroll)

    def build_form(self, params_def: dict, defaults: dict | None = None):
        """
        Build input fields based on parameter definitions using Label | Input | Unit layout.
        """
        if defaults is None:
            defaults = {}

        # 彻底清除现有布局中的所有内容（包括 widget 和 stretch）
        while self.form_layout.count():
            item = self.form_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.input_widgets.clear()
        self.ordered_widgets.clear()
        self.param_defs.clear()

        # Build groups
        for group_name, items in params_def.items():
            group_box = QGroupBox(group_name)
            group_layout = QGridLayout()  # Use QGridLayout for 3-column alignment
            group_layout.setColumnStretch(0, 1)  # Label
            group_layout.setColumnStretch(1, 0)  # Input
            group_layout.setColumnStretch(2, 0)  # Unit
            group_layout.setSpacing(10)

            row = 0
            for p_key, p_def in items.items():
                self.param_defs[p_key] = p_def
                p_type = p_def.get("type", "string").lower()
                default_val = defaults.get(p_key, p_def.get("default"))

                # 1. Label - 优先显示描述，右对齐紧贴输入框
                display_name = p_def.get("description") or p_key
                label = QLabel(display_name)
                label.setToolTip(f"变量名: {p_key}")
                label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                group_layout.addWidget(label, row, 0)

                # 2. Input Widget
                widget = None
                if p_type in ["int", "integer"]:
                    widget = NoScrollSpinBox()
                    widget.setFixedWidth(80)
                    widget.setAlignment(Qt.AlignmentFlag.AlignRight)
                    widget.setRange(int(p_def.get("min", -99999)), int(p_def.get("max", 99999)))
                    try:
                        val = int(default_val) if default_val is not None and str(default_val).strip() != "" else 0
                    except (ValueError, TypeError):
                        val = 0
                    widget.setValue(val)
                    widget.valueChanged.connect(self._on_value_changed)
                    widget.returnPressed.connect(self._focus_next_widget)

                elif p_type in ["float", "number"]:
                    widget = NoScrollDoubleSpinBox()
                    widget.setFixedWidth(80)
                    widget.setAlignment(Qt.AlignmentFlag.AlignRight)
                    widget.setRange(float(p_def.get("min", -99999.0)), float(p_def.get("max", 99999.0)))
                    widget.setDecimals(3)
                    try:
                        val = float(default_val) if default_val is not None and str(default_val).strip() != "" else 0.0
                    except (ValueError, TypeError):
                        val = 0.0
                    widget.setValue(val)
                    widget.valueChanged.connect(self._on_value_changed)
                    widget.returnPressed.connect(self._focus_next_widget)

                elif p_type in ["bool", "boolean"]:
                    widget = QCheckBox()
                    widget.setChecked(bool(default_val) if default_val is not None and str(default_val).strip() != "" else False)
                    widget.stateChanged.connect(self._on_value_changed)

                elif p_type in ["select", "choice"]:
                    widget = QComboBox()
                    widget.setFixedWidth(80)
                    options = p_def.get("options", [])
                    widget.addItems([str(opt) for opt in options])
                    if str(default_val) in [str(opt) for opt in options]:
                        widget.setCurrentText(str(default_val))
                    widget.currentTextChanged.connect(self._on_value_changed)

                else:
                    widget = QLineEdit()
                    widget.setFixedWidth(80)
                    widget.setAlignment(Qt.AlignmentFlag.AlignRight)
                    widget.setText(str(default_val) if default_val is not None and str(default_val).strip() != "" else "")
                    widget.textChanged.connect(self._on_value_changed)
                    widget.returnPressed.connect(self._focus_next_widget)

                if widget:
                    self.input_widgets[p_key] = widget
                    self.ordered_widgets.append(widget)
                    group_layout.addWidget(widget, row, 1)

                # 3. Unit
                unit = p_def.get("unit", "")
                unit_label = QLabel(unit)
                unit_label.setStyleSheet("color: #888; font-size: 10px;")
                unit_label.setFixedWidth(50) # 增加宽度以完整显示 mm/min 等单位
                group_layout.addWidget(unit_label, row, 2)

                row += 1

            group_box.setLayout(group_layout)
            self.form_layout.addWidget(group_box)

        self.form_layout.addStretch()
        self._on_value_changed()

    def _focus_next_widget(self):
        """Move focus to the next input widget."""
        sender = self.sender()
        if sender in self.ordered_widgets:
            idx = self.ordered_widgets.index(sender)
            if idx + 1 < len(self.ordered_widgets):
                next_widget = self.ordered_widgets[idx + 1]
                next_widget.setFocus()
                if isinstance(next_widget, (QLineEdit, QSpinBox, QDoubleSpinBox)):
                    next_widget.selectAll()

    def _on_value_changed(self, *args):
        """Handle input changes and perform real-time validation."""
        current_values = self.get_values()
        is_all_valid = True

        for p_key, widget in self.input_widgets.items():
            p_def = self.param_defs.get(p_key, {})
            val = current_values.get(p_key)
            
            # Validation logic
            is_valid = True
            p_type = p_def.get("type", "string").lower()

            if p_type in ["int", "integer", "float", "number"]:
                try:
                    num_val = float(val)
                    min_v = p_def.get("min")
                    max_v = p_def.get("max")
                    if min_v is not None and num_val < float(min_v):
                        is_valid = False
                    if max_v is not None and num_val > float(max_v):
                        is_valid = False
                except:
                    is_valid = False
            
            # UI Feedback
            if not is_valid:
                widget.setStyleSheet("background-color: #FFCCCC; border: 1px solid red;")
                is_all_valid = False
            else:
                widget.setStyleSheet("")

        if is_all_valid != self._is_valid:
            self._is_valid = is_all_valid
            self.validation_changed.emit(is_all_valid)

        self.params_changed.emit(current_values)

    def get_values(self) -> dict:
        """Collect current values from all widgets."""
        values = {}
        for p_key, widget in self.input_widgets.items():
            if isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                values[p_key] = widget.value()
            elif isinstance(widget, QCheckBox):
                values[p_key] = widget.isChecked()
            elif isinstance(widget, QComboBox):
                values[p_key] = widget.currentText()
            elif isinstance(widget, QLineEdit):
                values[p_key] = widget.text()
        return values


# =============================================================================
# 4. PreviewWidget - 预览输出组件
# =============================================================================


class PreviewWidget(QWidget):
    """
    Widget for previewing and exporting generated NC code.
    """

    template_changed = pyqtSignal(int)  # Emits the selected template index

    def __init__(self, parent=None):
        super().__init__(parent)
        self._templates: list[Template] = []
        self._last_result: RenderResult | None = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        # Title
        title_layout = QHBoxLayout()
        title = QLabel("3. 预览与导出")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title_layout.addWidget(title)
        title_layout.addStretch()
        layout.addLayout(title_layout)

        # Template Tabs (Using QTabBar to avoid empty content space)
        self.tabs = QTabBar()
        self.tabs.setDocumentMode(True)
        self.tabs.setExpanding(False)
        self.tabs.setDrawBase(False) # 移除底部的线条
        self.tabs.setStyleSheet("""
            QTabBar::tab {
                background-color: #f5f5f5;
                padding: 8px 15px;
                border: 1px solid #ddd;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
                min-width: 80px;
                font-size: 13px;
            }
            QTabBar::tab:hover {
                background-color: #e0e0e0;
            }
            QTabBar::tab:selected {
                background-color: #0078D7;
                color: white;
                font-weight: bold;
                border-color: #0078D7;
            }
        """)
        self.tabs.currentChanged.connect(self._on_tab_changed)
        layout.addWidget(self.tabs)

        # Text Editor
        self.editor = QTextEdit()
        self.editor.setReadOnly(True)
        self.editor.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)

        # Set monospace font
        font = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        font.setPointSize(10)
        self.editor.setFont(font)

        # Add highlighter
        self.highlighter = NCHighlighter(self.editor.document())

        layout.addWidget(self.editor)

        # Export Button
        self.export_btn = QPushButton("导出 NC 代码")
        self.export_btn.setFixedHeight(40)
        self.export_btn.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.export_btn.clicked.connect(self.export_file)
        layout.addWidget(self.export_btn)

    def set_templates(self, templates: list[Template]):
        """Populate the tabs with available templates."""
        self._templates = templates
        self.tabs.blockSignals(True)
        
        # Clear existing tabs
        while self.tabs.count() > 0:
            self.tabs.removeTab(0)
            
        for template in templates:
            self.tabs.addTab(template.name)
        self.tabs.blockSignals(False)

        if templates:
            self.tabs.setCurrentIndex(0)
            self._on_tab_changed(0)

    def _on_tab_changed(self, index):
        """Handle template selection via tabs."""
        if index >= 0:
            self.template_changed.emit(index)

    def update_preview(self, result: RenderResult):
        """Update the editor with new generated code."""
        self._last_result = result
        self.editor.setPlainText(result.content)

    def export_file(self):
        """Open a file dialog to save the generated NC code."""
        if not self._last_result:
            QMessageBox.warning(self, "警告", "没有可导出的代码。")
            return

        # 尝试从当前选中的模板获取文件名配置
        idx = self.tabs.currentIndex()
        default_name = "output.nc"
        if 0 <= idx < len(self._templates):
            tpl = self._templates[idx]
            name = tpl.output_name or tpl.name
            ext = tpl.output_ext or "nc"
            if ext and not ext.startswith("."):
                ext = f".{ext}"
            default_name = f"{name}{ext}"
        
        # 使用 QFileDialog 并强制使用内置样式以支持定位
        dialog = QFileDialog(self.window())
        dialog.setOption(QFileDialog.Option.DontUseNativeDialog)
        dialog.setWindowTitle("导出 NC 代码")
        dialog.setDirectory(".")
        dialog.selectFile(default_name)
        dialog.setNameFilter("NC Files (*.nc);;All Files (*)")
        dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        
        # 居中逻辑
        main_win = self.window()
        if main_win:
            dialog.setWindowModality(Qt.WindowModality.WindowModal)
            dialog.resize(800, 600)
            
            # 计算中心位置
            win_geo = main_win.geometry()
            size = dialog.size()
            x = win_geo.center().x() - size.width() // 2
            y = win_geo.center().y() - size.height() // 2
            dialog.move(x, y)

        if dialog.exec():
            file_paths = dialog.selectedFiles()
            if file_paths:
                file_path = file_paths[0]
                try:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(self._last_result.content)
                    QMessageBox.information(self.window(), "成功", f"文件已保存至:\n{file_path}")
                except Exception as e:
                    QMessageBox.critical(self.window(), "错误", f"保存文件失败:\n{e}")



# =============================================================================
# 5. MainWindow - 主窗口
# =============================================================================


class MainWindow(QMainWindow):
    """
    Main Application Window integrating Solution, Param, and Preview widgets.
    """

    def __init__(self, engine: SimpleEngine):
        super().__init__()
        self.engine = engine  # Store the engine instance
        self.setWindowTitle("NC Code Generator (Simple UI)")
        self.setWindowIcon(get_app_icon())
        self.resize(1000, 600)

        self.current_solution: Solution | None = None
        self.current_template: Template | None = None
        self.current_params = {}

        self._setup_ui()
        self._setup_menu()
        self._load_data()

    def _setup_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        
        # Left: Solution Selection (Navigator)
        self.solution_widget = SolutionWidget()
        self.solution_widget.solution_selected.connect(self._on_solution_selected)
        self.solution_widget.scheme_edited.connect(self.reload_schemes)
        
        # Middle: Parameter Input (Inspector)
        self.param_widget = ParamWidget()
        self.param_widget.params_changed.connect(self._on_params_changed)
        self.param_widget.validation_changed.connect(self._on_validation_changed)
        
        # Right: Preview and Export (Preview)
        self.preview_widget = PreviewWidget()
        self.preview_widget.template_changed.connect(self._on_template_selected)

        # Splitter for flexible layout
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.addWidget(self.solution_widget)
        self.splitter.addWidget(self.param_widget)
        self.splitter.addWidget(self.preview_widget)
        
        # Set initial sizes for three columns
        self.splitter.setSizes([200, 350, 450])
        
        self.main_layout.addWidget(self.splitter)

    def _setup_menu(self):
        """Create the tools menu."""
        menubar = self.menuBar()
        tools_menu = menubar.addMenu("工具")
        
        edit_action = tools_menu.addAction("编辑当前方案")
        edit_action.triggered.connect(self.solution_widget.on_edit_solution)
        
        param_lib_action = tools_menu.addAction("全局参数库")
        param_lib_action.triggered.connect(self._open_parameter_manager)

    def _on_validation_changed(self, is_valid: bool):
        """Enable or disable export button based on validation."""
        self.preview_widget.export_btn.setEnabled(is_valid)
        if not is_valid:
            self.preview_widget.export_btn.setToolTip("参数输入有误，请检查标红项")
        else:
            self.preview_widget.export_btn.setToolTip("")

    def _open_parameter_manager(self):
        """打开参数管理器"""
        try:
            # 导入参数管理器
            from gui.param_manager import show_parameter_manager

            # 初始化参数管理器
            from parameter_manager import get_parameter_manager

            manager = get_parameter_manager()
            from config import config
            manager.initialize(config.CONFIG_DIR)

            # 显示参数管理器窗口，保存引用防止被垃圾回收
            if not hasattr(self, "_param_manager_window") or self._param_manager_window is None:
                self._param_manager_window = show_parameter_manager(self)
            else:
                self._param_manager_window.show()
                self._param_manager_window.raise_()
                self._param_manager_window.activateWindow()

        except Exception as e:
            QMessageBox.warning(self, "错误", f"打开参数管理器失败: {e}")

    def _on_reload_schemes(self):
        """重新加载所有方案"""
        try:
            self.engine.load_schemes()
            self._load_data()
            QMessageBox.information(self.window(), "成功", "方案已重载")
        except Exception as e:
            QMessageBox.warning(self.window(), "错误", f"重载方案失败: {e}")

    def _load_data(self):
        """
        Load solutions from engine.
        """
        solutions = self.engine.load_schemes()
        self.solution_widget.set_solutions(solutions)

    def reload_schemes(self):
        """重新加载方案（用于编辑器更新后）"""
        self._load_data()

    def _on_solution_selected(self, solution: Solution):
        """Handle solution selection: load params and reset preview."""
        self.current_solution = solution
        
        # 激活方案（初始化渲染引擎和加载配置）
        self.engine.activate_solution(solution.id)

        # Build form based on solution parameters
        # engine.get_all_scheme_parameters returns a dictionary grouped by referenced_groups
        params_def = self.engine.get_all_scheme_parameters(solution)
        
        # Pass parameters directly (already grouped)
        self.param_widget.build_form(params_def, solution.defaults)

        # Update template list in preview widget
        self.preview_widget.set_templates(solution.templates)


    def _on_params_changed(self, values: dict):
        """Handle parameter changes."""
        self.current_params = values
        self._render()

    def _on_template_selected(self, index: int):
        """Handle template selection."""
        if self.current_solution and 0 <= index < len(self.current_solution.templates):
            self.current_template = self.current_solution.templates[index]
            self._render()

    def _render(self):
        """Render the current template with current parameters."""
        if not self.current_solution or not self.current_template:
            return
            
        try:
            result = self.engine.render(
                self.current_template,
                self.current_params
            )
            self.preview_widget.update_preview(result)
        except Exception as e:
            # Don't show dialog for render errors to avoid UI spam, just show in preview
            from models import RenderResult
            self.preview_widget.update_preview(RenderResult(content=f"渲染错误:\n{e}"))


# =============================================================================
# Main Execution
# =============================================================================

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Optional: Set a dark theme for better code visibility
    app.setStyle("Fusion")

    engine = SimpleEngine()
    window = MainWindow(engine)
    window.show()

    sys.exit(app.exec())
