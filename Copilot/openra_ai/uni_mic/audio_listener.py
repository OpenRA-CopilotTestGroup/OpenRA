import threading
import time
import speech_recognition as sr
import numpy as np
import traceback
from queue import Queue
from uni_mic.utils import get_logger
from uni_mic.config import AppConfig
from uni_mic.asr_manager import ASRManager

class AudioListener:
    def __init__(self, asr_manager:ASRManager, stop_event, config:AppConfig = None):
        self.asr_manager = asr_manager
        self.stop_event = stop_event
        self.listen_thread = None
        self.is_recording = True
        self.audio_queue:Queue = asr_manager.audio_queue
        self.logger = get_logger(__name__, 'info')

        self.mic = None
        self.energy_threshold = config.input.energy if config else 300
        self.sample_rate = 16000
        self.recognizer = sr.Recognizer()
        self.device_index = config.input.mic_index if config else None
        self.dynamic_energy = config.input.dynamic_energy if config else False
        self.phrase_time_limit = config.asr.phrase_time_limit if config else 10
        
        self.energy_threshold = 300
        self.min_energy_threshold = 200
        self.max_energy_threshold = 800
        self.energy_adjustment_ratio = 1.2
        self.noise_floor = None
        self.is_listening = True

        # adjust manually
        self.pause_threshold = config.input.pause if config else 1.2
        self.non_speaking_duration = config.input.pause if config else 0.3

    def __setup_mic(self):
        while not self.stop_event.is_set():
            try:
                self.mic = sr.Microphone(sample_rate=self.sample_rate,device_index=self.device_index)
                with self.mic as source:
                    self.recognizer.energy_threshold = self.energy_threshold
                    self.recognizer.pause_threshold = self.pause_threshold
                    self.recognizer.non_speaking_duration = self.non_speaking_duration
                    self.recognizer.adjust_for_ambient_noise(source, duration=2)
                break
            except Exception as e:
                print(f"setup_mic -> No microphone available:{e}")
                print(f"setup_mic -> Exception type: {type(e).__name__}")
                print(f"setup_mic -> Error message: {str(e)}")
                traceback.print_exc()
                if self.stop_event.is_set():
                    break
                time.sleep(1)

    def __close_mic(self):
        self.mic = None

    # not used now
    def __adjust_energy_threshold(self, audio_frame):
        if not self.dynamic_energy:
            return

        amplitude = np.mean(np.abs(audio_frame))
        
        if self.noise_floor is None:
            self.noise_floor = amplitude
            self.energy_threshold = max(self.min_energy_threshold, 
                                     min(amplitude * 1.2, self.max_energy_threshold))
            return

        if amplitude > self.energy_threshold:
            self.logger.info(f"Energy threshold adjusted: {self.energy_threshold} -> {amplitude * self.energy_adjustment_ratio}")
            self.energy_threshold = min(
                amplitude * self.energy_adjustment_ratio,
                self.max_energy_threshold
            )
        elif amplitude < self.noise_floor:
            self.logger.info(f"Noise floor adjusted: {self.noise_floor} -> {amplitude * 0.9}")
            self.noise_floor = amplitude * 0.9 + self.noise_floor * 0.1
            self.energy_threshold = max(
                self.noise_floor * 1.2,
                self.min_energy_threshold
            )

    def __is_loud_enough(self, audio_data: sr.AudioData):
        raw_data = audio_data.get_raw_data()
        audio_frame = np.frombuffer(raw_data, dtype=np.int16)
        #self.__adjust_energy_threshold(audio_frame)
        amplitude = np.mean(np.abs(audio_frame))
        return amplitude > self.energy_threshold

    def __listen_loop(self):
        self.__setup_mic()
        while not self.stop_event.is_set():
            try:
                if not self.is_listening:
                    time.sleep(0.1)
                    continue

                with self.mic as source:
                    self.logger.info("listen_loop -> Listening for audio")
                    audio_data = self.recognizer.listen(
                        source,
                        phrase_time_limit=self.phrase_time_limit,
                        timeout=None
                    )
                    # check again if listening is still on
                    if not self.is_listening:
                        continue
                    loud = self.__is_loud_enough(audio_data)
                    if loud:
                        self.audio_queue.put_nowait(audio_data)
                        self.logger.info("listen_loop -> Audio data sent to queue")
                    else:
                        self.logger.info("listen_loop -> Audio not loud enough")
            except (sr.WaitTimeoutError, sr.UnknownValueError) as e:
                self.logger.error(f"listen_loop -> SR error: {e}")
                self.__restart()
            except Exception as e:
                self.logger.error(f"listen_loop -> Unkown error: {e}:\n {traceback.format_exc()}")
                #self.__restart()
                time.sleep(1)

    def __restart(self):
        self.__close_mic()
        self.__setup_mic()

    def start(self):
        self.listen_thread = threading.Thread(target=self.__listen_loop, daemon=True)
        self.listen_thread.start()
        self.logger.info("start -> Listen thread started")

    def stop(self):
        self.stop_event.set()
        if self.listen_thread and self.listen_thread.is_alive():
            self.listen_thread.join()
        self.logger.info("Audio_listener -> Listen thread stopped")

    def pause_listening(self):
        self.is_listening = False
        self.logger.info("Audio_listener -> Microphone paused")

    def resume_listening(self):
        self.is_listening = True
        self.logger.info("Audio_listener -> Microphone resumed")

    def get_listening_status(self):
        return self.is_listening
