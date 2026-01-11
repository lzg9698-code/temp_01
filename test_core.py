"""测试核心引擎功能"""

from core import SimpleEngine

def test_engine():
    """测试引擎基本功能"""
    engine = SimpleEngine()
    
    print("=== 测试方案加载 ===")
    schemes = engine.load_schemes()
    print(f"找到 {len(schemes)} 个方案:")
    
    for scheme in schemes:
        print(f"\n方案: {scheme.name}")
        print(f"描述: {scheme.description}")
        print(f"模板数量: {len(scheme.templates)}")
        print(f"参数组: {list(scheme.parameters.keys())}")
        
        # 测试模板渲染
        if scheme.templates:
            template = scheme.templates[0]
            print(f"第一个模板: {template.name}")
            
            # 使用默认参数
            params = scheme.get_default_params()
            print(f"默认参数: {params}")
            
            result = engine.render_template(scheme, template, params)
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
