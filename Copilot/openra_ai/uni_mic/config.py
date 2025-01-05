from dataclasses import dataclass, field, fields
from typing import Optional
import json
import click


@dataclass
class ASRConfig:
    model: str = "large"
    device: str = "mps"
    language: str = "zh"
    initial_prompt: str = "以下是中文的普通话句子。"
    remote_asr: bool = False
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
    no_sample: bool = True
    no_text_callback: bool = False

@dataclass
class AppConfig:
    asr: 'ASRConfig' = field(default_factory=lambda: ASRConfig())
    input: 'InputConfig' = field(default_factory=lambda: InputConfig())
    starter: 'StarterConfig' = field(default_factory=lambda: StarterConfig())
    
    # following classmethods are not used by now
    @classmethod
    def from_dict(cls, config_dict: dict) -> 'AppConfig':
        asr_config = ASRConfig(**{k: v for k, v in config_dict.items()
                                if hasattr(ASRConfig, k)})
        input_config = InputConfig(**{k: v for k, v in config_dict.items()
                                    if hasattr(InputConfig, k)})

        main_config_keys = {'verbose', 'logging_level', 'gui'}
        main_config = {k: config_dict[k] for k in main_config_keys
                      if k in config_dict}

        return cls(
            asr=asr_config,
            input=input_config,
            **main_config
        )

    @classmethod
    def from_json(cls, json_file: str) -> 'AppConfig':
        with open(json_file, 'r', encoding='utf-8') as f:
            config_dict = json.load(f)
        return cls.from_dict(config_dict)

    def to_dict(self) -> dict:
        return {
            **vars(self.asr),
            **vars(self.input),
            **vars(self.starter)
        }

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