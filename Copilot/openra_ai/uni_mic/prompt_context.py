from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime

@dataclass
class PlanItem:
    name: str
    status: str
    timestamp: float

@dataclass
class GameState:
    cash: int = 0
    resources: int = 0
    power: int = 0
    visible_units: List[Dict] = None
    start_time: float = 0
    memory: str = "无"
    plans: List[PlanItem] = field(default_factory=list)

class PromptContext:
    def __init__(self):
        self.game_state = GameState()
        self.config_data: Dict = {}
        self.sample_code: str = ""
        self.api_prompt_content: str = ""
        self.errors: List[Dict] = []  # 错误信息列表
        
    def add_error(self, error_info: dict):
        """添加错误信息到上下文"""
        self.errors.append(error_info)
        # 只保留最近的2个错误
        if len(self.errors) > 2:
            self.errors.pop(0) 