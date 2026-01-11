"""方案管理器 - 负责扫描、列表和激活方案"""

import yaml
from pathlib import Path
from typing import List, Dict, Optional
from models import Solution, Template, Macro

class SolutionManager:
    """方案管理器"""

    def __init__(self, solutions_dir: Path):
        self.solutions_dir = solutions_dir
        self.solutions: Dict[str, Solution] = {}
        self.active_solution: Optional[Solution] = None

    def scan(self) -> List[Solution]:
        """扫描 solutions/ 目录下的所有方案"""
        self.solutions.clear()
        
        if not self.solutions_dir.exists():
            self.solutions_dir.mkdir(parents=True, exist_ok=True)
            return []

        for sol_dir in self.solutions_dir.iterdir():
            if not sol_dir.is_dir():
                continue

            scheme_file = sol_dir / "scheme.yaml"
            if not scheme_file.exists():
                continue

            try:
                with open(scheme_file, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)

                templates = []
                for t_data in data.get("templates", []):
                    templates.append(Template(
                        name=t_data["name"],
                        file=t_data["file"],
                        description=t_data.get("description", ""),
                        output_name=t_data.get("output_name", ""),
                        output_ext=t_data.get("output_ext", "nc")
                    ))

                macros = []
                for m_data in data.get("macros", []):
                    macros.append(Macro(
                        name=m_data["name"],
                        content=m_data["content"],
                        description=m_data.get("description", "")
                    ))

                sol_id = sol_dir.name
                solution = Solution(
                    id=sol_id,
                    name=data["name"],
                    description=data.get("description", ""),
                    version=data.get("version", "1.0.0"),  # 加载版本号
                    templates=templates,
                    path=sol_dir,
                    referenced_groups=data.get("referenced_groups", []),
                    defaults=data.get("defaults", {}),
                    config_file=sol_dir / "config.yaml",
                    macros=macros
                )
                self.solutions[sol_id] = solution
            except Exception as e:
                print(f"加载方案 {sol_dir.name} 失败: {e}")

        return list(self.solutions.values())

    def list_solutions(self) -> List[Solution]:
        """返回已扫描的方案列表"""
        return list(self.solutions.values())

    def activate(self, solution_id: str) -> Optional[Solution]:
        """激活指定方案"""
        if solution_id in self.solutions:
            self.active_solution = self.solutions[solution_id]
            return self.active_solution
        return None

    def get_active_solution(self) -> Optional[Solution]:
        """获取当前激活的方案"""
        return self.active_solution
