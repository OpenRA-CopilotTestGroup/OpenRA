from dataclasses import dataclass
from typing import Optional
import json


@dataclass
class ASRConfig:
    model: str = "large"
    device: str = "mps"
    language: str = "zh"
    faster: bool = False
    remote: bool = True
    initial_prompt: str = "以下是普通话的句子。"
    enable_post_processing: bool = False
    post_prompt: Optional[str] = None
    hallucinate_threshold: int = 400
    phrase_time_limit: int = 10


@dataclass
class InputConfig:
    input_mode: str = "mic"
    energy: int = 300
    dynamic_energy: bool = False
    pause: float = 1.2
    mic_index: Optional[int] = None
    save_file: bool = False
    list_devices: bool = False


@dataclass
class TextProcessingConfig:
    prompt: Optional[str] = None
    prefix: Optional[str] = None
    ignore_text_without_prefix: bool = False
    remove_prefix: bool = False


@dataclass
class AppConfig:
    asr: ASRConfig = ASRConfig()
    input: InputConfig = InputConfig()
    text_processing: TextProcessingConfig = TextProcessingConfig()
    gptmodel: str = "gpt-4o"
    verbose: bool = False
    logging_level: str = "info"
    gui: bool = True

    @classmethod
    def from_dict(cls, config_dict: dict) -> 'AppConfig':
        asr_config = ASRConfig(**{k: v for k, v in config_dict.items() 
                                if hasattr(ASRConfig, k)})
        input_config = InputConfig(**{k: v for k, v in config_dict.items() 
                                    if hasattr(InputConfig, k)})
        text_processing_config = TextProcessingConfig(**{k: v for k, v in config_dict.items() 
                                                       if hasattr(TextProcessingConfig, k)})
        
        main_config_keys = {'gptmodel', 'verbose', 'logging_level', 'gui'}
        main_config = {k: config_dict[k] for k in main_config_keys 
                      if k in config_dict}
        
        return cls(
            asr=asr_config,
            input=input_config,
            text_processing=text_processing_config,
            **main_config
        )

    @classmethod
    def from_json(cls, json_file: str) -> 'AppConfig':
        with open(json_file, 'r') as f:
            config_dict = json.load(f)
        return cls.from_dict(config_dict)

    def to_dict(self) -> dict:
        return {
            **vars(self.asr),
            **vars(self.input),
            **vars(self.text_processing),
            'gptmodel': self.gptmodel,
            'verbose': self.verbose,
            'logging_level': self.logging_level,
            'gui': self.gui
        }
