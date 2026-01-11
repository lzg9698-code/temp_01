# NC代码生成器 - 使用指南

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 运行应用
```bash
python main.py
```

### 3. 基本使用流程
1. **选择方案** - 从左侧选择加工类型（车削/铣削/钻孔）
2. **配置参数** - 在中间面板输入加工参数
3. **选择模板** - 在右侧选择具体的加工模板
4. **实时预览** - 查看生成的NC代码
5. **导出文件** - 点击"导出NC文件"保存代码

## 内置方案

### 🚗 车削加工
- **外圆车削** - 工件外径车削循环
- **端面车削** - 工件端面车削加工
- **切槽** - 切槽加工

**主要参数**：
- 进给速度、主轴转速、刀具号
- 毛坯直径、最终直径、工件长度
- 切削深度、精加工余量

### 🔧 铣削加工  
- **平面铣削** - 表面平面铣削
- **轮廓铣削** - 工件轮廓铣削
- **钻孔** - 铣刀钻孔加工

**主要参数**：
- 进给速度、主轴转速、刀具直径
- 工件尺寸（长×宽×高）
- 切削深度、步距、安全高度

### 🕳️ 钻孔加工
- **简单钻孔** - 标准钻孔循环
- **深孔钻孔** - 啄式钻孔循环
- **铰孔** - 精密铰孔加工

**主要参数**：
- 钻孔进给、转速、退刀速度
- 钻头直径、孔深、啄钻深度
- 孔位坐标、工件高度

## 高级功能

### 语法高亮
- G代码：绿色粗体
- M代码：蓝色粗体  
- 坐标：紫色
- 数字：红色
- 注释：灰色斜体

### 参数校验
- 数值范围检查
- 必填参数验证
- 类型匹配验证
- 实时错误提示

### 文件导出
- 自动生成带时间戳的文件名
- 格式：`{方案名}_{时间戳}.nc`
- 导出到 `exports/` 目录

## 添加自定义方案

### 1. 创建方案配置文件
在 `schemes/` 目录创建YAML文件，例如 `schemes/custom.yaml`：

```yaml
name: "自定义加工"
description: "我的自定义加工方案"

templates:
  - name: "自定义模板"
    file: "custom/template.nc.j2"
    description: "自定义模板描述"

parameters:
  参数组名:
    参数名:
      type: number|string|boolean|select
      default: 默认值
      min: 最小值    # 数字类型
      max: 最大值    # 数字类型
      unit: 单位
      description: 参数描述
      options: [选项1, 选项2]  # 选择类型

defaults:
  参数名: 默认值
```

### 2. 创建Jinja2模板文件
在 `templates/` 目录创建模板文件，例如 `templates/custom/template.nc.j2`：

```jinja2
{# 模板注释 #}
; 程序开始
N10 G90 G54 G21
N20 T{{ tool_number }}01 M6
N30 M03 S{{ spindle_speed }}

; 自定义加工逻辑
N40 G00 X{{ x_position }} Y{{ y_position }}
N50 G01 Z{{ depth }} F{{ feed_rate }}

N60 M30
```

### 3. 重启应用
重启应用即可加载新方案。

## Jinja2模板语法

### 基本变量
```jinja2
X{{ x_position }}Y{{ y_position }}    ; 简单变量
S{{ spindle_speed | format_number(0) }}  ; 格式化数字
```

### 条件判断
```jinja2
{% if use_coolant %}
M08  ; 冷却液开
{% endif %}
```

### 循环
```jinja2
{% set passes = (total_depth / cut_depth) | round(0, 'ceil') | int %}
{% for i in range(passes) %}
N{{ 100 + i*10 }} G01 Z{{ (i+1) * cut_depth }}
{% endfor %}
```

### 过滤器
- `format_number(n)` - 格式化数字，保留n位小数
- `pad_zero(width)` - 数字补零到指定位数
- `upper|lower` - 字符串大小写转换

## 故障排除

### 常见问题

**Q: 启动时出现模块导入错误**
```bash
ModuleNotFoundError: No module named 'PyQt6'
```
A: 安装依赖：`pip install -r requirements.txt`

**Q: 模板渲染失败**
```
模板变量未定义: 'some_var'
```
A: 检查模板中的变量名是否与方案参数名一致

**Q: 参数校验失败**
```
参数不能大于 1000
```
A: 检查参数值是否在方案定义的范围内

**Q: 导出文件权限错误**
```
PermissionError: [Errno 13] Permission denied
```
A: 确保对 `exports/` 目录有写权限

### 调试技巧

1. **查看参数定义**：检查 `schemes/*.yaml` 文件
2. **验证模板语法**：检查 `templates/**/*.nc.j2` 文件  
3. **测试渲染**：使用 `test_core.py` 验证模板渲染
4. **查看日志**：控制台输出包含详细错误信息

## 性能优化

- 大型模板避免过多嵌套循环
- 合理设置参数校验范围
- 模板文件使用UTF-8编码
- 避免模板中复杂的数学运算

## 扩展开发

### 添加新的参数类型
在 `ui.py` 的 `ParamWidget._create_param_widget()` 方法中添加新的控件逻辑。

### 添加新的过滤器  
在 `core.py` 的 `_init_jinja_env()` 方法中注册新的Jinja2过滤器。

### 自定义语法高亮
在 `ui.py` 的 `NCHighlighter` 类中添加新的语法规则。
