from abc import ABC, abstractmethod
from dataclasses import asdict
from typing import Dict, Any
from openai import OpenAI
import re
import OpenRA_Copilot_Library as OpenRA
from OpenRA_Copilot_Library import *
import os
from .config import ConfigManager,base_path
from concurrent.futures import ThreadPoolExecutor
from .log_manager import LogManager
from .prompt_manager import PromptManager
from .prompt_context import PromptContext, PlanItem
import time
import yaml
import traceback
import threading
from .utils import parse_response, CODE_REGEX, SPEECH_REGEX, TITLE_REGEX, MEMORY_REGEX

# 全局配置
MAX_OUTPUT_TOKENS = 3000

logger = LogManager.get_logger()
api = GameAPI(host="localhost")

class BaseAIAssistant(ABC):
    def __init__(self):
        self.config = ConfigManager.get_config().starter
        self.client = self._create_client()
        self.prompt_manager = PromptManager()
        self.context = PromptContext()
        self.current_input = ""
        self._init_context()
        self._load_noise_keywords()
        self.api = OpenRA.GameAPI("localhost")
        self.executor = ThreadPoolExecutor(max_workers=10)

    def _init_context(self):
        # 初始化配置数据
        self._load_game_config()
        self._load_api_prompt()
        self._load_sample_code()
        self.context.game_state.start_time = time.perf_counter()

    def _load_game_config(self):
        config_path = os.path.join(base_path, 'config.yaml')
        with open(config_path, 'r', encoding='utf-8') as f:
            self.context.config_data = yaml.safe_load(f)

    def _load_api_prompt(self):
        api_prompt_path = os.path.join(base_path, 'OpenRA_Promt.py')
        with open(api_prompt_path, 'r', encoding='utf-8') as f:
            self.context.api_prompt_content = f.read()

    def _load_sample_code(self):
        if not self.config.no_sample:
            if self.config.single_sample:
                sample_path = os.path.join(base_path, 'Sample.py')
                with open(sample_path, 'r', encoding='utf-8') as f:
                    self.context.sample_code = f.read()
            else:
                # 加载多个样例代码的逻辑
                sample_dir = os.path.join(base_path, 'samples')
                self.context.sample_code = ""
                if os.path.exists(sample_dir):
                    for sample_file in os.listdir(sample_dir):
                        if sample_file.endswith('.py'):
                            sample_path = os.path.join(sample_dir, sample_file)
                            with open(sample_path, 'r', encoding='utf-8') as f:
                                self.context.sample_code += f"# {sample_file}\n"
                                self.context.sample_code += f.read() + "\n\n"
                pass

    def update_game_state(self, api):
        """更新游戏状态"""
        player_info = api.player_base_info_query()
        self.context.game_state.cash = player_info.Cash
        self.context.game_state.resources = player_info.Resources
        self.context.game_state.power = player_info.Power
        
        visible_units = api.query_actor(
            TargetsQueryParam(
                type=[],
                faction=["任意"],
                range="screen",
                restrain=[{"visible": True}]
            )
        )
        self.context.game_state.visible_units = [
            {
                "actor_id": unit.actor_id,
                "faction": unit.faction,
                "type": unit.type,
                "position": {"x": unit.position.x, "y": unit.position.y}
            }
            for unit in visible_units
            if unit.faction != "中立"
        ]

    def update_memory(self, memory: str):
        """更新记忆"""
        self.context.game_state.memory = memory

    def _load_noise_keywords(self):
        noise_path = os.path.join(base_path, 'noise_keywords.yaml')
        with open(noise_path, 'r', encoding='utf-8') as f:
            self.noise_keywords = yaml.safe_load(f)['noise_keywords']

    @abstractmethod
    def _create_client(self):
        pass

    @abstractmethod
    def generate_response(self) -> str:
        pass
    
    def handle_strategy_command(self, user_input=None, gui=None):
        """处理策略命令"""
        try:
            # 更新计划状态到上下文
            if gui:
                self.context.game_state.plans = [
                    PlanItem(
                        name=plan['name'],
                        status=plan['status'],
                        timestamp=plan['timestamp']
                    )
                    for plan in gui.get_all_plans()
                ]

            # 检查语音底噪
            if user_input and any(keyword in user_input for keyword in self.noise_keywords):
                logger.warning(f"检测到语音底噪，忽略指令: {user_input}")
                print(f"检测到语音底噪，忽略指令: {user_input}")
                return

            # 设置当前输入
            self.current_input = user_input if user_input else ""
            
            # 生成响应
            response = self.generate_response()
            
            if gui and self.current_input != "":
                gui.add_player_dialog(self.current_input)
            
            # 解析响应内容
            code = CODE_REGEX.search(response)
            speech = SPEECH_REGEX.search(response)
            title = TITLE_REGEX.search(response)
            memory = MEMORY_REGEX.search(response)
            # 更新GUI显示
            if gui:
                if speech:
                    gui.add_ai_dialog(speech.group(1))
                if title:
                    plan = gui.add_plan_item(
                        plan_name=title.group(1), status="进行中")
                
            # 执行代码
            if code:
                executable = code.group(1)
                # 移除代码开头的import语句
                executable = re.sub(
                    r'^(import .*?\n|from .*? import .*?\n)*', '', executable.strip())
                logger.info(f"可执行代码: {executable}")
                def execute(command):
                    try:
                        if callable(command):
                            command()
                        else:
                            exec(command)
                        if gui and plan:
                            gui.update_plan_item_status(plan, "已完成")
                    except Exception as e:
                        logger.error(f"执行代码出错: {str(e)}")
                        traceback.print_exc()
                        if gui and plan:
                            gui.update_plan_item_status(plan, "失败")
                            error_message = traceback.format_exception_only(type(e), e)
                            last_line = "".join(error_message).strip()
                            gui.add_ai_dialog(f"错误信息：{last_line}", False)
                            
                            # 添加错误信息到上下文
                            error_info = {
                                'timestamp': time.perf_counter() - self.context.game_state.start_time,
                                'command': self.current_input,
                                'error': last_line,
                                'code': executable
                            }
                            self.context.add_error(error_info)

                # 在线程池中执行代码
                future = self.executor.submit(execute, executable)
            if memory:
                self.update_memory(memory.group(1))
                if gui:
                    gui.set_memory_content(memory.group(1))

        except Exception as e:
            logger.error(f"处理策略命令时出错: {str(e)}")
            if gui:
                gui.add_ai_dialog(f"执行出错: {str(e)}", False)

class OpenAIAssistant(BaseAIAssistant):
    def _create_client(self):
        logger.debug("Initializing OpenAI client")
        return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def generate_response(self) -> str:
        self.update_game_state(self.api)
        static_prompt, dynamic_prompt = self.prompt_manager.get_prompts(self.context)
        messages = [
            {"role": "system", "content": static_prompt + dynamic_prompt},
            {"role": "user", "content": self.current_input}
        ]
        
        try:
            completion = self.client.chat.completions.create(
                model=self.config.gptmodel,
                messages=messages,
                max_tokens=MAX_OUTPUT_TOKENS,
                temperature=1.0
            )
            return completion.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise

class DeepseekAIAssistant(OpenAIAssistant):
    def _create_client(self):
        logger.debug("Initializing Deepseek client")
        return OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com"
        )

class OpenAIResponseAIAssistant(BaseAIAssistant):
    def __init__(self):
        super().__init__()
        self.last_response_id = None
    
    def _create_client(self):
        logger.debug("Initializing OpenAI Response client")
        return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
    def generate_response(self) -> str:
        self.update_game_state(self.api)
        static_prompt, dynamic_prompt = self.prompt_manager.get_prompts(self.context)
        
        # 根据配置决定使用哪种 prompt
        if self.config.use_simplest_prompt and self.last_response_id:
            instructions = self.prompt_manager.get_simplest_prompt() + dynamic_prompt
        else:
            instructions = static_prompt + dynamic_prompt

        response = self.client.responses.create(
            model=self.config.gptmodel,
            input=self.current_input,
            instructions=instructions,
            previous_response_id=self.last_response_id,
            max_output_tokens=MAX_OUTPUT_TOKENS,
            temperature=1.0,
        )
        
        self.last_response_id = response.id
        logger.debug(f"OpenAI Response API response received: {response}")
        return response.output[0].content[0].text

class OpenAIRealtimeAIAssistant(BaseAIAssistant):
    def __init__(self):
        super().__init__()
        self.last_response_id = None
        self.ws_client = None  # WebSocket客户端实例
    
    def _create_client(self):
        logger.debug("Initializing OpenAI Realtime client")
        return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
    def generate_response(self) -> str:
        self.update_game_state(self.api)
        static_prompt, dynamic_prompt = self.prompt_manager.get_prompts(self.context)
        
        # 首先使用OpenAI提取玩家指令的意图
        messages = [
            {"role": "system", "content": "你是一个OpenRA游戏的指令提取助手。请从玩家的自然语言中提取出关键的游戏指令，或者对于游戏的指挥，命令等行为，复述即可，忽略对话内容，。如果没有识别到有效指令，输出 没有指令"},
            {"role": "user", "content": self.current_input}
        ]
        
        try:
            completion = self.client.chat.completions.create(
                model=self.config.gptmodel,
                messages=messages,
                max_tokens=MAX_OUTPUT_TOKENS,
                temperature=0.7
            )
            extracted_command = completion.choices[0].message.content
            logger.debug(f"OpenAI Realtime API response received: {extracted_command}")
            
            if "没有" in extracted_command:
                self.current_input = ""
                return ""
            
            self.current_input = extracted_command.strip()
            
            static_prompt, dynamic_prompt = self.prompt_manager.get_prompts(self.context)
            
            # 根据配置决定使用哪种 prompt
            if self.config.use_simplest_prompt and self.last_response_id:
                instructions = self.prompt_manager.get_simplest_prompt() + dynamic_prompt
            else:
                instructions = static_prompt + dynamic_prompt
                
            # 使用Response API生成具体执行代码
            response = self.client.responses.create(
                model=self.config.gptmodel,
                input=self.current_input,
                instructions=instructions,
                previous_response_id=self.last_response_id,
                max_output_tokens=MAX_OUTPUT_TOKENS,
                temperature=1.0
            )
            
            self.last_response_id = response.id
            logger.debug(f"OpenAI Response API response received: {response}")
            return response.output[0].content[0].text
            
        except Exception as e:
            logger.error(f"OpenAI API error in realtime mode: {str(e)}")
            raise

class AIAssistantFactory:
    @staticmethod
    def create_assistant(config) -> BaseAIAssistant:
        if "deepseek" in config.starter.gptmodel:
            return DeepseekAIAssistant()
        elif config.starter.openai_response_mode:
            return OpenAIResponseAIAssistant()
        elif config.starter.openai_realtime_mode:
            return OpenAIRealtimeAIAssistant()
        else:
            return OpenAIAssistant()