"""渲染引擎 - 封装 Jinja2 渲染逻辑和宏处理"""

import jinja2
from pathlib import Path
from typing import Any, Dict, Optional
from models import Solution, Template, RenderResult

class RenderEngine:
    """渲染引擎"""

    def __init__(self):
        self.jinja_env: Optional[jinja2.Environment] = None
        self.current_solution: Optional[Solution] = None

    def initialize(self, solution: Solution):
        """为特定方案初始化渲染环境"""
        self.current_solution = solution
        
        # 搜索路径包括方案目录
        search_paths = [str(solution.path)]
        
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(search_paths),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
            autoescape=False,
            undefined=jinja2.StrictUndefined,
        )

        # 添加自定义过滤器
        self.jinja_env.filters["format_number"] = self._format_number
        self.jinja_env.filters["pad_zero"] = self._pad_zero

        # 注册宏
        self._register_macros(solution)

    def _register_macros(self, solution: Solution):
        """将方案定义的宏注册到全局变量或上下文中"""
        # 这里的宏处理可以更复杂，比如预加载到环境
        # 简单起见，我们将宏作为变量传递给渲染上下文
        pass

    def _format_number(self, value: Any, decimals: int = 3) -> str:
        """格式化数字"""
        try:
            num = float(value)
            return f"{num:.{decimals}f}".rstrip("0").rstrip(".")
        except (ValueError, TypeError):
            return str(value)

    def _pad_zero(self, value: Any, width: int = 4) -> str:
        """补零"""
        try:
            return str(int(value)).zfill(width)
        except (ValueError, TypeError):
            return str(value)

    def render(self, template: Template, params: Dict[str, Any]) -> RenderResult:
        """渲染模板"""
        if not self.jinja_env:
            return RenderResult(success=False, error="渲染引擎未初始化")

        try:
            # 准备上下文：合并宏
            context = params.copy()
            if self.current_solution:
                for macro in self.current_solution.macros:
                    context[macro.name] = macro.content

            tpl = self.jinja_env.get_template(template.file)
            content = tpl.render(**context)
            return RenderResult(
                success=True,
                content=content,
                template_name=template.name
            )
        except Exception as e:
            return RenderResult(
                success=False,
                error=f"渲染失败: {str(e)}",
                template_name=template.name
            )
