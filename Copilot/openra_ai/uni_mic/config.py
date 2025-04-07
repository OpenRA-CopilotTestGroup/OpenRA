from dataclasses import dataclass, field, fields
import click


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
    ai_mode: str = "openai_normal"
    no_sample: bool = False
    single_sample: bool = False
    no_text_callback: bool = False
    no_prompt: bool = False
    debug_mode: bool = False
    use_response_api: bool = False


@dataclass
class AppConfig:
    asr: 'ASRConfig' = field(default_factory=lambda: ASRConfig())
    input: 'InputConfig' = field(default_factory=lambda: InputConfig())
    starter: 'StarterConfig' = field(default_factory=lambda: StarterConfig())

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

    def __new__(cls, config=None):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance.config = config
        return cls._instance

    @classmethod
    def set_config(cls, config):
        if cls._instance is None:
            cls._instance = cls()
        cls._instance.config = config

    @classmethod
    def get_config(cls):
        if cls._instance is None or cls._instance.config is None:
            raise ValueError("ConfigManager 未初始化，请先调用 set_config() 设置 config")
        return cls._instance.config
