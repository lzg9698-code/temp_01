"""方案可视化编辑器模块

提供scheme.yaml文件的图形化编辑功能，包括：
- 基本信息编辑
- 模板管理
- 参数配置
- YAML预览

使用示例：
    from scheme_editor import SchemeEditorDialog
    editor = SchemeEditorDialog(scheme, parent=self)
    if editor.exec() == QDialog.DialogCode.Accepted:
        # 处理编辑结果
        pass
"""

from .models import EditableScheme, ParameterDef, TemplateDef, ParameterGroup
from .serializers import SchemeSerializer
from .widgets import SchemeEditorDialog

__all__ = [
    "EditableScheme",
    "ParameterDef",
    "TemplateDef",
    "ParameterGroup",
    "SchemeSerializer",
    "SchemeEditorDialog",
]
