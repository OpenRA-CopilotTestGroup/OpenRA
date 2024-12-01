# audio_listener.py
import threading
from queue import Queue
import time
import pyaudio
import webrtcvad
import speech_recognition as sr

class AudioListener:
    def __init__(self, asr_manager):
        self.asr_manager = asr_manager
        # ensure synchronized stopping
        self.stop_event = asr_manager.stop_event
        self.selected_device_index = None
        self.audio_interface = pyaudio.PyAudio()
        self.listen_thread = None
        self.monitor_thread = None
        self.is_listening = True
        #self.audio_queue = asr_manager.audio_queue
        #self.data_queue = asr_manager.data_queue
        #self.result_queue = asr_manager.result_queue
        
        self.stream = None
        self.stream_format = pyaudio.paInt16
        self.stream_channels = 1
        self.chunk_size = 1024
        self.sample_rate = 16000
        
        # for sr
        self.source = None
        self.recorder = None
        self.energy = 300
        self.pause = 1.2
        self.dynamic_energy = False
        self.phrase_time_limit = 10
        self.listen_bg_thread = None
        self.lock = threading.Lock()
        
        self.__setup_mic(self.selected_device_index)
        
        #self.__init_audio_device()
    
    def enable_listen(self):
        self.is_listening = True
    
    def disable_listen(self):
        self.is_listening = False
        
    def start(self):
        self.listen_thread = threading.Thread(
            target=self.__listen,
            daemon=True
        )
        self.monitor_thread = threading.Thread(
            target=self.__monitor_device,
            daemon=True
        )
        self.listen_bg_thread = threading.Thread(
            target=self.__listen_in_background,
            daemon=True
        )
        print("Starting audio listener...")
        self.monitor_thread.start()
        #self.listen_thread.start()
        self.listen_bg_thread.start()
    
    def __listen(self):
        while not self.stop_event.is_set():
            if not self.is_listening:
                time.sleep(0.1)
                continue
            if not self.source:
                #if not self.selected_device_index:
                #    #self.__init_audio_device()
                self.__setup_mic()
                """if self.selected_device_index:
                    check = self.__open_stream()
                    if check:
                        pass
                    else:
                        time.sleep(3.0)
                        continue
                else:
                    time.sleep(1.0)  # Wait before retry
                continue"""
                
            try:
                """audio_data = self.stream.read(
                    self.chunk_size,
                    exception_on_overflow=False
                )"""
                
                print("Listening...")
                #if self.__is_speech(audio_data):
                #    self.asr_manager.audio_queue.put(audio_data)
            except Exception as e:
                print(f"Error while reading audio: {e}")
                #self.__close_stream()
            finally:
                print("Stopped listening")
                if self.source.stream is not None and not self.source.stream.is_stopped():
                    self.source.stream.stop_stream()
                    self.source.stream.close()
                    self.source.stream = None    
                time.sleep(5.0)  # Short delay before retry
    
    def __open_stream(self):
        try:
            self.__close_stream()
            self.stream = self.audio_interface.open(
                format=self.stream_format,
                channels=self.stream_channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
                input_device_index=self.selected_device_index
            )
            return True
        except Exception as e:
            print(f"Error opening audio stream: {e}")
            self.stream = None
            return False
    
    def __init_audio_device(self):
        devices = self.__list_devices()
        if devices:
            self.selected_device_index = devices[1][0]
            print(f"Selected audio device: {devices[1][1]} (index: {self.selected_device_index})")
        else:
            print("No audio input devices found!")
    
    def __close_stream(self):
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
    
    def __is_speech(self, audio_data):
        # Placeholder for speech detection
        vad = webrtcvad.Vad(1)
        is_speech = vad.is_speech(audio_data, self.sample_rate)
        return is_speech
    
    def __handle_device_error(self, error):
        print(f"Error opening audio stream: {error}")
        #self.stream = None
        #self.stop_event.set()
        time.sleep(1.0)  # Wait before retrying
    
    def __monitor_device(self):
        print("start monitoring device")
        pre_devices = []
        while not self.stop_event.is_set():
            try:
                #current_device = self.audio_interface.get_device_info_by_index(self.selected_device_index)
                cur_devices = self.__list_devices()
                if cur_devices != pre_devices:
                    pre_devices = cur_devices
                    if cur_devices:
                        self.selected_device_index = self.__select_device(cur_devices[0][0])
                    else:
                        self.selected_device_index = None
                        self.__close_stream()
                        print("No audio input devices found.")
            except:
                self.selected_device_index = None
            time.sleep(2.0)
    
    def __list_devices(self):
        device_count = self.audio_interface.get_device_count()
        device = []
        for i in range(device_count):
            device_info = self.audio_interface.get_device_info_by_index(i)
            if device_info['maxInputChannels'] > 0 and ("Microphone" in device_info['name'] or "麦克风" in device_info['name']):
                device.append((i,device_info['name']))
        return device
    
    def __select_device(self, device_index):
        self.selected_device_index = device_index
        self.__close_stream()
        self.__open_stream()
    
    def stop(self):
        self.stop_event.set()
        self.__close_stream()
        self.listen_thread.join()
        #if self.monitor_thread:
        self.monitor_thread.join()
        self.audio_interface.terminate()
        
    # implement sr from whisper_mic for testing
    def __setup_mic(self, mic_index=None):
        if mic_index is None:
            print("No microphone selected")
        with self.lock:
            if self.source:
                self.source.__exit__(None, None, None) 
        self.source = sr.Microphone(sample_rate=self.sample_rate, device_index=mic_index)
        #self.source.__enter__()
        
        self.recorder = sr.Recognizer()
        self.recorder.energy_threshold = self.energy
        self.recorder.pause_threshold = self.pause
        self.recorder.dynamic_energy_threshold = self.dynamic_energy
        
        with self.source:
            self.recorder.adjust_for_ambient_noise(self.source)
        print("Audio device setup successful")
    
    def __record_load(self,_, audio: sr.AudioData):
        data = audio.get_raw_data()
        self.asr_manager.audio_queue.put_nowait(data)
    
    def __get_audio(self, min_time: float = -1.):
        audio = bytes()
        got_audio = False
        time_start = time.time()
        while not got_audio or time.time() - time_start < min_time:
            while not self.asr_manager.audio_queue.empty():
                audio += self.asr_manager.audio_queue.get()
                got_audio = True
        data = sr.AudioData(audio,16000,2)
        return data
    
    def __yield_data(self):
        while True:
            try:
                data = self.__get_audio()
                self.asr_manager.data_queue.put(data)
            except Exception as e:
                print(f"Error getting audio data: {e}")
        
    def __listen_in_background(self):
        self.recorder.listen_in_background(
            self.source,
            self.__record_load,
            phrase_time_limit=self.phrase_time_limit
        )
        print("Listening in background...")
        threading.Thread(target=self.__yield_data, daemon=True).start()