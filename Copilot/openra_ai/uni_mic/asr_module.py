# asr_module.py
from abc import ABC, abstractmethod

class ASRModule(ABC):
    @abstractmethod
    def transcribe(self, audio_data):
        """Transcribe the given audio_data and return the results"""
        pass


# asr_whisper.py
class WhisperASR(ASRModule):
    
    def __init__(self):
        pass
    
    def transcribe(self, audio_data):
        result = ...
        return result

# asr_funasr.py
class FunASR(ASRModule):
    
    def __init__(self):
        pass
    
    def transcribe(self, audio_data):
        result = ...
        return result