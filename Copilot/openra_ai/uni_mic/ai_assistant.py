from abc import ABC, abstractmethod
from typing import Optional
from .config import StarterConfig
from .gui import AIAssistantUI

class BaseAIAssistant(ABC):
    def __init__(self, config: StarterConfig, gui: Optional[AIAssistantUI] = None):
        self.config = config
        self.gui = gui
        self.memory = "无"
        
    @abstractmethod
    async def process_command(self, prompt: str) -> str:
        """处理用户命令的抽象方法"""
        pass
    
    def update_memory(self, new_memory: str):
        self.memory = new_memory
        if self.gui:
            self.gui.set_memory_content(new_memory)
            
    def execute_command(self, code: str, plan=None):
        try:
            exec(code)
            if self.gui and plan:
                self.gui.update_plan_item_status(plan, "已完成")
        except Exception as e:
            if self.gui and plan:
                self.gui.update_plan_item_status(plan, "失败")
                self.gui.add_ai_dialog(f"错误信息：{str(e)}", False)
            raise e 