"""数据模型 - 极简设计"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from pathlib import Path


@dataclass
class Template:
    """模板定义"""

    name: str
    file: str
    description: str = ""

    def get_path(self, templates_dir: Path) -> Path:
        """获取模板文件完整路径"""
        return templates_dir / self.file


@dataclass
class Scheme:
    """方案配置"""

    name: str
    description: str
    templates: List[Template]
    parameters: Dict[str, Any]
    defaults: Dict[str, Any]
    file_path: Optional[Path] = field(default=None)

    def get_scheme_dir(self, templates_dir: Path) -> Path:
        """获取方案文件所在目录"""
        return self.file_path.parent if self.file_path else templates_dir

    def __post_init__(self):
        if not self.defaults:
            self.defaults = {}

    def get_default_params(self) -> Dict[str, Any]:
        """获取默认参数"""
        return self.defaults.copy()


@dataclass
class RenderResult:
    """渲染结果"""

    success: bool
    content: str = ""
    error: str = ""
    template_name: str = ""
