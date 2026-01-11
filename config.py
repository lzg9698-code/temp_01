"""配置管理 - 超简单"""

from pathlib import Path

class Config:
    """全局配置 - 无需配置文件"""
    
    # 目录路径
    ROOT = Path(__file__).parent
    SCHEMES_DIR = ROOT / "schemes"
    TEMPLATES_DIR = ROOT / "templates" 
    EXPORTS_DIR = ROOT / "exports"
    
    # UI配置
    WINDOW_WIDTH = 1200
    WINDOW_HEIGHT = 700
    WINDOW_TITLE = "NC代码生成器"
    
    # 支持的模板文件扩展名
    TEMPLATE_EXTENSIONS = ['.nc.j2', '.j2', '.jinja2']
    
    @classmethod
    def ensure_dirs(cls):
        """确保目录存在"""
        for dir_path in [cls.SCHEMES_DIR, cls.TEMPLATES_DIR, cls.EXPORTS_DIR]:
            dir_path.mkdir(exist_ok=True)

# 全局配置实例
config = Config()
config.ensure_dirs()
