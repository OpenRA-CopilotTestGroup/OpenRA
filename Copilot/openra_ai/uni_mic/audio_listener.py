# audio_listener.py
import threading
from queue import Queue
import time
import pyaudio
import webrtcvad

class AudioListener:
    def __init__(self, asr_manager):
        self.asr_manager = asr_manager
        self.stop_event = threading.Event()
        self.selected_device_index = None
        self.audio_interface = pyaudio.PyAudio()
        self.listen_thread = None
        
        self.stream = None
        self.stream_format = pyaudio.paInt16
        self.stream_channels = 1
        self.chunk_size = 1024
        self.sample_rate = 16000
        
        #self.audio_queue = audio_queue
        #self.stop_event = stop_event
        #self.mic_index = mic_index
        
    def start(self):
        self.listen_thread = threading.Thread(
            target=self.__listen,
            daemon=True
        )
        self.listen_thread.start()
    
    def __listen(self):
        while not self.stop_event.is_set():
            if not self.stream:
                self.__open_stream()
            try:
                audio_data = self.stream.read(
                    self.chunk_size,
                    exception_on_overflow=False
                )
                if self.__is_speech(audio_data):
                    self.asr_manager.audio_queue.put(audio_data)
            except Exception as e:
                self.__close_stream()
                self.__handle_device_error(e)
            
    def __open_stream(self):
        try:
            self.stream = self.audio_interface.open(
                format=self.stream_format,
                channels=self.stream_channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
                input_device_index=self.selected_device_index
            )
        except Exception as e:
            self.__handle_device_error(e)
    
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
        while not self.stop_event.is_set():
            """if not self.selected_device_index:
                devices = self.__list_devices()
                if devices:
                    print("Available devices:")
                    for index, device_name in devices:
                        print(f"{index}: {device_name}")
                    device_index = input("Select device: ")
                    self.__select_device(int(device_index))
                else:
                    print("No audio input devices found.")
            time.sleep(1.0)"""
            #current_device
    
    def __list_devices(self):
        device_count = self.audio_interface.get_device_count()
        device = []
        for i in range(device_count):
            device_info = self.audio_interface.get_device_info_by_index(i)
            if device_info['maxInputChannels'] > 0:
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
        self.audio_interface.terminate()