"""测试核心引擎功能"""

import sys
from pathlib import Path

# 将 src 目录添加到模块搜索路径
src_path = str(Path(__file__).parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from core import SimpleEngine

def test_engine():
    """测试引擎基本功能"""
    engine = SimpleEngine()
    
    print("=== 测试方案加载 ===")
    schemes = engine.load_schemes()
    print(f"找到 {len(schemes)} 个方案:")
    
    for solution in schemes:
        print(f"\n方案: {solution.name}")
        print(f"描述: {solution.description}")
        print(f"模板数量: {len(solution.templates)}")
        
        # 激活方案
        engine.activate_solution(solution.id)
        
        # 测试模板渲染
        if solution.templates:
            template = solution.templates[0]
            print(f"第一个模板: {template.name}")
            
            # 使用默认参数
            params = solution.get_default_params(engine.param_manager.library)
            print(f"默认参数: {params}")
            
            result = engine.render(template, params)
            if result.success:
                print(f"渲染成功，内容长度: {len(result.content)} 字符")
                print("渲染内容预览:")
                print("---")
                print(result.content[:200] + "..." if len(result.content) > 200 else result.content)
                print("---")
            else:
                print(f"渲染失败: {result.error}")

if __name__ == "__main__":
    test_engine()
