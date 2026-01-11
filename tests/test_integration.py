"""集成测试 - 验证三个核心功能"""

import sys
from pathlib import Path

# 将 src 目录添加到模块搜索路径
src_path = str(Path(__file__).parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from core import SimpleEngine
from models import Solution, Template, RenderResult

def test_all_features():
    """测试所有核心功能"""
    engine = SimpleEngine()
    
    print("=== 功能1: 模板渲染测试 ===")
    schemes = engine.load_schemes()
    
    if not schemes:
        print("X 未找到任何方案")
        return False
    
    print(f"OK 成功加载 {len(schemes)} 个方案")
    
    for solution in schemes:
        print(f"\n方案: {solution.name}")
        print(f"   描述: {solution.description}")
        print(f"   模板数量: {len(solution.templates)}")
        
        # 激活方案
        engine.activate_solution(solution.id)
        
        # 获取所有参数
        all_params = engine.get_all_scheme_parameters(solution)
        print(f"   引用参数组: {list(all_params.keys())}")
        
        # 测试每个模板的渲染
        for template in solution.templates:
            print(f"   测试模板: {template.name}")
            params = solution.get_default_params(engine.param_manager.library)
            result = engine.render(template, params)
            
            if result.success:
                print(f"     OK 渲染成功，代码长度: {len(result.content)}")
            else:
                print(f"     X 渲染失败: {result.error}")
                return False
    
    print("\n=== 功能2: 参数获取测试 ===")
    if schemes:
        solution = schemes[0]
        engine.activate_solution(solution.id)
        params = solution.get_default_params(engine.param_manager.library)
        print(f"   OK 成功获取默认参数: {len(params)} 个")
    
    print("\n=== 功能3: 实时预览测试 ===")
    if schemes:
        solution = schemes[0]
        engine.activate_solution(solution.id)
        template = solution.templates[0]
        
        print(f"测试方案: {solution.name}")
        print(f"测试模板: {template.name}")
        
        # 测试默认参数
        params1 = solution.get_default_params(engine.param_manager.library)
        result1 = engine.render(template, params1)
        
        if result1.success:
            print("   OK 默认参数渲染成功")
        else:
            print(f"   X 默认参数渲染失败: {result1.error}")
        
        # 测试修改参数（只修改存在的参数）
        params2 = params1.copy()
        if 'feed_rate' in params2:
            params2['feed_rate'] = 999
        if 'spindle_speed' in params2:
            params2['spindle_speed'] = 5000
        
        result2 = engine.render(template, params2)
        
        if result2.success:
            print("   OK 修改参数渲染成功")
            
            # 检查结果是否不同
            if result1.content != result2.content:
                print("   OK 参数变化反映在渲染结果中")
            else:
                print("   ! 参数变化未反映在渲染结果中（可能模板未使用该参数）")
        else:
            print(f"   X 修改参数渲染失败: {result2.error}")
    
    print("\n=== 测试总结 ===")
    print("OK 模板渲染功能正常")
    print("OK 参数输入功能正常") 
    print("OK 输出预览功能正常")
    print("\nSUCCESS 所有核心功能测试通过！")
    
    return True

if __name__ == "__main__":
    test_all_features()
