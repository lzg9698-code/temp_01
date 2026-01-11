"""核心引擎 - 整合各模块逻辑"""

from pathlib import Path
from typing import List, Dict, Any, Optional
from models import Solution, Template, RenderResult
from solution_manager import SolutionManager
from render_engine import RenderEngine
from parameter_manager import get_parameter_manager
from config import config

class SimpleEngine:
    """核心引擎 - 采用模块化架构"""

    def __init__(self):
        # 使用全局配置中的路径
        self.solutions_dir = config.SCHEMES_DIR
        self.solution_manager = SolutionManager(self.solutions_dir)
        self.render_engine = RenderEngine()
        self.param_manager = get_parameter_manager()
        
        # 初始化全局参数库
        self.param_manager.initialize(config.CONFIG_DIR)

    def load_schemes(self) -> List[Solution]:
        """加载所有方案 (为了兼容 UI，保留此方法名)"""
        return self.solution_manager.scan()

    def activate_solution(self, solution_id: str) -> Optional[Solution]:
        """激活方案并初始化渲染引擎"""
        solution = self.solution_manager.activate(solution_id)
        if solution:
            # 加载方案特定配置
            if solution.config_file:
                sol_config = self.param_manager.load_solution_config(solution.config_file)
                # 更新方案的默认值等
                if "defaults" in sol_config:
                    solution.defaults.update(sol_config["defaults"])
            
            # 初始化渲染引擎
            self.render_engine.initialize(solution)
        return solution

    def render(self, template: Template, params: Dict[str, Any]) -> RenderResult:
        """渲染 NC 代码"""
        return self.render_engine.render(template, params)

    def get_all_scheme_parameters(self, solution: Solution) -> Dict[str, Any]:
        """获取方案的所有参数定义"""
        from scheme_editor.utils import TemplateUtils
        
        # 1. 获取方案引用的所有参数定义
        effective_params = solution.get_effective_parameters(self.param_manager.library)
        
        # 2. 扫描所有模板文件，提取被使用的变量名
        used_variables = set()
        for template in solution.templates:
            template_path = solution.path / template.file
            if template_path.exists():
                try:
                    with open(template_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        # 使用统一的提取工具，替代之前的正则匹配
                        vars = TemplateUtils.extract_variables(content)
                        used_variables.update(vars)
                except Exception as e:
                    print(f"读取模板文件失败 {template_path}: {e}")
        
        # 3. 过滤参数定义
        # 仅显示在模板中被引用，或者在方案默认值(defaults)中定义的参数
        result = {}
        for group_name in solution.referenced_groups:
            group = self.param_manager.library.get_group(group_name)
            if group:
                group_params = {}
                for p_name, p_def in group.parameters.items():
                    # 检查参数是否被使用
                    is_used = p_name in used_variables
                    # 检查参数是否有方案级别的默认值覆盖
                    has_default = p_name in solution.defaults
                    
                    # 仅保留被使用的参数或有默认值的参数
                    if is_used or has_default:
                        group_params[p_name] = p_def.get_dict()
                
                if group_params:
                    result[group_name] = group_params
        
        return result
