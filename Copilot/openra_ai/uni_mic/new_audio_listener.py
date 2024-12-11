import threading
from queue import Queue
import time
import pyaudio
import webrtcvad
import speech_recognition as sr
import struct
import numpy as np
import traceback
from .utils import get_logger

class AudioListener:
    def __init__(self, asr_manager, stop_event):
        self.asr_manager = asr_manager
        # ensure synchronized stopping
        self.stop_event = stop_event
        self.listen_thread = None
        self.monitor_thread = None
        self.is_recording = True
        #self.audio_queue = asr_manager.audio_queue
        #self.data_queue = asr_manager.data_queue
        #self.result_queue = asr_manager.result_queue
        self.logger = get_logger(__name__, 'info')
        
        self.stream = None
        self.stream_format = pyaudio.paInt16
        self.stream_channels = 1
        self.chunk_size = 1024
        self.sample_rate = 16000
        
        # for sr
        self.mic = None
        self.recognizer = sr.Recognizer()
        self.device_index = None
        self.cur_frames = []
        self.energy = 300
        self.dynamic_energy = False
        self.phrase_time_limit = 10
        self.energy_threshold = 300
        self.hallucinate_threshold = 400
        
        # for vad
        self.vad = webrtcvad.Vad(1)
        
    def __setup_mic(self):
        while not self.stop_event.is_set():
            try:
                self.mic = sr.Microphone(sample_rate=self.sample_rate,device_index=self.device_index)
                with self.mic as source:
                    self.recognizer.energy_threshold = self.energy_threshold
                    self.recognizer.adjust_for_ambient_noise(source, duration=2)
                break
            except Exception as e:
                print(f"setup_mic -> No microphone available:{e}")
                if self.stop_event.is_set():
                    break
                time.sleep(1)
    
    def __close_mic(self):
        """if self.mic is not None and self.mic.stream is not None:
            try:
                self.mic.stream.stop_stream()
                self.mic.stream.close()
            except Exception as e:
                pass"""
        self.mic = None
    
    def __is_loud_enough(self, audio_data: sr.AudioData):
        raw_data = audio_data.get_raw_data()
        audio_frame = np.frombuffer(raw_data, dtype=np.int16)
        amplitude = np.mean(np.abs(audio_frame))
        return amplitude > self.energy_threshold
    
    def __get_all_audio(self, min_time: float = -1.):
        audio = bytes()
        got_audio = False
        time_start = time.time()
        while not got_audio or time.time() - time_start < min_time:
            while not self.audio_queue.empty():
                audio += self.audio_queue.get()
                got_audio = True
        data = sr.AudioData(audio,16000,2)
        return data
    
    def __preprocess(self, audio_data: sr.AudioData):
        """try:
            raw_data = audio_data.get_raw_data()
            audio_loud_enough = self.__is_loud_enough(raw_data)
            if not audio_loud_enough:
                self.logger.info("preprocess -> Audio not loud enough")
                return None
            return np.frombuffer(raw_data, dtype=np.int16).astype(np.float32) / 32768.0
        except Exception as e:
            self.logger.error(f"preprocess -> Error: {e}")
            return None"""
        return self.__is_loud_enough(audio_data)
    
    @staticmethod
    def __calc_volume(audio_frame):
        # a placeholder
        sample_count = len(audio_frame) // 2
        if sample_count == 0:
            return 0
        fmt = "<" + "h" * sample_count
        samples = struct.unpack(fmt, audio_frame)
        square_sum = sum(s**2 for s in samples)
        rms = (square_sum / sample_count) ** 0.5
        return rms
    
    def __is_speech(self, audio_frame):
        # a placeholder
        return self.vad.is_speech(audio_frame, self.sample_rate)
    
    def __is_valid_speech(self, full_data):
        # Adjust frame size to 30ms for VAD
        frame_duration_ms = 30
        frame_size = int(self.sample_rate * frame_duration_ms / 1000) * 2  # 2 bytes per sample for 16-bit audio
        frames = [full_data[i:i+frame_size] for i in range(0, len(full_data), frame_size)]
        voice_frames = [f for f in frames if self.__is_speech(f)]
        return len(voice_frames) > 3
    
    def pre__listen_loop(self):
        self.__setup_mic()
        threshold = self.recognizer.energy_threshold
        start_talking = threshold * 1.5
        end_talking = 0.8
        silence_start = None
        while not self.stop_event.is_set():
            try:
                with self.mic as source:
                    audio_frame = source.stream.read(self.chunk_size)
                    volume = self.__calc_volume(audio_frame)
                if not self.is_recording:
                    if volume >= start_talking:
                        self.logger.info("listen_loop -> Recording started")
                        self.is_recording = True
                        self.cur_frames = [audio_frame]
                        silence_start = None
                else:
                    self.cur_frames.append(audio_frame)
                    self.logger.info("listen_loop -> Recording in progress")
                    if volume > self.energy:
                        silence_start = None
                    else:
                        if silence_start is None:
                            silence_start = time.time()
                        elif time.time() - silence_start > end_talking:
                            self.logger.info("listen_loop -> Recording stopped")
                            full_data = b''.join(self.cur_frames)
                            
                            if self.__is_valid_speech(full_data):
                                audio_data = sr.AudioData(full_data, self.sample_rate, 2)
                                self.asr_manager.audio_queue.put(audio_data)
                            else:
                                self.logger.info("listen_loop -> Invalid speech detected")

                            self.is_recording = False
                            self.cur_frames = []
                            silence_start = None
                time.sleep(0.01)
            except OSError as e:
                self.logger.error(f"listen_loop -> OSError: {e}")
                self.__restart()
                threshold = self.recognizer.energy_threshold
            except Exception as e:
                self.logger.error(f"listen_loop -> Unkown error: {e}")
                #self.__restart()
                time.sleep(1)
            
    def __listen_loop(self):
        self.__setup_mic()
        while not self.stop_event.is_set():
            try:
                with self.mic as source:
                    self.logger.info("listen_loop -> Listening for audio")
                    audio_data = self.recognizer.listen(source, phrase_time_limit=self.phrase_time_limit)
                    loud = self.__preprocess(audio_data)
                    if loud:
                        self.asr_manager.audio_queue.put_nowait(audio_data)
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
        #self.logger.warning(f"handle_device_error -> Error with device: {error}")
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
        self.logger.info("stop -> Listen thread stopped")


