# NC代码生成器 - 开发指南 (DEVELOPMENT.md)

## 项目概述
这是一个基于 Jinja2 模板的超轻量级 NC 代码生成工具，使用 PyQt6 构建 GUI 界面。项目采用模块化架构，旨在提供极简、高效、易扩展的 NC 编程辅助体验。

## 核心架构
项目采用 **MVC (Model-View-Controller)** 模式的变体：

- **Model (`models.py`)**: 定义了 `Solution`, `Template`, `Macro` 等核心数据类。
- **Controller/Engine**:
    - `core.py`: 核心引擎，协调各组件工作。
    - `solution_manager.py`: 负责方案的扫描、加载和生命周期管理。
    - `render_engine.py`: 封装 Jinja2 逻辑，处理模板渲染。
    - `parameter_manager.py`: 管理全局参数库和方案特定参数。
- **View (`ui.py`, `gui/`, `scheme_editor/`)**:
    - `ui.py`: 主界面框架。
    - `gui/param_manager.py`: 全局参数管理器。
    - `scheme_editor/`: 方案编辑器，支持可视化修改 `scheme.yaml`。

## 代码风格指南

### 1. 命名规范
- **类名**: `PascalCase` (如 `SolutionManager`, `MainWindow`)
- **函数/方法名**: `snake_case` (如 `load_solutions`, `render_template`)
- **变量名**: `snake_case` (如 `current_solution`, `param_name`)
- **常量**: `ALL_CAPS_WITH_UNDERSCORES` (如 `DEFAULT_CONFIG_PATH`)

### 2. 导入语句
按以下顺序组织导入：
1. 标准库 (`sys`, `pathlib`, `typing` 等)
2. 第三方库 (`yaml`, `jinja2`, `PyQt6` 等)
3. 本地模块 (`from core import ...`)

### 3. 类型注解
- 所有函数参数和返回值必须包含类型注解。
- 使用现代 Python 类型注解语法（如 `list[str]` 而非 `List[str]`，Python 3.10+）。

### 4. 文档字符串
- 使用简体中文编写类和方法的文档字符串。
- 说明功能、参数、返回值及可能的异常。

### 5. 错误处理
- 使用 `try-except` 块捕获潜在异常（如文件 I/O、YAML 解析、模板渲染错误）。
- 提供用户友好的错误提示，并在控制台记录详细日志。

## 开发工作流

### 1. 环境准备
```bash
pip install -r requirements.txt
```

### 2. 运行应用
```bash
python main.py
```

### 3. 测试验证
项目包含多个层级的测试脚本：
- `test_core.py`: 核心逻辑基础测试。
- `test_integration.py`: 完整业务流程集成测试（推荐）。
- `test_editor.py`: 方案编辑器功能测试。

### 4. 添加新功能
1. 在 `models.py` 中定义或扩展数据模型。
2. 在对应的管理器（如 `solution_manager.py`）中实现逻辑。
3. 在 `ui.py` 或相关 UI 组件中添加交互界面。
4. 编写或运行现有测试确保功能正确。

## 数据协议约定

### Solution (方案) 结构
方案存储在 `solutions/` 目录下，每个方案是一个子目录，包含：
- `scheme.yaml`: 方案定义文件。
- `*.nc.j2`: Jinja2 模板文件。

### scheme.yaml 示例
```yaml
name: "加工方案"
description: "方案描述"
referenced_groups: ["基础参数"]  # 引用全局参数组
templates:
  - name: "模板1"
    file: "t1.nc.j2"
defaults:
  param1: 100
macros:
  - name: "M_START"
    content: "M03 S1000"
```

## 性能与优化
- **延迟加载**: 方案和模板在需要时才进行深度解析。
- **实时渲染**: 参数变动时触发渲染，采用简单的防抖逻辑。
- **内存管理**: UI 组件在切换方案时及时清理，避免内存泄漏。

## 贡献指南
1. 遵循 PEP 8 代码规范。
2. 保持代码简洁，优先使用标准库。
3. 文档和注释使用简体中文。
4. 提交代码前确保通过所有集成测试。
