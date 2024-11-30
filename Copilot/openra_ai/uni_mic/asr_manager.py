# asr_manager.py
import threading
from queue import Queue, Empty
import time

class ASRManager:
    def __init__(self, asr_module, audio_queue: Queue, result_queue: Queue):
        self.asr_module = asr_module
        self.audio_queue = audio_queue
        self.result_queue = result_queue
        self.stop_event = threading.Event()
        self.trans_thread = None
        self.is_listening = True

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

    def __process_audio(self):
        while not self.stop_event.is_set():
            if not self.is_listening:
                time.sleep(0.1)
                continue
            try:
                audio_data = self.audio_queue.get(timeout=0.1)
                result = self.asr_module.transcribe(audio_data)
                if result:  # Only put non-empty results
                    self.result_queue.put(result)
            except Empty:
                continue
            except Exception as e:
                print(f"Error processing audio: {e}")
                continue
    
    def stop(self):
        self.stop_event.set()
        self.trans_thread.join()