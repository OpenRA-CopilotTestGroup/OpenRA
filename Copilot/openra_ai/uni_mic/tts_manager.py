from abc import ABC, abstractmethod
import asyncio
import edge_tts
import dashscope
from dashscope.audio.tts_v2 import *
import os
import tempfile
import uuid
import queue
import threading
from playsound import playsound
from typing import Optional
import requests
from .log_manager import LogManager
from .config import ConfigManager
import traceback

logger = LogManager.get_logger()

class BaseTTSEngine(ABC):
    @abstractmethod
    async def synthesize(self, text: str) -> str:
        """合成语音，返回音频文件路径"""
        pass

class EdgeTTSEngine(BaseTTSEngine):
    def __init__(self, voice: str):
        self.voice = voice

    async def synthesize(self, text: str) -> str:
        filename = f"tts_edge_{uuid.uuid4().hex}.mp3"
        path = os.path.join(tempfile.gettempdir(), filename)
        
        tts = edge_tts.Communicate(text, voice=self.voice)
        await tts.save(path)
        return path

class CosyVoiceTTSEngine(BaseTTSEngine):
    def __init__(self, model: str, voice: str):
        self.model = model
        self.voice = voice
        if not dashscope.api_key:
            raise ValueError("DASHSCOPE_API_KEY not set")

    async def synthesize(self, text: str) -> str:
        filename = f"tts_cosy_{uuid.uuid4().hex}.wav"
        path = os.path.join(tempfile.gettempdir(), filename)
        
        synthesizer = SpeechSynthesizer(
            model=self.model,
            voice=self.voice,
            format=AudioFormat.WAV
        )
        
        response = synthesizer.call(text)
        if response.status_code == 200:
            with open(path, 'wb') as f:
                f.write(response.output)
            return path
        raise Exception(f"CosyVoice TTS failed: {response.message}")

class MinimaxTTSEngine(BaseTTSEngine):
    def __init__(self, voice: str):
        self.voice = voice
        self.api_key = os.getenv("MINIMAX_API_KEY")
        self.group_id = os.getenv("MINIMAX_GROUP_ID")
        if not self.api_key:
            raise ValueError("MINIMAX_API_KEY not set")
        if not self.group_id:
            raise ValueError("MINIMAX_GROUP_ID not set")
        
    async def synthesize(self, text: str) -> str:
        filename = f"tts_minimax_{uuid.uuid4().hex}.wav"
        path = os.path.join(tempfile.gettempdir(), filename)
        
        url = "https://api.minimax.chat/v1/text_to_speech"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "text": text,
            "model": "speech-02-turbo",
            "voice_id": self.voice,
            "audio_type": "wav",
            "group_id": self.group_id,
            "stream": False,
        }
        
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            with open(path, 'wb') as f:
                f.write(response.content)
            return path
        raise Exception(f"Minimax TTS failed: {response.text}")

class TTSManager:
    def __init__(self):
        self.config = ConfigManager.get_config().tts
        self.q = queue.Queue()
        self.loop = asyncio.new_event_loop()
        self._stop = threading.Event()
        self.current_engine: Optional[BaseTTSEngine] = None
        self.fallback_engine: Optional[BaseTTSEngine] = None
        
        # 初始化主引擎
        self._init_engines()
        
        # 启动播放线程
        self.player_thread = threading.Thread(target=self._player_thread, daemon=True)
        self.player_thread.start()

    def _init_engines(self):
        """初始化TTS引擎"""
        try:
            if self.config.tts_engine == "edge":
                self.current_engine = EdgeTTSEngine(self.config.edge_voice)
            elif self.config.tts_engine == "cosyvoice":
                self.current_engine = CosyVoiceTTSEngine(
                    self.config.cosyvoice_model,
                    self.config.cosyvoice_voice
                )
            elif self.config.tts_engine == "minimax":
                self.current_engine = MinimaxTTSEngine(self.config.minimax_voice)
            else:
                raise ValueError(f"Unknown TTS engine: {self.config.tts_engine}")
            
            # 初始化 fallback 引擎
            if self.config.tts_fallback_to_edge:
                self.fallback_engine = EdgeTTSEngine(self.config.edge_voice)
                
        except Exception as e:
            logger.error(f"Failed to initialize primary TTS engine: {e}")
            if self.config.tts_fallback_to_edge:
                logger.info("Falling back to Edge TTS")
                self.current_engine = EdgeTTSEngine(self.config.edge_voice)

    def _player_thread(self):
        """播放线程"""
        asyncio.set_event_loop(self.loop)
        while not self._stop.is_set():
            try:
                text = self.q.get(timeout=0.5)
                self.loop.run_until_complete(self._play_text(text))
            except queue.Empty:
                continue
            except Exception as e:
                traceback.print_exc()
                logger.error(f"TTS player error: {e}")

    async def _play_text(self, text: str):
        """尝试播放文本"""
        audio_file = None
        for attempt in range(self.config.tts_retry_times):
            try:
                audio_file = await self.current_engine.synthesize(text)
                break
            except Exception as e:
                logger.error(f"TTS synthesis failed (attempt {attempt + 1}): {e}")
                if attempt == self.config.tts_retry_times - 1 and self.fallback_engine:
                    logger.info("Trying fallback engine")
                    try:
                        audio_file = await self.fallback_engine.synthesize(text)
                        break
                    except Exception as fe:
                        logger.error(f"Fallback TTS failed: {fe}")

        if audio_file:
            try:
                playsound(audio_file)
            finally:
                if ConfigManager.get_config().starter.debug_mode:
                    # 在debug模式下，将文件复制到工作目录
                    debug_filename = f"last_tts_{self.config.tts_engine}.wav"
                    try:
                        import shutil
                        shutil.copy2(audio_file, debug_filename)
                        logger.info(f"Debug: 已保存最后的TTS音频文件到 {debug_filename}")
                    except Exception as e:
                        logger.error(f"Debug: 保存音频文件失败: {e}")
                os.remove(audio_file)

    def play(self, text: str):
        """添加文本到播放队列"""
        self.q.put(text)

    def stop(self):
        """停止TTS管理器"""
        self._stop.set()
        self.player_thread.join()
        self.loop.close() 