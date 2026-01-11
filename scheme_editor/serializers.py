"""方案YAML序列化器

负责YAML格式与EditableScheme对象之间的转换，包括格式验证。
"""

import yaml
from typing import Dict, Any, List, Tuple, Optional

from .models import (
    EditableScheme,
    TemplateDef,
    ParameterDef,
    ParameterGroup,
    ParameterType,
)


class SchemeSerializer:
    """方案序列化器"""

    @staticmethod
    def from_scheme(scheme) -> EditableScheme:
        """从现有Scheme对象创建EditableScheme"""
        editable_scheme = EditableScheme(
            name=scheme.name,
            description=scheme.description,
            file_path=str(scheme.file_path) if scheme.file_path else None,
        )

        # 转换模板
        for template in scheme.templates:
            template_def = TemplateDef(
                name=template.name, file=template.file, description=template.description
            )
            editable_scheme.add_template(template_def)

        # 转换参数组和参数
        for group_name, group_params in scheme.parameters.items():
            param_group = ParameterGroup(name=group_name)

            for param_name, param_def in group_params.items():
                # 解析参数类型
                param_type_str = param_def.get("type", "string")
                param_type = ParameterType(param_type_str)

                # 创建参数定义
                param = ParameterDef(
                    name=param_name,
                    type=param_type,
                    default=param_def.get("default"),
                    min_value=param_def.get("min"),
                    max_value=param_def.get("max"),
                    unit=param_def.get("unit", ""),
                    description=param_def.get("description", ""),
                    required=param_def.get("required", True),
                    options=param_def.get("options", []),
                )

                param_group.add_parameter(param)

            editable_scheme.add_parameter_group(param_group)

        return editable_scheme

    @staticmethod
    def from_yaml(yaml_content: str) -> EditableScheme:
        """从YAML内容解析为EditableScheme"""
        try:
            data = yaml.safe_load(yaml_content)
            if not data or not isinstance(data, dict):
                raise ValueError("YAML内容格式无效")

            return SchemeSerializer._parse_scheme_data(data)

        except yaml.YAMLError as e:
            raise ValueError(f"YAML解析错误: {e}")
        except Exception as e:
            raise ValueError(f"解析失败: {e}")

    @staticmethod
    def from_yaml_file(file_path: str) -> EditableScheme:
        """从YAML文件解析为EditableScheme"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                yaml_content = f.read()

            scheme = SchemeSerializer.from_yaml(yaml_content)
            scheme.file_path = file_path
            return scheme

        except FileNotFoundError:
            raise ValueError(f"文件不存在: {file_path}")
        except Exception as e:
            raise ValueError(f"读取文件失败: {e}")

    @staticmethod
    def to_yaml(scheme: EditableScheme) -> str:
        """将EditableScheme序列化为YAML"""
        try:
            data = scheme.get_dict()
            yaml_content = yaml.dump(
                data,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
                indent=2,
            )
            return yaml_content

        except Exception as e:
            raise ValueError(f"序列化失败: {e}")

    @staticmethod
    def to_yaml_file(scheme: EditableScheme, file_path: str) -> None:
        """将EditableScheme保存到YAML文件"""
        try:
            yaml_content = SchemeSerializer.to_yaml(scheme)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(yaml_content)

        except Exception as e:
            raise ValueError(f"保存文件失败: {e}")

    @staticmethod
    def validate_yaml(yaml_content: str) -> Tuple[bool, str]:
        """验证YAML格式的有效性"""
        try:
            data = yaml.safe_load(yaml_content)
            if not data or not isinstance(data, dict):
                return False, "YAML内容必须包含字典结构"

            # 验证必需字段
            if "name" not in data:
                return False, "缺少必需字段: name"

            # 尝试解析为方案对象
            try:
                scheme = SchemeSerializer._parse_scheme_data(data)
                is_valid, errors = scheme.validate()

                if not is_valid:
                    return False, "方案验证失败:\n" + "\n".join(
                        f"- {error}" for error in errors
                    )

                return True, "格式有效"

            except Exception as e:
                return False, f"数据结构无效: {e}"

        except yaml.YAMLError as e:
            return False, f"YAML语法错误: {e}"
        except Exception as e:
            return False, f"验证失败: {e}"

    @staticmethod
    def _parse_scheme_data(data: Dict[str, Any]) -> EditableScheme:
        """解析方案数据"""
        # 基本信息
        scheme = EditableScheme(
            name=data.get("name", ""), description=data.get("description", "")
        )

        # 解析模板
        templates_data = data.get("templates", [])
        if templates_data:
            for template_data in templates_data:
                if isinstance(template_data, dict):
                    template = TemplateDef(
                        name=template_data.get("name", ""),
                        file=template_data.get("file", ""),
                        description=template_data.get("description", ""),
                    )
                    scheme.add_template(template)

        # 解析参数组
        parameters_data = data.get("parameters", {})
        if parameters_data:
            for group_name, group_params in parameters_data.items():
                if isinstance(group_params, dict):
                    param_group = ParameterGroup(name=group_name)

                    for param_name, param_def in group_params.items():
                        if isinstance(param_def, dict):
                            # 解析参数类型
                            param_type_str = param_def.get("type", "string")
                            try:
                                param_type = ParameterType(param_type_str)
                            except ValueError:
                                param_type = ParameterType.STRING

                            # 创建参数定义
                            param = ParameterDef(
                                name=param_name,
                                type=param_type,
                                default=param_def.get("default"),
                                min_value=param_def.get("min"),
                                max_value=param_def.get("max"),
                                unit=param_def.get("unit", ""),
                                description=param_def.get("description", ""),
                                required=param_def.get("required", True),
                                options=param_def.get("options", []),
                            )

                            param_group.add_parameter(param)

                    scheme.add_parameter_group(param_group)

        return scheme

    @staticmethod
    def get_yaml_template() -> str:
        """获取YAML模板"""
        template = """name: "新加工方案"
description: "请输入方案描述"

templates:
  - name: "示例模板"
    file: "example_template.nc.j2"
    description: "示例模板描述"

parameters:
  基础设置:
    example_param:
      type: number
      default: 100
      min: 0
      max: 1000
      unit: "单位"
      description: "参数描述"

defaults:
  example_param: 100
"""
        return template
