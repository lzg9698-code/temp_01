# NC代码生成器 - 极简版

基于Jinja2模板的超轻量级NC代码生成工具。

## 特点

- **零配置** - 开箱即用，无需数据库
- **三栏界面** - 方案选择 / 参数输入 / 输出预览
- **实时预览** - 参数变更即时刷新
- **语法高亮** - NC代码着色显示
- **极简架构** - 仅5个Python文件

## 安装

```bash
pip install -r requirements.txt
```

## 使用

```bash
python main.py
```

## 目录结构

```
nc-generator-simple/
├── main.py              # 启动入口
├── core.py              # 核心引擎
├── ui.py                # 用户界面
├── models.py            # 数据模型
├── config.py            # 配置管理
├── schemes/             # 方案配置（YAML）
├── templates/           # Jinja2模板
└── exports/             # 输出目录
```

## 添加新方案

1. 在 `schemes/` 目录创建YAML文件
2. 在 `templates/` 目录创建Jinja2模板
3. 重启应用即可加载

## 方案配置示例

```yaml
name: "车削加工"
description: "基础车削NC代码生成"
templates:
  - name: "外圆车削"
    file: "turning/outer_circle.nc.j2"
    description: "外圆车削循环"

parameters:
  基础设置:
    feed_rate:
      type: number
      default: 1200
      min: 100
      max: 5000
      unit: mm/min
      description: 进给速度

defaults:
  feed_rate: 1200
  spindle_speed: 2000
```
