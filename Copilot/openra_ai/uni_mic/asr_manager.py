# asr_manager.py
import threading
from queue import Queue, Empty

class ASRManager:
    def __init__(self, asr_module, audio_queue: Queue, result_queue: Queue):
        self.asr_module = asr_module
        self.audio_queue = audio_queue
        self.result_queue = result_queue
        self.stop_event = threading.Event()
        self.trans_thread = None
    
        #self.is_listening = False

    def start(self):
        self.trans_thread = threading.Thread(
            target=self.__process_audio,
            daemon=True
        )
        self.trans_thread.start()

    def __process_audio(self):
        while not self.stop_event.is_set():
            try:
                audio_data = self.audio_queue.get(timeout=0.1)
                # implement transcribe method in asr_module.py
                result = self.asr_module.transcribe(audio_data)
                self.result_queue.put(result)
            except Empty:
                continue
            except Exception as e:
                print(f"Error processing audio: {e}")
                continue
    
    def stop(self):
        self.stop_event.set()
        self.trans_thread.join()