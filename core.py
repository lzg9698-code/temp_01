"""核心引擎 - 所有业务逻辑"""

import re
import yaml
from pathlib import Path
from typing import List, Dict, Any, Tuple
import jinja2

from config import config
from models import Scheme, Template, RenderResult

class SimpleEngine:
    """超简化NC代码生成引擎"""
    
    def __init__(self):
        self.schemes_dir = config.SCHEMES_DIR
        self.templates_dir = config.TEMPLATES_DIR
        self._init_jinja_env()
    
    def _init_jinja_env(self):
        """初始化Jinja2环境"""
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self.templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
            autoescape=False,  # NC代码不需要转义
            undefined=jinja2.StrictUndefined  # 未定义变量报错
        )
        
        # 添加自定义过滤器
        self.jinja_env.filters['format_number'] = self._format_number
        self.jinja_env.filters['pad_zero'] = self._pad_zero
    
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
    
    def load_schemes(self) -> List[Scheme]:
        """加载所有方案"""
        schemes = []
        
        for yaml_file in self.schemes_dir.glob("*.yaml"):
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                
                # 解析模板列表
                templates = []
                for template_data in data.get('templates', []):
                    template = Template(
                        name=template_data['name'],
                        file=template_data['file'],
                        description=template_data.get('description', '')
                    )
                    templates.append(template)
                
                # 创建方案对象
                scheme = Scheme(
                    name=data['name'],
                    description=data.get('description', ''),
                    templates=templates,
                    parameters=data.get('parameters', {}),
                    defaults=data.get('defaults', {}),
                    file_path=yaml_file
                )
                schemes.append(scheme)
                
            except Exception as e:
                print(f"加载方案 {yaml_file} 失败: {e}")
                continue
        
        return schemes
    
    def render_template(self, scheme: Scheme, template: Template, params: Dict[str, Any]) -> RenderResult:
        """渲染模板"""
        try:
            template_path = template.get_path(self.templates_dir)
            
            if not template_path.exists():
                return RenderResult(
                    success=False,
                    error=f"模板文件不存在: {template_path}",
                    template_name=template.name
                )
            
            # 使用相对路径加载模板
            template_rel_path = str(template.file).replace("\\", "/")
            jinja_template = self.jinja_env.get_template(template_rel_path)
            
            # 渲染模板
            content = jinja_template.render(**params)
            
            return RenderResult(
                success=True,
                content=content,
                template_name=template.name
            )
            
        except jinja2.TemplateNotFound as e:
            return RenderResult(
                success=False,
                error=f"模板未找到: {e}",
                template_name=template.name
            )
        except jinja2.UndefinedError as e:
            return RenderResult(
                success=False,
                error=f"模板变量未定义: {e}",
                template_name=template.name
            )
        except Exception as e:
            return RenderResult(
                success=False,
                error=f"渲染错误: {e}",
                template_name=template.name
            )
    
    def validate_params(self, scheme: Scheme, params: Dict[str, Any]) -> Tuple[bool, Dict[str, str]]:
        """参数校验"""
        errors = {}
        
        # 遍历参数定义进行校验
        for group_name, group_params in scheme.parameters.items():
            for param_name, param_def in group_params.items():
                param_value = params.get(param_name)
                
                # 检查必填参数
                if param_def.get('required', True) and param_value is None:
                    errors[param_name] = f"{param_name} 是必填参数"
                    continue
                
                # 跳过空值的类型校验
                if param_value is None:
                    continue
                
                # 类型校验
                param_type = param_def.get('type', 'string')
                if param_type == 'number':
                    try:
                        float(param_value)
                    except (ValueError, TypeError):
                        errors[param_name] = f"{param_name} 必须是数字"
                        continue
                    
                    # 数值范围校验
                    value = float(param_value)
                    if 'min' in param_def and value < param_def['min']:
                        errors[param_name] = f"{param_name} 不能小于 {param_def['min']}"
                    if 'max' in param_def and value > param_def['max']:
                        errors[param_name] = f"{param_name} 不能大于 {param_def['max']}"
                
                elif param_type == 'string':
                    # 字符串长度校验
                    if isinstance(param_value, str):
                        if 'min_length' in param_def and len(param_value) < param_def['min_length']:
                            errors[param_name] = f"{param_name} 长度不能小于 {param_def['min_length']}"
                        if 'max_length' in param_def and len(param_value) > param_def['max_length']:
                            errors[param_name] = f"{param_name} 长度不能大于 {param_def['max_length']}"
        
        return len(errors) == 0, errors
    
    def get_template_variables(self, template: Template) -> List[str]:
        """扫描模板变量"""
        try:
            template_path = template.get_path(self.templates_dir)
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 匹配Jinja2变量 {{ variable_name }}
            variable_pattern = r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)(?:\.|\[|\(|\s|\}|$)"
            matches = re.findall(variable_pattern, content)
            
            return list(set(matches))
        except Exception as e:
            print(f"扫描模板变量失败: {e}")
            return []
