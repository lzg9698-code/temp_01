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
)
from PyQt6.QtCore import Qt, pyqtSignal, QRegularExpression
from PyQt6.QtGui import (
    QSyntaxHighlighter,
    QTextCharFormat,
    QColor,
    QFont,
    QFontDatabase,
)

from core import SimpleEngine
from models import Scheme, Template, RenderResult

# =============================================================================
# 1. NCHighlighter - NC代码语法高亮
# =============================================================================


class NCHighlighter(QSyntaxHighlighter):
    """
    G-code/NC syntax highlighter for QTextEdit.
    Supports G-codes, M-codes, Coordinates, Comments, and generic numbers.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []

        # Define text formats
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#0000FF"))  # Blue for G-codes
        keyword_format.setFontWeight(QFont.Weight.Bold)

        mcode_format = QTextCharFormat()
        mcode_format.setForeground(QColor("#A52A2A"))  # Brown/Red for M-codes
        mcode_format.setFontWeight(QFont.Weight.Bold)

        coord_format = QTextCharFormat()
        coord_format.setForeground(QColor("#800080"))  # Purple for X, Y, Z, I, J, K

        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#008080"))  # Teal for raw numbers

        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#808080"))  # Gray for comments
        comment_format.setFontItalic(True)

        # Define rules (regex patterns)
        rules = [
            # G-codes (e.g., G00, G1, G90)
            (r"\bG\d+(\.\d+)?\b", keyword_format),
            # M-codes (e.g., M03, M30)
            (r"\bM\d+(\.\d+)?\b", mcode_format),
            # Coordinates (e.g., X100, Y-50.5, Z10)
            (r"\b[XYZIJKR]-?\d+(\.\d+)?\b", coord_format),
            # Feeds and Speeds (F, S, T)
            (r"\b[FST]\d+(\.\d+)?\b", coord_format),
            # Comments: (...) or ; ...
            (r"\(.*\)", comment_format),
            (r";.*", comment_format),
        ]

        # Compile regexes
        for pattern, fmt in rules:
            self.highlighting_rules.append((QRegularExpression(pattern), fmt))

    def highlightBlock(self, text: str | None):
        """Apply highlighting rules to the given text block."""
        if not text:
            return
        for pattern, fmt in self.highlighting_rules:
            iterator = pattern.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)


# =============================================================================
# 2. SchemeWidget - 方案选择组件
# =============================================================================


class SchemeWidget(QWidget):
    """
    Widget for selecting a generation scheme/template.
    """

    scheme_selected = pyqtSignal(Scheme)  # Emits the full Scheme object

    def __init__(self, parent=None):
        super().__init__(parent)
        self._schemes: list[Scheme] = []
        self._current_scheme: Scheme | None = None  # 当前选择的方案
        self.desc_label = QLabel()  # Initialize to avoid linter errors
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Title
        title = QLabel("1. 选择方案")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title)

        # Combo Box
        self.combo = QComboBox()
        self.combo.currentIndexChanged.connect(self._on_index_changed)
        layout.addWidget(self.combo)

        # Description Area
        self.desc_label = QLabel("请选择一个加工方案")
        self.desc_label.setWordWrap(True)
        self.desc_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.desc_label)

        # Edit Scheme Button
        self.edit_btn = QPushButton("编辑方案")
        self.edit_btn.setEnabled(False)  # 初始禁用
        self.edit_btn.clicked.connect(self.on_edit_scheme)
        layout.addWidget(self.edit_btn)

        layout.addStretch()

    def set_schemes(self, schemes: list[Scheme]):
        """Populate the combo box with scheme data."""
        self._schemes = schemes
        self.combo.clear()
        for scheme in schemes:
            self.combo.addItem(scheme.name)

        # Trigger default selection
        if schemes:
            self.combo.setCurrentIndex(0)
            self._on_index_changed(0)

    def _on_index_changed(self, index):
        if 0 <= index < len(self._schemes):
            scheme = self._schemes[index]
            if self.desc_label:
                self.desc_label.setText(
                    scheme.description or "No description available."
                )
            self.scheme_selected.emit(scheme)
            self._current_scheme = scheme
            self.edit_btn.setEnabled(True)  # 启用编辑按钮

    def on_edit_scheme(self):
        """编辑当前方案"""
        if self._current_scheme:
            try:
                from scheme_editor import SchemeEditorDialog

                editor = SchemeEditorDialog(self._current_scheme, self)

                # 设置与主窗口相同的位置和大小
                main_window = self.parent()
                while main_window and not isinstance(main_window, QMainWindow):
                    main_window = main_window.parent()

                if main_window:
                    editor.setGeometry(main_window.geometry())

                if editor.exec() == QDialog.DialogCode.Accepted:
                    # 编辑完成，通知主界面重新加载方案
                    if hasattr(self.parent(), "reload_schemes"):
                        self.parent().reload_schemes()

            except Exception as e:
                QMessageBox.critical(self, "错误", f"打开编辑器失败:\n{e}")


# =============================================================================
# 3. ParamWidget - 参数输入组件
# =============================================================================


class ParamWidget(QWidget):
    """
    Dynamic parameter input widget based on schema.
    """

    params_changed = pyqtSignal(dict)  # Emits dictionary of current values

    def __init__(self, parent=None):
        super().__init__(parent)
        self.input_widgets = {}  # Map param_key -> widget
        self.param_defs = {}
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
        self.form_layout = QVBoxLayout(
            self.form_container
        )  # Changed to QVBoxLayout to support groups
        self.form_layout.setContentsMargins(0, 0, 0, 0)
        self.form_layout.setSpacing(10)

        scroll.setWidget(self.form_container)
        main_layout.addWidget(scroll)

    def build_form(self, params_def: dict, defaults: dict | None = None):
        """
        Build input fields based on parameter definitions.
        params_def structure example:
        {
            "Group Name": {
                "param_name": {"type": "number", "default": 100, ...}
            }
        }
        """
        if defaults is None:
            defaults = {}

        # Clear existing form
        while self.form_layout.count():
            item = self.form_layout.takeAt(0)
            if item:
                widget = item.widget()
                if widget:
                    widget.deleteLater()

        self.input_widgets.clear()
        self.param_defs = params_def

        # Handle flat or grouped structure
        # If the first value is a dict containing 'type', it's flat.
        # Otherwise assume grouped.
        is_grouped = True
        first_val = next(iter(params_def.values())) if params_def else None
        if first_val and "type" in first_val:
            is_grouped = False
            # Normalize to single group
            params_def = {"Parameters": params_def}

        for group_name, group_params in params_def.items():
            group_box = QGroupBox(group_name)
            group_layout = QFormLayout()
            group_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

            for key, p_def in group_params.items():
                label_text = p_def.get("description", key)  # Use description as label
                p_type = p_def.get("type", "string")

                # Priority: defaults dict > param def default > type default
                default_val = defaults.get(key)
                if default_val is None:
                    default_val = p_def.get("default")

                widget = None

                if p_type == "int" or p_type == "integer":
                    widget = QSpinBox()
                    widget.setRange(
                        int(p_def.get("min", -99999)), int(p_def.get("max", 99999))
                    )
                    widget.setValue(int(default_val) if default_val is not None else 0)
                    widget.valueChanged.connect(self._on_value_changed)

                elif p_type == "float" or p_type == "number":
                    widget = QDoubleSpinBox()
                    widget.setRange(
                        float(p_def.get("min", -99999.0)),
                        float(p_def.get("max", 99999.0)),
                    )
                    widget.setDecimals(3)
                    widget.setValue(
                        float(default_val) if default_val is not None else 0.0
                    )
                    widget.valueChanged.connect(self._on_value_changed)

                elif p_type == "bool" or p_type == "boolean":
                    widget = QCheckBox()
                    widget.setChecked(
                        bool(default_val) if default_val is not None else False
                    )
                    widget.stateChanged.connect(self._on_value_changed)

                elif p_type == "select" or p_type == "choice":
                    widget = QComboBox()
                    options = p_def.get("options", [])
                    widget.addItems([str(opt) for opt in options])
                    if default_val in options:
                        widget.setCurrentText(str(default_val))
                    widget.currentTextChanged.connect(self._on_value_changed)

                else:  # string/text default
                    widget = QLineEdit()
                    widget.setText(str(default_val) if default_val is not None else "")
                    widget.textChanged.connect(self._on_value_changed)

                if widget:
                    group_layout.addRow(f"{label_text}:", widget)
                    self.input_widgets[key] = widget

            group_box.setLayout(group_layout)
            self.form_layout.addWidget(group_box)

        self.form_layout.addStretch()

        # Trigger initial change
        self._on_value_changed()

    def get_values(self) -> dict:
        """Retrieve current values from all input widgets."""
        values = {}
        for key, widget in self.input_widgets.items():
            if isinstance(widget, QSpinBox):
                values[key] = widget.value()
            elif isinstance(widget, QDoubleSpinBox):
                values[key] = widget.value()
            elif isinstance(widget, QCheckBox):
                values[key] = widget.isChecked()
            elif isinstance(widget, QComboBox):
                values[key] = widget.currentText()
            elif isinstance(widget, QLineEdit):
                values[key] = widget.text()
        return values

    def _on_value_changed(self, *args):
        """Internal slot to emit params_changed signal."""
        self.params_changed.emit(self.get_values())


# =============================================================================
# 4. PreviewWidget - 预览输出组件
# =============================================================================


class PreviewWidget(QWidget):
    """
    Displays the generated NC code with syntax highlighting.
    """

    template_changed = pyqtSignal(Template)  # Emits the selected template

    def __init__(self, parent=None):
        super().__init__(parent)
        self._templates: list[Template] = []
        self._current_template: Template | None = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Header
        header_layout = QHBoxLayout()
        title = QLabel("3. 代码预览")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        header_layout.addWidget(title)

        header_layout.addStretch()

        self.btn_copy = QPushButton("复制全部")
        self.btn_copy.clicked.connect(self.copy_to_clipboard)
        header_layout.addWidget(self.btn_copy)

        self.btn_export = QPushButton("导出文件")
        self.btn_export.clicked.connect(self.export_file)
        header_layout.addWidget(self.btn_export)

        layout.addLayout(header_layout)

        # Template Selector
        tpl_layout = QHBoxLayout()
        tpl_layout.addWidget(QLabel("选择模板:"))
        self.combo_tpl = QComboBox()
        self.combo_tpl.currentIndexChanged.connect(self._on_template_changed)
        tpl_layout.addWidget(self.combo_tpl, 1)
        layout.addLayout(tpl_layout)

        # Text Editor
        self.editor = QTextEdit()
        self.editor.setReadOnly(True)

        # Set Monospace Font
        font = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        font.setPointSize(10)
        self.editor.setFont(font)

        # Apply Highlighter
        self.highlighter = NCHighlighter(self.editor.document())

        layout.addWidget(self.editor)

    def set_templates(self, templates: list[Template]):
        """Update template list."""
        self._templates = templates
        self.combo_tpl.blockSignals(True)
        self.combo_tpl.clear()
        for tpl in templates:
            self.combo_tpl.addItem(tpl.name)
        self.combo_tpl.blockSignals(False)

        if templates:
            self.combo_tpl.setCurrentIndex(0)
            self._on_template_changed(0)
        else:
            self._current_template = None
            self.set_content("")

    def _on_template_changed(self, index):
        if 0 <= index < len(self._templates):
            self._current_template = self._templates[index]
            self.template_changed.emit(self._current_template)

    def set_content(self, text: str):
        """Update the preview text."""
        self.editor.setPlainText(text)

    def copy_to_clipboard(self):
        """Copy current content to system clipboard."""
        if not self.editor.toPlainText():
            return
        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(self.editor.toPlainText())
            QMessageBox.information(self, "成功", "代码已复制到剪贴板。")

    def export_file(self):
        """Export current content to a file."""
        content = self.editor.toPlainText()
        if not content:
            QMessageBox.warning(self, "警告", "没有内容可导出")
            return

        default_name = "output.nc"
        if self._current_template:
            default_name = f"{self._current_template.name}.nc"

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出NC代码",
            default_name,
            "NC Files (*.nc);;Text Files (*.txt);;All Files (*)",
        )

        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                QMessageBox.information(self, "成功", f"文件已保存到:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存文件失败:\n{e}")


# =============================================================================
# 5. MainWindow - 主窗口
# =============================================================================


class MainWindow(QMainWindow):
    """
    Main Application Window integrating Scheme, Param, and Preview widgets.
    """

    def __init__(self, engine: SimpleEngine):
        super().__init__()
        self.engine = engine  # Store the engine instance
        self.setWindowTitle("NC Code Generator (Simple UI)")
        self.resize(1000, 600)

        self.current_scheme: Scheme | None = None
        self.current_template: Template | None = None
        self.current_params = {}

        self._init_ui()
        self._load_data()

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Using QSplitter for adjustable columns
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 1. Left Panel: Schemes
        self.scheme_widget = SchemeWidget()
        self.scheme_widget.scheme_selected.connect(self._on_scheme_selected)
        splitter.addWidget(self.scheme_widget)

        # 2. Middle Panel: Parameters
        self.param_widget = ParamWidget()
        self.param_widget.params_changed.connect(self._on_params_changed)
        splitter.addWidget(self.param_widget)

        # 3. Right Panel: Preview
        self.preview_widget = PreviewWidget()
        self.preview_widget.template_changed.connect(self._on_template_selected)
        splitter.addWidget(self.preview_widget)

        # Set initial sizes ratio (20%, 30%, 50%)
        splitter.setSizes([200, 300, 500])

        main_layout.addWidget(splitter)

    def _load_data(self):
        """
        Load schemes from engine.
        """
        schemes = self.engine.load_schemes()
        self.scheme_widget.set_schemes(schemes)

    def reload_schemes(self):
        """重新加载方案（用于编辑器更新后）"""
        self._load_data()

    def _on_scheme_selected(self, scheme: Scheme):
        """Handle scheme selection: load params and reset preview."""
        self.current_scheme = scheme

        # Build form based on scheme parameters
        # Pass defaults to pre-fill the form
        self.param_widget.build_form(scheme.parameters, scheme.defaults)

        # Update template list in preview widget
        self.preview_widget.set_templates(scheme.templates)

        # Note: build_form triggers params_changed, which calls _on_params_changed
        # set_templates triggers template_changed, which calls _on_template_selected

    def _on_params_changed(self, values: dict):
        """Handle parameter changes: regenerate preview."""
        self.current_params = values
        self._generate_preview()

    def _on_template_selected(self, template: Template):
        """Handle template selection: regenerate preview."""
        self.current_template = template
        self._generate_preview()

    def _generate_preview(self):
        """
        Generate preview code using the engine.
        """
        if not self.current_scheme or not self.current_template:
            return

        # Call engine to render
        result: RenderResult = self.engine.render_template(
            self.current_scheme, self.current_template, self.current_params
        )

        if result.success:
            self.preview_widget.set_content(result.content)
        else:
            self.preview_widget.set_content(
                f"Error rendering template:\n{result.error}"
            )


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
