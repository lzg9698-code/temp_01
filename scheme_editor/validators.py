"""数据验证器

提供各种数据验证功能。
"""

from typing import List, Tuple, Any


class ValidationUtils:
    """验证工具类"""

    @staticmethod
    def validate_filename(filename: str) -> Tuple[bool, str]:
        """验证文件名"""
        if not filename.strip():
            return False, "文件名不能为空"

        # 检查非法字符
        illegal_chars = '<>:"/\\|?*'
        for char in illegal_chars:
            if char in filename:
                return False, f"文件名不能包含字符: {char}"

        # 检查扩展名
        valid_extensions = [".nc.j2", ".j2", ".jinja2"]
        if not any(filename.endswith(ext) for ext in valid_extensions):
            return False, "模板文件必须是.j2或.jinja2格式"

        return True, ""

    @staticmethod
    def validate_parameter_name(name: str) -> Tuple[bool, str]:
        """验证参数名"""
        if not name.strip():
            return False, "参数名不能为空"

        # 检查是否以字母或下划线开头
        if not name[0].isalpha() and name[0] != "_":
            return False, "参数名必须以字母或下划线开头"

        # 检查是否只包含字母、数字、下划线
        for char in name:
            if not (char.isalnum() or char == "_"):
                return False, "参数名只能包含字母、数字和下划线"

        return True, ""

    @staticmethod
    def validate_group_name(name: str) -> Tuple[bool, str]:
        """验证参数组名"""
        if not name.strip():
            return False, "参数组名不能为空"

        # 检查长度
        if len(name) > 20:
            return False, "参数组名不能超过20个字符"

        return True, ""

    @staticmethod
    def validate_scheme_name(name: str) -> Tuple[bool, str]:
        """验证方案名"""
        if not name.strip():
            return False, "方案名不能为空"

        # 检查长度
        if len(name) > 50:
            return False, "方案名不能超过50个字符"

        return True, ""

    @staticmethod
    def validate_range(
        value: Any, min_val: Any = None, max_val: Any = None
    ) -> Tuple[bool, str]:
        """验证数值范围"""
        try:
            num_value = float(value)

            if min_val is not None and num_value < float(min_val):
                return False, f"值不能小于 {min_val}"

            if max_val is not None and num_value > float(max_val):
                return False, f"值不能大于 {max_val}"

            return True, ""

        except (ValueError, TypeError):
            return False, "值必须是数字"

    @staticmethod
    def validate_required(value: Any, required: bool) -> Tuple[bool, str]:
        """验证必填字段"""
        if required and (value is None or str(value).strip() == ""):
            return False, "此字段为必填项"

        return True, ""

    @staticmethod
    def validate_select_options(value: Any, options: List[str]) -> Tuple[bool, str]:
        """验证选择项"""
        if not options:
            return False, "选项列表不能为空"

        if value not in options:
            return False, f"值必须是以下选项之一: {', '.join(options)}"

        return True, ""

    @staticmethod
    def validate_unique_names(
        names: List[str], name_type: str = "名称"
    ) -> Tuple[bool, str]:
        """验证名称唯一性"""
        if len(names) != len(set(names)):
            # 找出重复的名称
            duplicates = []
            seen = set()
            for name in names:
                if name in seen:
                    duplicates.append(name)
                seen.add(name)

            return False, f"存在重复的{name_type}: {', '.join(set(duplicates))}"

        return True, ""

    @staticmethod
    def validate_yaml_structure(data: Any) -> Tuple[bool, str]:
        """验证YAML结构"""
        if not isinstance(data, dict):
            return False, "YAML根节点必须是字典"

        # 检查必需字段
        if "name" not in data:
            return False, "缺少必需字段: name"

        # 检查templates字段
        if "templates" in data:
            templates = data["templates"]
            if not isinstance(templates, list):
                return False, "templates字段必须是列表"

            for i, template in enumerate(templates):
                if not isinstance(template, dict):
                    return False, f"templates[{i}] 必须是字典"

                required_template_fields = ["name", "file"]
                for field in required_template_fields:
                    if field not in template:
                        return False, f"templates[{i}] 缺少必需字段: {field}"

        # 检查parameters字段
        if "parameters" in data:
            parameters = data["parameters"]
            if not isinstance(parameters, dict):
                return False, "parameters字段必须是字典"

        return True, ""
