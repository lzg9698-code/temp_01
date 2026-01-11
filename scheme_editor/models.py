"""方案编辑器数据模型

定义编辑器专用的数据结构，支持可视化编辑和验证。
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum


class ParameterType(Enum):
    """参数类型枚举"""

    STRING = "string"
    NUMBER = "number"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    SELECT = "select"


@dataclass
class ParameterDef:
    """参数定义"""

    name: str
    type: ParameterType
    default: Any = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    unit: str = ""
    description: str = ""
    required: bool = True
    options: List[str] = field(default_factory=list)

    def validate_value(self, value: Any) -> tuple[bool, str]:
        """验证参数值的有效性"""
        if not value and self.required:
            return False, f"{self.name} 是必填参数"

        if value is None:
            return True, ""

        # 类型验证
        try:
            if self.type == ParameterType.NUMBER:
                float(value)
                # 范围验证
                float_value = float(value)
                if self.min_value is not None and float_value < self.min_value:
                    return False, f"{self.name} 不能小于 {self.min_value}"
                if self.max_value is not None and float_value > self.max_value:
                    return False, f"{self.name} 不能大于 {self.max_value}"
            elif self.type == ParameterType.INTEGER:
                int(value)
                # 范围验证
                int_value = int(value)
                if self.min_value is not None and int_value < self.min_value:
                    return False, f"{self.name} 不能小于 {self.min_value}"
                if self.max_value is not None and int_value > self.max_value:
                    return False, f"{self.name} 不能大于 {self.max_value}"
            elif self.type == ParameterType.SELECT:
                if value not in self.options:
                    return (
                        False,
                        f"{self.name} 必须是以下选项之一: {', '.join(self.options)}",
                    )
        except (ValueError, TypeError) as e:
            return False, f"{self.name} 类型错误: {e}"

        return True, ""

    def get_dict(self) -> Dict[str, Any]:
        """转换为字典格式，用于YAML序列化"""
        result: Dict[str, Any] = {
            "type": self.type.value,
            "description": self.description,
        }

        if self.default is not None:
            result["default"] = self.default

        if self.min_value is not None:
            result["min"] = self.min_value

        if self.max_value is not None:
            result["max"] = self.max_value

        if self.unit:
            result["unit"] = self.unit

        if self.options:
            result["options"] = self.options

        if not self.required:
            result["required"] = False

        return result


@dataclass
class TemplateDef:
    """模板定义"""

    name: str
    file: str
    description: str = ""

    def get_dict(self) -> Dict[str, Any]:
        """转换为字典格式，用于YAML序列化"""
        result: Dict[str, Any] = {
            "name": self.name,
            "file": self.file,
            "description": self.description,
        }
        return result

    def validate(self) -> tuple[bool, str]:
        """验证模板定义的有效性"""
        if not self.name.strip():
            return False, "模板名称不能为空"

        if not self.file.strip():
            return False, "模板文件不能为空"

        # 检查文件扩展名
        if not self.file.endswith((".nc.j2", ".j2", ".jinja2")):
            return False, "模板文件必须是.j2或.jinja2格式"

        return True, ""


@dataclass
class ParameterGroup:
    """参数组"""

    name: str
    parameters: List[ParameterDef] = field(default_factory=list)

    def add_parameter(self, param: ParameterDef) -> None:
        """添加参数"""
        # 检查参数名是否重复
        if any(p.name == param.name for p in self.parameters):
            raise ValueError(f"参数名 '{param.name}' 已存在")
        self.parameters.append(param)

    def remove_parameter(self, name: str) -> bool:
        """删除参数"""
        for i, param in enumerate(self.parameters):
            if param.name == name:
                del self.parameters[i]
                return True
        return False

    def get_dict(self) -> Dict[str, Dict[str, Any]]:
        """转换为字典格式，用于YAML序列化"""
        result: Dict[str, Dict[str, Any]] = {}
        for param in self.parameters:
            result[param.name] = param.get_dict()
        return result

    def validate(self) -> tuple[bool, str]:
        """验证参数组的有效性"""
        if not self.name.strip():
            return False, "参数组名不能为空"

        # 检查参数名是否重复
        names = [p.name for p in self.parameters]
        if len(names) != len(set(names)):
            return False, "参数组中存在重复的参数名"

        # 验证每个参数
        for param in self.parameters:
            is_valid, error = param.validate_value(param.default)
            if not is_valid:
                return False, f"参数 '{param.name}' 默认值无效: {error}"

        return True, ""


@dataclass
class EditableScheme:
    """可编辑的方案"""

    name: str
    description: str = ""
    templates: List[TemplateDef] = field(default_factory=list)
    parameter_groups: List[ParameterGroup] = field(default_factory=list)
    file_path: Optional[str] = None

    def add_template(self, template: TemplateDef) -> None:
        """添加模板"""
        # 检查模板名是否重复
        if any(t.name == template.name for t in self.templates):
            raise ValueError(f"模板名 '{template.name}' 已存在")
        self.templates.append(template)

    def remove_template(self, name: str) -> bool:
        """删除模板"""
        for i, template in enumerate(self.templates):
            if template.name == name:
                del self.templates[i]
                return True
        return False

    def add_parameter_group(self, group: ParameterGroup) -> None:
        """添加参数组"""
        # 检查参数组名是否重复
        if any(g.name == group.name for g in self.parameter_groups):
            raise ValueError(f"参数组名 '{group.name}' 已存在")
        self.parameter_groups.append(group)

    def remove_parameter_group(self, name: str) -> bool:
        """删除参数组"""
        for i, group in enumerate(self.parameter_groups):
            if group.name == name:
                del self.parameter_groups[i]
                return True
        return False

    def get_dict(self) -> Dict[str, Any]:
        """转换为字典格式，用于YAML序列化"""
        result: Dict[str, Any] = {
            "name": self.name,
            "description": self.description,
            "templates": [t.get_dict() for t in self.templates],
            "parameters": {g.name: g.get_dict() for g in self.parameter_groups},
        }

        # 添加默认值
        defaults: Dict[str, Any] = {}
        for group in self.parameter_groups:
            for param in group.parameters:
                if param.default is not None:
                    defaults[param.name] = param.default

        if defaults:
            result["defaults"] = defaults

        return result

    def validate(self) -> tuple[bool, List[str]]:
        """验证方案的有效性"""
        errors = []

        # 验证方案名称
        if not self.name.strip():
            errors.append("方案名称不能为空")

        # 验证模板
        template_names = [t.name for t in self.templates]
        if len(template_names) != len(set(template_names)):
            errors.append("存在重复的模板名")

        for template in self.templates:
            is_valid, error = template.validate()
            if not is_valid:
                errors.append(f"模板 '{template.name}': {error}")

        # 验证参数组
        group_names = [g.name for g in self.parameter_groups]
        if len(group_names) != len(set(group_names)):
            errors.append("存在重复的参数组名")

        for group in self.parameter_groups:
            is_valid, error = group.validate()
            if not is_valid:
                errors.append(f"参数组 '{group.name}': {error}")

        # 检查跨组参数名冲突
        all_param_names = []
        for group in self.parameter_groups:
            for param in group.parameters:
                all_param_names.append(param.name)

        if len(all_param_names) != len(set(all_param_names)):
            errors.append("不同参数组中存在重复的参数名")

        return len(errors) == 0, errors
