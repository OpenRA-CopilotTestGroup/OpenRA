# asr_manager.py
import threading
from queue import Queue, Empty
import time
import speech_recognition as sr
import numpy as np
from uni_mic.utils import get_logger

class ASRManager:
    def __init__(self, asr_module, audio_queue: Queue, result_queue: Queue, stop_event: threading.Event):
        self.asr_module = asr_module
        self.audio_queue = audio_queue
        self.result_queue = result_queue
        self.stop_event = stop_event
        self.trans_thread = None
        self.is_listening = True
        self.logger = get_logger(__name__, 'info')

    def start(self):
        self.trans_thread = threading.Thread(
            target=self.__process_audio,
            daemon=True
        )
        self.trans_thread.start()

    def enable_listen(self):
        self.is_listening = True
    
    def disable_listen(self):
        self.is_listening = False

    @staticmethod
    def __trans_to_numpy(data: sr.AudioData):
        raw_data = data.get_raw_data()
        return np.frombuffer(raw_data, np.int16).flatten().astype(np.float32) / 32768.0

    def __process_audio(self):
        while not self.stop_event.is_set():
            if not self.is_listening:
                time.sleep(0.1)
                continue
            try:
                audio_data = self.audio_queue.get(timeout=0.1)
                numpy_data = self.__trans_to_numpy(audio_data)
                self.logger.info(f"ASR_Manager -> Transcribing audio...")
                result = self.asr_module.transcribe(numpy_data)
                if result:  # Only put non-empty results
                    self.result_queue.put_nowait(result)
                    self.logger.info(f"ASR_Manager -> put the result:{result}")
                    
            except Empty:
                continue
            except Exception as e:
                self.logger.error(f"ASR_Manager -> Error: {e}")
                continue
    
    def stop(self):
        self.stop_event.set()
        if self.trans_thread.is_alive():
            self.trans_thread.join()