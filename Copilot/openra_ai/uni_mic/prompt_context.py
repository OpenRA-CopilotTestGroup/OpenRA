from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime

@dataclass
class GameState:
    cash: int = 0
    resources: int = 0
    power: int = 0
    visible_units: List[Dict] = None
    start_time: float = 0
    memory: str = "无"

class PromptContext:
    def __init__(self):
        self.game_state = GameState()
        self.config_data: Dict = {}
        self.sample_code: str = ""
        self.api_prompt_content: str = "" 