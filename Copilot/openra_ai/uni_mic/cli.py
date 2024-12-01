#!/usr/bin/env python3

import click
# import torch
import speech_recognition as sr
from typing import Optional
import time
import os
import sys
import queue
import threading

from .rafuncs import handle_strategy_command
from .gui import create_ai_assistant_ui_instance
from .audio_listener import AudioListener
#from .sr_listener import AudioListener
from .utils import get_logger
from .asr_manager import ASRManager
from .asr_module import WhisperASR
logger = get_logger("cli", 'info')

CACHED_PROMPTS = []
CACHED_TIME = 0.0
LAST_TIME = 0.0
GPTMODEL = "gpt-4o"
GUI_WINDOW = None
GUI_APP = None
text_callback_queue = queue.Queue()


def text_callback(text: str, is_from_ui: bool = False):
    print(repr(text))
    global CACHED_PROMPTS
    global CACHED_TIME
    global GPTMODEL
    if not is_from_ui and GUI_WINDOW:
        GUI_WINDOW.add_player_dialog(text)
    CACHED_PROMPTS.append(text)
    full_text = ",".join(CACHED_PROMPTS)
    full_text = full_text.removesuffix("\u6267\u884c\u547d\u4ee4")
    print("The strategy command is: ", full_text)
    handle_strategy_command(prompt=full_text, model=GPTMODEL, gui=GUI_WINDOW)
    CACHED_PROMPTS.clear()


def text_callback_async(text: str, is_from_ui: bool = False):
    text_callback_queue.put((text, is_from_ui))


def handle_keyboard_input():
    print("Keyboard input mode. Type your command and press 'Enter':")
    while True:
        try:
            user_input = input("Enter command: ").strip()
            if user_input.lower() == "exit":
                print("Exiting keyboard input mode.")
                break
            text_callback(user_input)
        except KeyboardInterrupt:
            print("Operation interrupted successfully")
            break


def process_queue():
    while not text_callback_queue.empty():
        try:
            text, is_from_ui = text_callback_queue.get_nowait()
            text_callback(text, is_from_ui)
        except queue.Empty:
            break


def handle_mic_input(**kwargs):
    if kwargs.get('list_devices', False):
        print("Possible devices: ", sr.Microphone.list_microphone_names())
        return

    audio_queue = queue.Queue()
    data_queue = queue.Queue()
    result_queue = queue.Queue()
    
    asr_module = WhisperASR(**kwargs)  # Pass CLI arguments to WhisperASR
    asr_manager = ASRManager(asr_module, audio_queue, data_queue, result_queue)
    audio_listener = AudioListener(asr_manager)
    
    asr_manager.start()
    audio_listener.start()
    
    def process_results():
        while not asr_manager.stop_event.is_set():
            try:
                result = result_queue.get(timeout=0.1)
                if result:
                    text_callback_async(result)
            except queue.Empty:
                continue
    
    result_thread = threading.Thread(target=process_results, daemon=True)
    result_thread.start()
    
    try:
        if GUI_WINDOW:
            GUI_WINDOW.qt_tick_signal.connect(lambda: process_queue())
            GUI_APP.exec_()
        else:
            while True:
                process_queue()
                time.sleep(0.1)
    except KeyboardInterrupt:
        print("Operation interrupted successfully")
    finally:
        # Cleanup
        asr_manager.stop()
        audio_listener.stop()
        if kwargs.get('save_file', False):
            # Handle file saving if needed
            pass


@click.command()
@click.option("--input_mode", default="mic", help="Input mode: 'mic' for microphone, 'keyboard' for keyboard input", type=click.Choice(["mic", "keyboard"]))
@click.option("--model", default="large", help="Model to use", type=click.Choice(["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"]))
@click.option("--gptmodel", default="gpt-4o", help="AI Gen GPT Model to use", type=str)
@click.option("--device", default="mps", help="Device to use", type=click.Choice(["mps"]))
@click.option("--language", default="zh", help="Language model", type=click.Choice(["en", "zh"]))
@click.option("--verbose", default=False, help="Whether to print verbose output", is_flag=True, type=bool)
@click.option("--prompt", default=None, help="Prompt", type=str)
@click.option("--prefix", default=None, help="Prefix", type=str)
@click.option("--ignore_text_without_prefix", default=False, help="Ignore text without prefix", is_flag=True, type=bool)
@click.option("--remove_prefix", default=False, help="Remove prefix", is_flag=True, type=bool)
@click.option("--initial_prompt", default="以下是普通话的句子。", help="Initial prompt", type=str)
@click.option("--enable_post_processing", default=False, help="Enable post processing", is_flag=True, type=bool)
@click.option("--post_prompt", default=None, help="Post prompt", type=str)
@click.option("--energy", default=300, help="Energy level for mic to detect", type=int)
@click.option("--dynamic_energy", default=False, is_flag=True, help="Flag to enable dynamic energy", type=bool)
@click.option("--pause", default=1.2, help="Pause time before entry ends", type=float)
@click.option("--save_file", default=False, help="Flag to save file", is_flag=True, type=bool)
@click.option("--mic_index", default=None, help="Mic index to use", type=int)
@click.option("--list_devices", default=False, help="Flag to list devices", is_flag=True, type=bool)
@click.option("--faster", default=False, help="Use faster_whisper implementation", is_flag=True, type=bool)
@click.option("--remote", default=False, help="Use OpenAI whisper client", is_flag=True, type=bool)
@click.option("--hallucinate_threshold", default=400, help="Raise this to reduce hallucinations. Lower this to activate more often.", type=int)
@click.option("--phrase_time_limit", default=10, help="Phrase time limit", type=int)
@click.option("--logging_level", default="info", help="Logging level", type=click.Choice(["fatal", "error", "warning", "info", "debug"]))
@click.option("--config", default=None, help="JSON filename that contains config", type=str)
@click.option("--gui", is_flag=True, help="Is need a GUI page")
# test new whisper mic
@click.option("--use_new_whisper", is_flag=True, help="Use the new Whisper Mic implementation")
def main(**kwargs):
    global GPTMODEL
    global GUI_WINDOW
    global GUI_APP
    GPTMODEL = kwargs['gptmodel']

    if kwargs['gui']:
        def gui_input_callback(gui, player_input):
            text_callback(player_input, True)
        GUI_APP, GUI_WINDOW = create_ai_assistant_ui_instance()
        GUI_WINDOW.player_dialog_signal.connect(gui_input_callback)
        GUI_WINDOW.ui_exit_signal.connect(lambda: sys.exit(0))
    if kwargs['input_mode'] == "mic":
        handle_mic_input(**kwargs)
    elif kwargs['input_mode'] == "keyboard":
        handle_keyboard_input()


if __name__ == "__main__":
    main()
