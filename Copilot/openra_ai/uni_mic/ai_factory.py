from enum import Enum
from .ai_implementations import *

class AIMode(Enum):
    DEEPSEEK = "deepseek"
    OPENAI_RESPONSE = "openai_response"
    OPENAI_REALTIME = "openai_realtime"
    OPENAI_NORMAL = "openai_normal"

class AIAssistantFactory:
    @staticmethod
    def create_assistant(mode: AIMode, config: StarterConfig, gui=None) -> BaseAIAssistant:
        if mode == AIMode.DEEPSEEK:
            return DeepseekAIAssistant(config, gui)
        elif mode == AIMode.OPENAI_RESPONSE:
            return OpenAIResponseAPIAssistant(config, gui)
        elif mode == AIMode.OPENAI_REALTIME:
            return OpenAIRealtimeAssistant(config, gui)
        elif mode == AIMode.OPENAI_NORMAL:
            return OpenAINormalAssistant(config, gui)
        else:
            raise ValueError(f"Unknown AI mode: {mode}") 