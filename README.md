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
├── templates/           # 模板包目录
│   ├── turning/         # 车削模板包
│   │   ├── scheme.yaml  # 方案配置
│   │   ├── outer_circle.nc.j2
│   │   ├── face.nc.j2
│   │   └── groove.nc.j2
│   ├── milling/         # 铣削模板包
│   │   ├── scheme.yaml  # 方案配置
│   │   ├── face_mill.nc.j2
│   │   ├── contour.nc.j2
│   │   └── drill.nc.j2
│   └── drilling/        # 钻孔模板包
│       ├── scheme.yaml  # 方案配置
│       ├── simple_drill.nc.j2
│       ├── deep_drill.j2
│       └── ream.nc.j2
└── exports/             # 输出目录
```

## 添加新方案

1. 在 `templates/` 目录创建新的子目录（如 `new_process/`）
2. 在子目录中创建 `scheme.yaml` 配置文件
3. 在同一目录中创建对应的 `.nc.j2` 模板文件
4. 重启应用即可自动加载

### 方案配置示例

```yaml
name: "新加工工艺"
description: "新的NC代码生成工艺"

templates:
  - name: "工艺名称"
    file: "template_file.nc.j2"
    description: "工艺描述"

parameters:
  参数组名:
    参数名:
      type: number|string|int|bool|select
      default: 默认值
      min: 最小值  # number类型
      max: 最大值  # number类型
      description: "参数描述"

defaults:
  参数名: 默认值
```

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
