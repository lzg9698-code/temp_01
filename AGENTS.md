# AGENTS.md - NC代码生成器项目指南

## 项目概述

这是一个基于Jinja2模板的超轻量级NC代码生成工具，使用PyQt6构建GUI界面。项目采用极简架构设计，仅有5个核心Python文件。

## 构建和运行命令

### 安装依赖
```bash
pip install -r requirements.txt
```

### 运行应用
```bash
python main.py
```

### 测试命令
```bash
# 核心功能测试
python test_core.py

# 集成测试（推荐）
python test_integration.py
```

### 运行单个测试
项目没有使用unittest/pytest框架，测试通过直接执行Python文件运行。如需测试特定功能：
```bash
# 临时创建测试文件或修改现有测试文件，然后执行
python your_test_file.py
```

## 代码风格指南

### 1. 导入语句
- 使用标准Python导入风格
- 按标准库、第三方库、本地模块的顺序组织
- 避免使用通配符导入 `from module import *`

```python
# 标准库
import sys
import re
from pathlib import Path
from typing import List, Dict, Any

# 第三方库
import yaml
import jinja2
from PyQt6.QtWidgets import QApplication, QMainWindow

# 本地模块
from core import SimpleEngine
from models import Scheme, Template
```

### 2. 文件和目录结构
- 使用有意义的中文文件名（注释和文档）和英文变量名
- 每个文件职责单一：
  - `main.py`: 应用入口点
  - `core.py`: 核心业务逻辑
  - `ui.py`: 用户界面组件
  - `models.py`: 数据模型定义
  - `config.py`: 全局配置管理

### 3. 命名规范
- **类名**: PascalCase (如 `SimpleEngine`, `MainWindow`)
- **函数/方法名**: snake_case (如 `load_schemes`, `render_template`)
- **变量名**: snake_case (如 `current_scheme`, `template_path`)
- **常量**: UPPER_SNAKE_CASE (如 `SCHEMES_DIR`, `WINDOW_WIDTH`)

### 4. 文档字符串
- 使用简体中文编写文档字符串
- 类和方法都要有文档字符串
- 格式简洁明了：

```python
class SimpleEngine:
    """超简化NC代码生成引擎"""
    
    def render_template(self, scheme: Scheme, template: Template, params: Dict[str, Any]) -> RenderResult:
        """渲染模板
        Args:
            scheme: 加工方案
            template: 模板对象  
            params: 渲染参数
        Returns:
            RenderResult: 渲染结果
        """
```

### 5. 类型注解
- 所有函数参数和返回值都要有类型注解
- 使用现代类型注解语法：

```python
from typing import List, Dict, Any, Tuple, Optional

def load_schemes(self) -> List[Scheme]:
    """加载所有方案"""
    
def validate_params(self, scheme: Scheme, params: Dict[str, Any]) -> Tuple[bool, Dict[str, str]]:
    """参数校验"""
```

### 6. 错误处理
- 使用try-except块处理异常
- 提供有意义的错误信息
- 不要忽略异常：

```python
try:
    with open(yaml_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
except Exception as e:
    print(f"加载方案 {yaml_file} 失败: {e}")
    continue
```

### 7. UI代码规范
- 使用PyQt6现代语法
- 将大型UI类分解为逻辑组件
- 使用信号和槽机制进行组件通信

```python
# 现代类型注解
def __init__(self, parent=None):
    super().__init__(parent)
    self._templates: list[Template] = []
    self._current_template: Template | None = None

# 信号定义
template_changed = pyqtSignal(Template)
```

## 项目架构模式

### 1. MVC模式
- **Model**: `models.py` - 数据模型
- **View**: `ui.py` - 用户界面
- **Controller**: `core.py` - 业务逻辑

### 2. 配置管理
- 使用简单的类配置，无需外部配置文件
- 路径使用`pathlib.Path`进行跨平台兼容

### 3. 模板系统
- Jinja2环境配置：`trim_blocks=True`, `lstrip_blocks=True`
- 自定义过滤器：`format_number`, `pad_zero`
- 严格模式：未定义变量会报错

## 开发工作流

### 1. 添加新方案
1. 在`schemes/`目录创建YAML配置文件
2. 在`templates/`目录创建对应的Jinja2模板文件
3. 重启应用即可自动加载

### 2. 测试新功能
1. 修改或创建测试文件
2. 运行`python test_integration.py`验证所有功能
3. 运行`python test_core.py`进行基础功能测试

### 3. 代码审查要点
- 确保所有函数有类型注解
- 检查错误处理是否完善
- 验证UI组件是否正确清理资源
- 确认模板变量命名一致性

## 数据结构约定

### Scheme YAML结构
```yaml
name: "方案名称"
description: "方案描述"
templates:
  - name: "模板名称"
    file: "template/path.nc.j2"
    description: "模板描述"

parameters:
  分组名:
    参数名:
      type: number|string|int|bool|select
      default: 默认值
      min: 最小值  # number类型
      max: 最大值  # number类型
      unit: "单位"  # 可选
      description: "参数描述"

defaults:
  参数名: 默认值
```

### Jinja2模板约定
- 文件扩展名: `.nc.j2`
- 使用中文注释说明模板用途
- 变量名使用下划线分隔
- 利用自定义过滤器格式化输出

## 性能注意事项

1. **模板渲染**: 避免在模板中进行复杂计算
2. **UI响应**: 参数变更时实时预览，注意防抖
3. **文件操作**: 使用UTF-8编码处理所有文本文件
4. **内存管理**: UI组件使用后及时调用`deleteLater()`

## 调试技巧

1. **模板调试**: 检查`core.py`中的`get_template_variables`方法
2. **参数验证**: 使用`validate_params`方法检查参数有效性
3. **渲染错误**: 查看`RenderResult.error`字段获取详细错误信息
4. **UI调试**: 使用Qt Creator或查看控制台输出

## 部署说明

项目为纯Python应用，支持跨平台部署：
1. 确保目标机器安装Python 3.8+
2. 安装requirements.txt中的依赖
3. 直接运行`python main.py`
4. 可使用PyInstaller打包为独立可执行文件

## 贡献指南

1. 保持代码简洁，遵循现有架构模式
2. 新增功能需要对应添加测试
3. 文档和注释使用简体中文
4. 遵循PEP 8代码规范
5. 确保类型注解完整准确