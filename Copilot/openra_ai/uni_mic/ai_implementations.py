from openai import OpenAI
import dashscope
from .ai_assistant import BaseAIAssistant
import os

class DeepseekAIAssistant(BaseAIAssistant):
    def __init__(self, config, gui=None):
        super().__init__(config, gui)
        self.client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com"
        )
        
    async def process_command(self, prompt: str) -> str:
        # Deepseek的具体实现
        response = self.client.chat.completions.create(
            model=self.config.gptmodel,
            messages=[
                {"role": "system", "content": self.get_system_prompt()},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content

class OpenAIResponseAPIAssistant(BaseAIAssistant):
    def __init__(self, config, gui=None):
        super().__init__(config, gui)
        self.client = OpenAI()
        self.last_response_id = None
        
    async def process_command(self, prompt: str) -> str:
        response = self.client.responses.create(
            model=self.config.gptmodel,
            input=prompt,
            instructions=self.get_system_prompt(),
            previous_response_id=self.last_response_id,
        )
        self.last_response_id = response.id
        return response.output[0].content[0].text

class OpenAIRealtimeAssistant(BaseAIAssistant):
    def __init__(self, config, gui=None):
        super().__init__(config, gui)
        self.client = OpenAI()
        
    async def process_command(self, prompt: str) -> str:
        # 实时流式处理的实现
        stream = await self.client.chat.completions.create(
            model=self.config.gptmodel,
            messages=[
                {"role": "system", "content": self.get_system_prompt()},
                {"role": "user", "content": prompt}
            ],
            stream=True
        )
        
        full_response = ""
        for chunk in stream:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_response += content
                if self.gui:
                    self.gui.add_ai_dialog(content, False)
        return full_response 