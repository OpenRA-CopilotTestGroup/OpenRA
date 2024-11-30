# audio_listener.py
import threading
from queue import Queue
import time
import pyaudio
import webrtcvad

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
        
        self.stream = None
        self.stream_format = pyaudio.paInt16
        self.stream_channels = 1
        self.chunk_size = 1024
        self.sample_rate = 16000
        self.__init_audio_device()
    
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
        self.monitor_thread.start()
        self.listen_thread.start()
    
    def __listen(self):
        while not self.stop_event.is_set():
            if not self.is_listening:
                time.sleep(0.1)
                continue
            if not self.stream:
                if not self.selected_device_index:
                    self.__init_audio_device()
                if self.selected_device_index:
                    check = self.__open_stream()
                    if check:
                        pass
                    else:
                        time.sleep(3.0)
                        continue
                else:
                    time.sleep(1.0)  # Wait before retry
                continue
                
            try:
                audio_data = self.stream.read(
                    self.chunk_size,
                    exception_on_overflow=False
                )
                if self.__is_speech(audio_data):
                    self.asr_manager.audio_queue.put(audio_data)
            except Exception as e:
                print(f"Error while reading audio: {e}")
                #self.__close_stream()
            finally:    
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