from dataclasses import dataclass, field, fields
import click
import os
import sys


@dataclass
class ASRConfig:
    model: str = "base"
    device: str = "cpu"
    language: str = "zh"
    initial_prompt: str = "以下是中文的普通话句子。"
    api_key: str = None
    remote_asr: bool = False
    remote_type: str = "funasr"
    remote_asr_url: str = "http://digisky.ananthe.party:5286/transcribe"
    hallucinate_threshold: int = 400
    phrase_time_limit: int = 10


@dataclass
class InputConfig:
    input_mode: str = "mic"
    energy: int = 300
    dynamic_energy: bool = False
    pause: float = 1.2
    #mic_index: int = None
    save_file: bool = False
    #list_devices: bool = False

@dataclass
class StarterConfig:
    gui: bool = True
    logging_level: str = "info"
    verbose: bool = False
    gptmodel: str = "gpt-4o"
    gptmodel_pre: str = "gpt-4o-mini"
    no_sample: bool = False
    single_sample: bool = False
    no_text_callback: bool = False
    no_prompt: bool = False
    debug_mode: bool = False
    openai_response_mode: bool = False
    openai_realtime_mode: bool = False
    use_simplest_prompt: bool = False
    retry_when_failed: bool = True
    max_retry_times: int = 1


@dataclass
class TTSConfig:
    tts_engine: str = "edge"  # edge, cosyvoice, minimax
    edge_voice: str = "zh-CN-XiaoxiaoNeural"  # edge tts voice
    cosyvoice_model: str = "cosyvoice-v1"
    cosyvoice_voice: str = "longxiaoxia"
    minimax_voice: str = "female-shaonv"
    tts_volume: float = 1.0
    tts_rate: int = 150
    tts_retry_times: int = 3
    tts_fallback_to_edge: bool = True


@dataclass
class AppConfig:
    asr: 'ASRConfig' = field(default_factory=lambda: ASRConfig())
    input: 'InputConfig' = field(default_factory=lambda: InputConfig())
    starter: 'StarterConfig' = field(default_factory=lambda: StarterConfig())
    tts: 'TTSConfig' = field(default_factory=lambda: TTSConfig())

def add_options(dataclass_type):
    def decorator(f):
        for field in reversed(fields(dataclass_type)):
            option_name = f"--{field.name.replace('_', '-')}"
            default = field.default if field.default != field.default_factory else None
            field_type = field.type
            is_flag = field_type == bool
            f = click.option(
                option_name,
                default=default,
                help=field.metadata.get("help", ""),
                is_flag=is_flag,
                type=None if is_flag else field_type,
            )(f)
        return f
    return decorator

class ConfigManager:
    _instance = None
    _default_config = AppConfig(
        asr=ASRConfig(),
        input=InputConfig(),
        starter=StarterConfig(),
        tts=TTSConfig()
    )

    def __new__(cls, config=None):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance.config = config if config is not None else cls._default_config
        return cls._instance

    @classmethod
    def set_config(cls, config):
        if cls._instance is None:
            cls._instance = cls()
        cls._instance.config = config

    @classmethod
    def get_config(cls):
        if cls._instance is None:
            # 如果实例不存在，创建一个带有默认配置的实例
            cls._instance = cls()
        if cls._instance.config is None:
            # 如果配置为空，使用默认配置
            cls._instance.config = cls._default_config
        return cls._instance.config

    @classmethod
    def reset_to_default(cls):
        """重置为默认配置"""
        if cls._instance is not None:
            cls._instance.config = cls._default_config

if hasattr(sys, '_MEIPASS'):
    base_path = os.getcwd()
else:
    base_path = os.path.dirname(os.path.dirname(__file__))
    
base_path = os.path.join(base_path, 'configs')
