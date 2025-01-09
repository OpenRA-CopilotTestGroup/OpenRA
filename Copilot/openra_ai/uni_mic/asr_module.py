# asr_module.py
from abc import ABC, abstractmethod
from typing import Union, Dict, Any
import os
import requests
import numpy as np
import time
import tempfile
from openai import OpenAI
from .utils import get_logger
from .config import ASRConfig

def load_whisper():
    import importlib
    whisper = importlib.import_module("whisper")
    return whisper

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

    def __init__(self, config: ASRConfig = ASRConfig()):
        self.language = config.language
        self.model = config.model
        self.device = config.device
        self.initial_prompt = config.initial_prompt
        self.audio_model = None
        self.logger = get_logger("whisper_asr", "info")

    def transcribe(self, audio_data: np.ndarray):
        predicted_text = ''
        self.logger.info(f"Transcribing audio with {self.device} and {self.model}...")
        try:
            whisper = load_whisper()
            #import whisper
            # current path
            # model_root = os.path.join(os.path.dirname(__file__), "models")
            model_root = os.path.expanduser("~/.cache/whisper")
            self.audio_model = whisper.load_model(
                self.model,
                download_root=model_root,
                device=self.device,
                in_memory=True
            )
            result = self.audio_model.transcribe(
                audio_data,
                language=self.language,
                initial_prompt=self.initial_prompt
            )
            self.logger.info(f"Transcription result: {result}")
            predicted_text = result["text"]
            predicted_text = predicted_text.strip()
            if predicted_text:
                return predicted_text
        except ImportError:
            self.logger.error("Whisper not found. Please install whisper.")
            return predicted_text
        
# asr_funasr.py
class FunASRRemoteASR(ASRModule):

    def __init__(self, config: ASRConfig = ASRConfig()):
        self.server_url = config.remote_asr_url
        # self.server_url = "http://localhost:5000/transcribe"
        self.logger = get_logger("fun_asr", "info")
        self.logger.info("FunASR Init with url: " + self.server_url)

    def transcribe(self, audio_data: np.ndarray):
        try:
            start_time = time.time()
            audio_bytes = audio_data.tobytes()
            self.logger.info(
                f"FunASRRemoteASR -> Sent audio data: {len(audio_bytes)} bytes")
            response = requests.post(self.server_url,
                                     data=audio_bytes,
                                     proxies={"http": None, "https": None},
                                     timeout=10)

            elapsed_time = time.time() - start_time
            self.logger.info(
                f"FunaASRRemoteASR -> Total time taken: {elapsed_time:.2f} seconds")
            self.logger.info(
                f"FunASRRemoteASR -> Transcribing audio with FunASR...")
            if response.status_code == 200:
                result = response.json()
                return result.get("text", "")
            else:
                with open("debug_audio.wav", "wb") as f:
                    f.write(audio_bytes)

                self.logger.error(
                    f"FunASRRemoteASR -> Error: Server returned status code {response.status_code}")
                self.logger.error(
                    f"FunASRRemoteASR -> Response content: {response.text}")
                print(response)
        except Exception as e:
            self.logger.error(f"FunASRRemoteASR -> Error: {e}")
            return ""

class WhisperAPIASR(ASRModule):
    def __init__(self, config: ASRConfig = ASRConfig()):
        self.api_key = config.api_key
        self.model = "whisper-1"
        self.response_format = "text"
        self.logger = get_logger("whisper_api_asr", "info")

        if not self.api_key:
            self.logger.error("WhisperAPIASR -> API KEY not configured")
            raise ValueError("WhisperAPIASR -> API KEY not configured")

        try:
            self.client = OpenAI(api_key=self.api_key)
            self.logger.info("WhisperAPIASR -> Initialized")
        except Exception as e:
            self.logger.error(f"WhisperAPIASR -> Error: {e}")
            raise ValueError("WhisperAPIASR -> Error initializing Whisper API")

    def transcribe(self, audio_data: np.ndarray):
        try:
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=True) as temp_audio:
                temp_audio.write(audio_data.tobytes())
                temp_audio.flush()

                self.logger.info(f"WhisperAPIASR -> Transcribing audio with {self.model}...")

                transcription = self.client.audio.transcriptions.create(
                    model=self.model,
                    file=temp_audio,
                    response_format=self.response_format,
                )

            return transcription.text
        except Exception as e:
            self.logger.error(f"WhisperAPIASR -> Error: {e}")
            return ""