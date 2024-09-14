#import torch
import queue
import speech_recognition as sr
import threading
import numpy as np
import os
import os.path
import time
import json
import tempfile
import platform
import pynput.keyboard
from io import BytesIO
from openai import OpenAI
# from ctypes import *

from utils import get_logger

#TODO: This is a linux only fix and needs to be testd.  Have one for mac and windows too.
# Define a null error handler for libasound to silence the error message spam
# def py_error_handler(filename, line, function, err, fmt):
#     None

# ERROR_HANDLER_FUNC = CFUNCTYPE(None, c_char_p, c_int, c_char_p, c_int, c_char_p)
# c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)

# asound = cdll.LoadLibrary('libasound.so')
# asound.snd_lib_error_set_handler(c_error_handler)
class WhisperMic:
    def __init__(
        self,model="base",
        device="cpu",
        language="zh",verbose=False,energy=300,pause=2,dynamic_energy=False,save_file=False,
        model_root="~/.cache/whisper",mic_index=None,faster=False,hallucinate_threshold=300,
        prompt=None,
        prefix=None,
        initial_prompt=None,
        remote=False,
        enable_post_processing=False,
        post_prompt=None,
        ignore_text_without_prefix=False,
        remove_prefix=False,
        phrase_time_limit=10,
        logging_level="info",
        config=None,
        text_callback=None
    ):
        self.config_json = {}
        if not config:
            import pkg_resources
            config = pkg_resources.resource_filename('whisper_mic', 'config.json')
        if config and os.path.exists(config):
            with open(config, 'r', encoding="utf-8") as f:
                self.config_json = json.load(f)
        self.logging_level = self.config_json.get("logging_level", logging_level)
        self.logger = get_logger("whisper_mic", self.logging_level)
        self.logger.info("logging_level: %s", self.logging_level)
        self.energy = self.config_json.get('energy', energy)
        self.logger.info('energy: %s', self.energy)
        self.hallucinate_threshold = self.config_json.get('hallucinate_threshold', hallucinate_threshold)
        self.logger.info('hallucinate_threshold: %s', self.hallucinate_threshold)
        self.pause = self.config_json.get('pause', pause)
        self.logger.info('pause: %s', self.pause)
        self.dynamic_energy = self.config_json.get('dynamic_energy: 5s', dynamic_energy)
        self.logger.info('dynamic_energy: %s', self.dynamic_energy)
        self.save_file = self.config_json.get('save_file', save_file)
        self.logger.info('save_file: %s', self.save_file)
        self.verbose = self.config_json.get('verbose', verbose)
        self.logger.info('verbose: %s', self.verbose)
        self.language = self.config_json.get('language', language)
        self.logger.info("language: %s", self.language)
        self.text_callback = text_callback
        self.prompt = self.config_json.get('prompt', prompt)
        self.logger.info("prompt: %s", self.prompt)
        self.prefix = self.config_json.get('prefix', prefix)
        self.logger.info("prefix: %s", self.prefix)
        self.initial_prompt = self.config_json.get('initial_prompt', initial_prompt)
        if self.prefix:
            self.initial_prompt = self.initial_prompt + self.prefix
        self.logger.info("initial_prompt: %s", self.initial_prompt)
        self.enable_post_processing = self.config_json.get('enable_post_processing', enable_post_processing)
        self.logger.info('enable_post_processing: %s', self.enable_post_processing)
        self.post_prompt = self.config_json.get('post_prompt', post_prompt)
        self.logger.info('post_prompt: %s', self.post_prompt)
        self.remote = self.config_json.get("remote", remote)
        self.logger.info("remote: %s", self.remote)
        self.faster = self.config_json.get('faster', faster)
        self.logger.info("faster: %s", self.faster)
        self.ignore_text_without_prefix = self.config_json.get('ignore_text_without_prefix', ignore_text_without_prefix)
        self.logger.info('ignore_text_without_prefix: %s', self.ignore_text_without_prefix)
        self.remove_prefix = self.config_json.get('remove_prefix', remove_prefix)
        self.logger.info('remove_prefix: %s', self.remove_prefix)
        self.model = self.config_json.get("model", model)
        if (self.model != "large" and self.model != "large-v2") and self.language == "en":
            self.model = self.model + ".en"
        self.logger.info("model: %s", self.model)
        self.phrase_time_limit = self.config_json.get("phrase_time_limit", phrase_time_limit)
        self.logger.info("phrase_time_limit: %s", self.phrase_time_limit)
        self.keyboard = pynput.keyboard.Controller()
        self.platform = platform.system()
        self.logger.info('platform: %s', self.platform)

        device = self.config_json.get('device', device)
        if self.platform == "darwin":
            if device == "mps":
                self.logger.warning("Using MPS for Mac, this does not work but may in the future")
                device = "mps"
                #device = torch.device(device)
        self.device = device
        self.logger.info("device: %s", self.device)

        model_root = os.path.expanduser(model_root)
        self.logger.info("model_root: %s", model_root)
        self.client = OpenAI()
        if self.remote:
            pass
        elif self.faster:
            from faster_whisper import WhisperModel
            self.audio_model = WhisperModel(self.model, download_root=model_root, device=self.device, compute_type="int8")            
        else:
            import whisper
            self.audio_model = whisper.load_model(self.model, device=self.device, download_root=model_root, in_memory=True)
        
        self.temp_dir = tempfile.mkdtemp() if self.save_file else None

        self.audio_queue = queue.Queue()
        self.result_queue: "queue.Queue[str]" = queue.Queue()
        
        self.break_threads = False
        self.mic_active = False

        self.banned_results = [""," ","\n",None]

        if self.save_file:
            self.file = open("transcribed_text.txt", "w+", encoding="utf-8")

        self.__setup_mic(mic_index)

    def generate_corrected_transcript(self, transcribed_text):
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": self.post_prompt
                },
                {
                    "role": "user",
                    "content": transcribed_text
                }
            ]
            # response_format ={"type": "json_object"}
        )
        self.logger.debug("corrected transcript: %s", response)
        return response.choices[0].message.content

    def __setup_mic(self, mic_index):
        if mic_index is None:
            self.logger.info("No mic index provided, using default")
        self.source = sr.Microphone(sample_rate=16000, device_index=mic_index)

        self.recorder = sr.Recognizer()
        self.recorder.energy_threshold = self.energy
        self.recorder.pause_threshold = self.pause
        self.recorder.dynamic_energy_threshold = self.dynamic_energy

        with self.source:
            self.recorder.adjust_for_ambient_noise(self.source)

        self.logger.info("Mic setup complete")

    # Whisper takes a Tensor while faster_whisper only wants an NDArray
    def __preprocess(self, data):
        raw_data = data.get_raw_data()
        is_audio_loud_enough = self.is_audio_loud_enough(raw_data)
        if self.remote:
            wav_data = BytesIO(data.get_wav_data())
            wav_data.name = "SpeechRecognition_audio.wav"
            return wav_data,is_audio_loud_enough
        else:
            return np.frombuffer(raw_data, np.int16).flatten().astype(np.float32) / 32768.0,is_audio_loud_enough
        #else:
        #    return torch.from_numpy(np.frombuffer(raw_data, np.int16).flatten().astype(np.float32) / 32768.0),is_audio_loud_enough
        
    def is_audio_loud_enough(self, frame):
        audio_frame = np.frombuffer(frame, dtype=np.int16)
        amplitude = np.mean(np.abs(audio_frame))
        return amplitude > self.hallucinate_threshold

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

    # Handles the task of getting the audio input via microphone. This method has been used for listen() method
    def __listen_handler(self, timeout):
        try:
            with self.source as microphone:
                audio = self.recorder.listen(source=microphone, timeout=timeout, phrase_time_limit=self.phrase_time_limit)
            self.__record_load(0, audio)
            audio_data = self.__get_all_audio()
            self.__transcribe(data=audio_data)
        except sr.WaitTimeoutError:
            self.result_queue.put_nowait("Timeout: No speech detected within the specified time.")
        except sr.UnknownValueError:
            self.result_queue.put_nowait("Speech recognition could not understand audio.")


    # This method is similar to the __listen_handler() method but it has the added ability for recording the audio for a specified duration of time
    def __record_handler(self, duration, offset):
        with self.source as microphone:
            audio = self.recorder.record(source=microphone, duration=duration, offset=offset)
        
        self.__record_load(0, audio)
        audio_data = self.__get_all_audio()
        self.__transcribe(data=audio_data)


    # This method takes the recorded audio data, converts it into raw format and stores it in a queue. 
    def __record_load(self,_, audio: sr.AudioData) -> None:
        data = audio.get_raw_data()
        self.audio_queue.put_nowait(data)


    def __transcribe_forever(self) -> None:
        while True:
            if self.break_threads:
                break
            self.__transcribe()


    def __transcribe(self,data=None, realtime: bool = False) -> None:
        if data is None:
            audio_data = self.__get_all_audio()
        else:
            audio_data = data
        audio_data,is_audio_loud_enough = self.__preprocess(audio_data)

        if is_audio_loud_enough:
            predicted_text = ''
            self.logger.debug("send request")
            if self.remote:
                prompt = self.initial_prompt
                if self.prompt:
                    prompt = prompt + self.prompt
                transcription = self.client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_data, 
                    language=self.language,
                    prompt=prompt,
                    # response_format="text"
                )
                self.logger.debug("received transcription: %s", transcription)
                predicted_text = transcription.text
            # faster_whisper returns an iterable object rather than a string
            elif self.faster:
                prompt = self.initial_prompt
                if self.prompt:
                    prompt = prompt + self.prompt
                segments, info = self.audio_model.transcribe(
                    audio_data,language=self.language,
                    prefix=self.prefix,                                 
                    initial_prompt=prompt)
                for segment in segments:
                    self.logger.debug("received segment: %s", segment)
                    predicted_text += segment.text
            else:
                result = self.audio_model.transcribe(
                    audio_data,language=self.language,suppress_tokens="",
                    prefix=self.prefix,
                    initial_prompt=self.initial_prompt, prompt=self.prompt
                )
                self.logger.debug("received result: %s", result)
                predicted_text = result["text"]

            predicted_text = predicted_text.strip()
            if predicted_text and self.enable_post_processing:
                predicted_text = self.generate_corrected_transcript(predicted_text)
            
            if predicted_text and self.prefix:
                if not predicted_text.startswith(self.prefix):
                    if self.ignore_text_without_prefix:
                        self.logger.debug('ignore %r because it is not started with prefix', predicted_text)
                        predicted_text = ''
                else:
                    if self.remove_prefix:
                        self.logger.debug('remove prefix from  %r', predicted_text)
                        predicted_text = predicted_text[len(self.prefix):]

            if predicted_text:
                if predicted_text not in self.banned_results:
                    if not self.verbose:
                        self.result_queue.put_nowait(predicted_text)
                    else:
                        self.result_queue.put_nowait(result)
                else:
                    self.logger.debug('skip %r because it is in banned_results', predicted_text)

                if self.save_file:
                    # os.remove(audio_data)
                    self.file.write(predicted_text)
        else:
            self.logger.debug('ignore audio because it is not loud enough')

    async def listen_loop_async(self, dictate: bool = False) -> None:
        for result in self.listen_continuously():
            if dictate:
                self.keyboard.type(result)
            else:
                yield result


    def listen_loop(self) -> None:
        for result in self.listen_continuously():
            if self.text_callback:
                self.text_callback(result)


    def listen_continuously(self):
        self.recorder.listen_in_background(self.source, self.__record_load, phrase_time_limit=self.phrase_time_limit)
        self.logger.info("Listening...")
        threading.Thread(target=self.__transcribe_forever, daemon=True).start()

        while True:
            yield self.result_queue.get()

            
    def listen(self, timeout = None):
        self.logger.info("Listening...")
        self.__listen_handler(timeout)
        while True:
            if not self.result_queue.empty():
                return self.result_queue.get()


    # This method is similar to the listen() method, but it has the ability to listen for a specified duration, mentioned in the "duration" parameter.
    def record(self, duration=None, offset=None):
        self.logger.info("Listening...")
        self.__record_handler(duration, offset)
        while True:
            if not self.result_queue.empty():
                return self.result_queue.get()


    def toggle_microphone(self) -> None:
        #TO DO: make this work
        self.mic_active = not self.mic_active
        if self.mic_active:
            self.logger.info("Mic on")
        else:
            self.logger.info("turning off mic")
            self.mic_thread.join()
            self.logger.info("Mic off")
