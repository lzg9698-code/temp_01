"""数据模型 - 极简设计"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class ParameterType(Enum):
    """参数类型枚举"""

    STRING = "string"
    NUMBER = "number"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    SELECT = "select"


@dataclass
class GlobalParameter:
    """全局参数定义"""

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
        if (value is None or value == "") and self.required:
            return False, f"{self.name} 是必填参数"

        if value is None:
            return True, ""

        # 类型验证
        try:
            if self.type == ParameterType.NUMBER:
                float_value = float(value)
                # 范围验证
                if self.min_value is not None and float_value < self.min_value:
                    return False, f"{self.name} 不能小于 {self.min_value}"
                if self.max_value is not None and float_value > self.max_value:
                    return False, f"{self.name} 不能大于 {self.max_value}"
            elif self.type == ParameterType.INTEGER:
                int_value = int(value)
                # 范围验证
                if self.min_value is not None and int_value < self.min_value:
                    return False, f"{self.name} 不能小于 {self.min_value}"
                if self.max_value is not None and int_value > self.max_value:
                    return False, f"{self.name} 不能大于 {self.max_value}"
            elif self.type == ParameterType.SELECT:
                # Handle both simple list and structured options
                valid_values = []
                for opt in self.options:
                    if isinstance(opt, dict) and "value" in opt:
                        valid_values.append(str(opt["value"]))
                    else:
                        valid_values.append(str(opt))
                        
                if str(value) not in valid_values:
                    return (
                        False,
                        f"{self.name} 必须是以下选项之一: {', '.join(valid_values)}",
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
class GlobalParameterGroup:
    """全局参数组"""

    name: str
    description: str = ""
    parameters: Dict[str, GlobalParameter] = field(default_factory=dict)

    def add_parameter(self, param: GlobalParameter) -> None:
        """添加参数"""
        if param.name in self.parameters:
            raise ValueError(f"参数名 '{param.name}' 在组 '{self.name}' 中已存在")
        self.parameters[param.name] = param

    def remove_parameter(self, name: str) -> bool:
        """删除参数"""
        if name in self.parameters:
            del self.parameters[name]
            return True
        return False

    def get_parameter(self, name: str) -> Optional[GlobalParameter]:
        """获取参数"""
        return self.parameters.get(name)

    def get_dict(self) -> Dict[str, Any]:
        """转换为字典格式，用于YAML序列化"""
        result: Dict[str, Any] = {
            "description": self.description,
            "items": {
                name: param.get_dict() for name, param in self.parameters.items()
            },
        }
        return result

    def validate(self) -> tuple[bool, str]:
        """验证参数组的有效性"""
        if not self.name.strip():
            return False, "参数组名不能为空"

        # 验证每个参数
        for param in self.parameters.values():
            is_valid, error = param.validate_value(param.default)
            if not is_valid:
                return False, f"参数 '{param.name}' 默认值无效: {error}"

        return True, ""


@dataclass
class ParameterLibrary:
    """全局参数库"""

    groups: Dict[str, GlobalParameterGroup] = field(default_factory=dict)
    file_path: Optional[Path] = field(default=None)

    def add_group(self, group: GlobalParameterGroup) -> None:
        """添加参数组"""
        if group.name in self.groups:
            raise ValueError(f"参数组名 '{group.name}' 已存在")
        self.groups[group.name] = group

    def remove_group(self, name: str) -> bool:
        """删除参数组"""
        if name in self.groups:
            del self.groups[name]
            return True
        return False

    def get_group(self, name: str) -> Optional[GlobalParameterGroup]:
        """获取参数组"""
        return self.groups.get(name)

    def get_all_parameters(self) -> Dict[str, GlobalParameter]:
        """获取所有参数（跨组）"""
        all_params = {}
        for group in self.groups.values():
            all_params.update(group.parameters)
        return all_params

    def get_parameter(self, name: str) -> Optional[GlobalParameter]:
        """跨组查找参数"""
        for group in self.groups.values():
            if name in group.parameters:
                return group.parameters[name]
        return None

    def get_group_names(self) -> List[str]:
        """获取所有参数组名"""
        return list(self.groups.keys())

    def get_dict(self) -> Dict[str, Any]:
        """转换为字典格式，用于YAML序列化"""
        result: Dict[str, Any] = {
            "groups": {name: group.get_dict() for name, group in self.groups.items()}
        }
        return result

    def validate(self) -> tuple[bool, List[str]]:
        """验证整个参数库"""
        errors = []

        # 检查参数组名是否重复
        group_names = list(self.groups.keys())
        if len(group_names) != len(set(group_names)):
            errors.append("存在重复的参数组名")

        # 验证每个参数组
        for group in self.groups.values():
            is_valid, error = group.validate()
            if not is_valid:
                errors.append(f"参数组 '{group.name}': {error}")

        # 检查跨组参数名冲突
        all_param_names = []
        for group in self.groups.values():
            all_param_names.extend(group.parameters.keys())

        if len(all_param_names) != len(set(all_param_names)):
            errors.append("不同参数组中存在重复的参数名")

        return len(errors) == 0, errors


@dataclass
class Template:
    """模板定义"""

    name: str
    file: str
    description: str = ""
    output_name: str = ""  # 默认输出文件名（不含后缀）
    output_ext: str = "nc"  # 默认输出后缀名

    def get_path(self, base_dir: Path) -> Path:
        """获取模板文件完整路径"""
        return base_dir / self.file


@dataclass
class Macro:
    """宏定义 - 用于代码片段复用"""

    name: str
    content: str
    description: str = ""


@dataclass
class Solution:
    """方案配置"""

    id: str
    name: str
    description: str
    templates: List[Template]
    path: Path  # 方案根路径
    version: str = "1.0.0"  # 方案版本
    referenced_groups: List[str] = field(default_factory=list)
    defaults: Dict[str, Any] = field(default_factory=dict)
    config_file: Optional[Path] = field(default=None)
    macros: List[Macro] = field(default_factory=list)

    def get_default_params(
        self, parameter_library: Optional["ParameterLibrary"] = None
    ) -> Dict[str, Any]:
        """获取默认参数"""
        if parameter_library is None:
            return self.defaults.copy()

        result = {}
        for group_name in self.referenced_groups:
            group = parameter_library.get_group(group_name)
            if group:
                for param in group.parameters.values():
                    if param.default is not None:
                        result[param.name] = param.default

        result.update(self.defaults)
        return result

    def get_effective_parameters(
        self, parameter_library: Optional["ParameterLibrary"] = None
    ) -> Dict[str, GlobalParameter]:
        """获取有效参数定义"""
        if parameter_library is None:
            return {}

        result = {}
        for group_name in self.referenced_groups:
            group = parameter_library.get_group(group_name)
            if group:
                result.update(group.parameters)
        return result

    def add_referenced_group(self, group_name: str) -> None:
        """添加引用的参数组"""
        if group_name not in self.referenced_groups:
            self.referenced_groups.append(group_name)

    def remove_referenced_group(self, group_name: str) -> bool:
        """移除引用的参数组"""
        if group_name in self.referenced_groups:
            self.referenced_groups.remove(group_name)
            return True
        return False

    def validate(
        self, parameter_library: Optional["ParameterLibrary"] = None
    ) -> tuple[bool, List[str]]:
        """验证方案配置"""
        errors = []

        if not self.name.strip():
            errors.append("方案名称不能为空")

        template_names = [t.name for t in self.templates]
        if len(template_names) != len(set(template_names)):
            errors.append("存在重复的模板名")

        if parameter_library:
            available_groups = parameter_library.get_group_names()
            for group_name in self.referenced_groups:
                if group_name not in available_groups:
                    errors.append(f"引用的参数组 '{group_name}' 不存在")
        
        return len(errors) == 0, errors


@dataclass
class RenderResult:
    """渲染结果"""

    success: bool
    content: str = ""
    error: str = ""
    template_name: str = ""
