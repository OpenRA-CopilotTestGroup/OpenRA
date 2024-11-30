# asr_module.py
from abc import ABC, abstractmethod
from typing import Union, Dict, Any
import os
from .utils import get_logger

class ASRModule(ABC):
    @abstractmethod
    def transcribe(self, audio_data: bytes) -> Union[str, Dict[str, Any]]:
        """
        Transcribe the given audio data to text.
        
        Args:
            audio_data (bytes): Raw audio data in bytes format
            
        Returns:
            Union[str, Dict[str, Any]]: Transcription result either as plain text
                                      or structured data
        """
        pass


# asr_whisper.py
class WhisperASR(ASRModule):
    
    def __init__(self, **kwargs):
        
        self.language = "zh"
        self.model = "large-v3"
        self.device = "mps"
        self.prompt = None
        self.prefix = None
        self.initial_prompt = "以下是普通话的句子。"
        if self.prefix:
            self.initial_prompt += self.prefix
        
        self.audio_model = None
        self.remote = False
        self.faster = False
        self.logger = get_logger("whisper_asr","info")
    
    def transcribe(self, audio_data):
        predicted_text = ''
        self.logger.debug("Transcribing audio...")
        if self.remote:
            pass
        elif self.faster:
            pass
        else:
            import whisper
            # current path
            #model_root = os.path.join(os.path.dirname(__file__), "models")
            model_root = os.path.expanduser("~/.cache/whisper")
            self.audio_model = whisper.load_model(
                self.model,
                download_root=model_root,
                device=self.device,
                #compute_type = "int8"
            )
            result = self.audio_model.transcribe(
                audio_data,
                language=self.language,
                suppress_tokens="",
                prefix=self.prefix,
                initial_prompt=self.initial_prompt,
                prompt=self.prompt
            )
            self.logger.debug(f"Transcription result: {result}")
            predicted_text = result["text"]
        predicted_text = predicted_text.strip()
        if predicted_text:
            return predicted_text

# asr_funasr.py
class FunASR(ASRModule):
    
    def __init__(self):
        pass
    
    def transcribe(self, audio_data):
        result = ...
        return result