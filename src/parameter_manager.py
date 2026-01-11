"""参数管理器

负责管理全局参数库的加载、保存和操作。
采用单例模式确保全局唯一性。
"""

import yaml
import os
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import asdict

from models import (
    ParameterLibrary,
    GlobalParameterGroup,
    GlobalParameter,
    ParameterType,
)


class ParameterManager:
    """全局参数管理器（单例）"""

    _instance: Optional["ParameterManager"] = None
    _initialized: bool = False

    def __new__(cls) -> "ParameterManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._library: Optional[ParameterLibrary] = None
        self._config_dir: Optional[Path] = None
        self._parameters_file: Optional[Path] = None
        self._initialized = True

    @property
    def library(self) -> Optional[ParameterLibrary]:
        """获取参数库实例"""
        return self._library

    def initialize(self, config_dir: Path) -> bool:
        """初始化参数管理器

        Args:
            config_dir: 配置目录路径

        Returns:
            初始化是否成功
        """
        try:
            self._config_dir = config_dir
            self._parameters_file = config_dir / "parameters.yaml"

            # 确保配置目录存在
            self._config_dir.mkdir(parents=True, exist_ok=True)

            # 加载参数库
            return self.load_library()

        except Exception as e:
            print(f"参数管理器初始化失败: {e}")
            return False

    def load_library(self) -> bool:
        """加载参数库

        Returns:
            加载是否成功
        """
        try:
            if not self._parameters_file or not self._parameters_file.exists():
                # 如果文件不存在，创建默认的参数库
                self._library = ParameterLibrary()
                return self.save_library()

            with open(self._parameters_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data or "groups" not in data:
                raise ValueError("无效的参数库格式")

            self._library = self._library_from_dict(data)
            self._library.file_path = self._parameters_file

            # 验证加载的库
            is_valid, errors = self._library.validate()
            if not is_valid:
                print(f"参数库验证警告: {'; '.join(errors)}")

            return True

        except Exception as e:
            print(f"加载参数库失败: {e}")
            # 创建空的参数库
            self._library = ParameterLibrary()
            self._library.file_path = self._parameters_file
            return False

    def save_library(self) -> bool:
        """保存参数库

        Returns:
            保存是否成功
        """
        try:
            if not self._library or not self._parameters_file:
                return False

            # 验证库的有效性
            is_valid, errors = self._library.validate()
            if not is_valid:
                raise ValueError(f"参数库验证失败: {'; '.join(errors)}")

            # 备份现有文件
            if self._parameters_file.exists():
                backup_path = self._parameters_file.with_suffix(".yaml.backup")
                import shutil

                shutil.copy2(self._parameters_file, backup_path)

            # 保存新文件
            data = self._library.get_dict()
            with open(self._parameters_file, "w", encoding="utf-8") as f:
                yaml.dump(
                    data,
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                    indent=2,
                    sort_keys=False,
                )

            return True

        except Exception as e:
            print(f"保存参数库失败: {e}")
            return False

    def _library_from_dict(self, data: Dict[str, Any]) -> ParameterLibrary:
        """从字典创建参数库

        Args:
            data: YAML加载的数据

        Returns:
            参数库实例
        """
        library = ParameterLibrary()

        for group_name, group_data in data.get("groups", {}).items():
            group = GlobalParameterGroup(
                name=group_name, description=group_data.get("description", "")
            )

            for param_name, param_data in group_data.get("items", {}).items():
                param = GlobalParameter(
                    name=param_name,
                    type=self._parse_parameter_type(param_data.get("type", "string")),
                    default=param_data.get("default"),
                    min_value=param_data.get("min"),
                    max_value=param_data.get("max"),
                    unit=param_data.get("unit", ""),
                    description=param_data.get("description", ""),
                    required=param_data.get("required", True),
                    options=param_data.get("options", []),
                )
                group.add_parameter(param)

            library.add_group(group)

        return library

    def _parse_parameter_type(self, type_str: str) -> ParameterType:
        """解析参数类型字符串

        Args:
            type_str: 类型字符串

        Returns:
            参数类型枚举
        """
        type_map = {
            "string": ParameterType.STRING,
            "number": ParameterType.NUMBER,
            "integer": ParameterType.INTEGER,
            "boolean": ParameterType.BOOLEAN,
            "select": ParameterType.SELECT,
        }
        return type_map.get(type_str.lower(), ParameterType.STRING)

    def get_group_names(self) -> List[str]:
        """获取所有参数组名

        Returns:
            参数组名列表
        """
        if not self._library:
            return []
        return list(self._library.groups.keys())

    def load_solution_config(self, config_file: Path) -> Dict[str, Any]:
        """加载方案特定配置

        Args:
            config_file: 方案配置文件路径

        Returns:
            配置字典
        """
        try:
            if not config_file.exists():
                return {}

            with open(config_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            return data or {}
        except Exception as e:
            print(f"加载方案配置失败 {config_file}: {e}")
            return {}

    def get_group(self, name: str) -> Optional[GlobalParameterGroup]:
        """获取参数组

        Args:
            name: 参数组名

        Returns:
            参数组实例或None
        """
        if not self._library:
            return None
        return self._library.get_group(name)

    def get_parameter(self, name: str) -> Optional[GlobalParameter]:
        """跨组查找参数

        Args:
            name: 参数名

        Returns:
            参数实例或None
        """
        if not self._library:
            return None
        return self._library.get_parameter(name)

    def get_all_parameters(self) -> Dict[str, GlobalParameter]:
        """获取所有参数

        Returns:
            参数名到参数实例的映射
        """
        if not self._library:
            return {}
        return self._library.get_all_parameters()

    def add_group(self, group: GlobalParameterGroup) -> bool:
        """添加参数组

        Args:
            group: 参数组实例

        Returns:
            添加是否成功
        """
        if not self._library:
            return False

        try:
            self._library.add_group(group)
            return self.save_library()
        except ValueError as e:
            print(f"添加参数组失败: {e}")
            return False

    def remove_group(self, name: str) -> bool:
        """删除参数组

        Args:
            name: 参数组名

        Returns:
            删除是否成功
        """
        if not self._library:
            return False

        try:
            removed = self._library.remove_group(name)
            if removed:
                return self.save_library()
            return False
        except Exception as e:
            print(f"删除参数组失败: {e}")
            return False

    def add_parameter_to_group(self, group_name: str, param: GlobalParameter) -> bool:
        """向参数组添加参数

        Args:
            group_name: 参数组名
            param: 参数实例

        Returns:
            添加是否成功
        """
        if not self._library:
            return False

        group = self._library.get_group(group_name)
        if not group:
            print(f"参数组 '{group_name}' 不存在")
            return False

        try:
            group.add_parameter(param)
            return self.save_library()
        except ValueError as e:
            print(f"添加参数失败: {e}")
            return False

    def update_parameter_in_group(
        self, group_name: str, old_name: str, new_param: GlobalParameter
    ) -> bool:
        """更新参数组中的参数

        Args:
            group_name: 参数组名
            old_name: 旧参数名
            new_param: 新参数实例

        Returns:
            更新是否成功
        """
        if not self._library:
            return False

        group = self._library.get_group(group_name)
        if not group:
            print(f"参数组 '{group_name}' 不存在")
            return False

        try:
            if old_name in group.parameters:
                # 如果名称变了，先删除旧的
                if old_name != new_param.name:
                    if new_param.name in group.parameters:
                        print(f"参数名 '{new_param.name}' 已存在")
                        return False
                    group.remove_parameter(old_name)
                
                group.parameters[new_param.name] = new_param
                return self.save_library()
            return False
        except Exception as e:
            print(f"更新参数失败: {e}")
            return False

    def remove_parameter_from_group(self, group_name: str, param_name: str) -> bool:
        """从参数组删除参数

        Args:
            group_name: 参数组名
            param_name: 参数名

        Returns:
            删除是否成功
        """
        if not self._library:
            return False

        group = self._library.get_group(group_name)
        if not group:
            print(f"参数组 '{group_name}' 不存在")
            return False

        try:
            removed = group.remove_parameter(param_name)
            if removed:
                return self.save_library()
            return False
        except Exception as e:
            print(f"删除参数失败: {e}")
            return False

    def import_from_scheme(
        self, scheme_name: str, parameters: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """从方案导入参数

        Args:
            scheme_name: 方案名
            parameters: 方案参数定义

        Returns:
            (成功状态, 消息)
        """
        if not self._library:
            return False, "参数库未初始化"

        try:
            # 创建新参数组
            group_name = f"从 {scheme_name} 导入"
            group = GlobalParameterGroup(
                name=group_name, description=f"从方案 '{scheme_name}' 导入的参数"
            )

            # 转换参数格式
            param_count = 0
            for param_name, param_data in parameters.items():
                if isinstance(param_data, dict):
                    # 标准格式的参数定义
                    param = GlobalParameter(
                        name=param_name,
                        type=self._parse_parameter_type(
                            param_data.get("type", "string")
                        ),
                        default=param_data.get("default"),
                        min_value=param_data.get("min"),
                        max_value=param_data.get("max"),
                        unit=param_data.get("unit", ""),
                        description=param_data.get("description", ""),
                        required=param_data.get("required", True),
                        options=param_data.get("options", []),
                    )
                else:
                    # 简单值，当作string类型
                    param = GlobalParameter(
                        name=param_name,
                        type=ParameterType.STRING,
                        default=param_data,
                        description=f"从 {scheme_name} 导入的参数",
                    )

                group.add_parameter(param)
                param_count += 1

            # 添加到库中
            self._library.add_group(group)
            success = self.save_library()

            if success:
                return True, f"成功导入 {param_count} 个参数到组 '{group_name}'"
            else:
                return False, "保存参数库失败"

        except Exception as e:
            return False, f"导入参数失败: {e}"

    def export_group_to_dict(self, group_name: str) -> Optional[Dict[str, Any]]:
        """导出参数组为字典格式

        Args:
            group_name: 参数组名

        Returns:
            字典格式的参数组或None
        """
        if not self._library:
            return None

        group = self._library.get_group(group_name)
        if not group:
            return None

        return group.get_dict()

    def validate_library(self) -> Tuple[bool, List[str]]:
        """验证参数库

        Returns:
            (是否有效, 错误列表)
        """
        if not self._library:
            return False, ["参数库未初始化"]

        return self._library.validate()

    def get_library_info(self) -> Dict[str, Any]:
        """获取参数库信息

        Returns:
            包含统计信息的字典
        """
        if not self._library:
            return {}

        total_groups = len(self._library.groups)
        total_params = sum(
            len(group.parameters) for group in self._library.groups.values()
        )

        param_types = {}
        for group in self._library.groups.values():
            for param in group.parameters.values():
                type_name = param.type.value
                param_types[type_name] = param_types.get(type_name, 0) + 1

        return {
            "file_path": str(self._parameters_file) if self._parameters_file else None,
            "total_groups": total_groups,
            "total_parameters": total_params,
            "parameter_types": param_types,
            "group_names": self.get_group_names(),
        }

    def load_solution_config(self, config_file: Path) -> Dict[str, Any]:
        """加载方案特定的配置（defaults等）"""
        if not config_file.exists():
            return {}
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"加载方案配置失败: {e}")
            return {}


# 全局单例实例
_parameter_manager: Optional[ParameterManager] = None


def get_parameter_manager() -> ParameterManager:
    """获取单例实例"""
    return ParameterManager()
