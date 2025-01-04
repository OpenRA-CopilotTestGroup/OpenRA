#!/usr/bin/env python3

import click
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
from .utils import get_logger
from .asr_manager import ASRManager
from .asr_module import WhisperASR, FunASRRemoteASR
from .config import AppConfig, ASRConfig, InputConfig, TextProcessingConfig

logger = get_logger("cli", 'info')

CACHED_PROMPTS = []
CACHED_TIME = 0.0
LAST_TIME = 0.0
GPTMODEL = "gpt-4o"
GUI_WINDOW = None
GUI_APP = None
NO_SAMPLE_PROMPT = False
NO_TEXT_CALLBACK = False
text_callback_queue = queue.Queue()


def text_callback(text: str, is_from_ui: bool = False):
    logger.info(f"Received text input: {repr(text)}")
    print(f"Received text input: {repr(text)}")
    if NO_TEXT_CALLBACK:
        return
    global CACHED_PROMPTS
    global CACHED_TIME
    global GPTMODEL
    if not is_from_ui and GUI_WINDOW:
        GUI_WINDOW.add_player_dialog(text)
    CACHED_PROMPTS.append(text)
    full_text = ",".join(CACHED_PROMPTS)
    full_text = full_text.removesuffix("\u6267\u884c\u547d\u4ee4")
    logger.info(f"Processing strategy command: {full_text}")
    handle_strategy_command(prompt=full_text, model=GPTMODEL,
                            gui=GUI_WINDOW, no_sample_prompt=NO_SAMPLE_PROMPT)
    logger.info("Strategy command processed, clearing cache")
    CACHED_PROMPTS.clear()


def text_callback_async(text: str, is_from_ui: bool = False):
    text_callback_queue.put((text, is_from_ui))


def handle_keyboard_input():
    logger.info("Starting keyboard input mode")
    while True:
        try:
            user_input = input("Enter command: ").strip()
            if user_input.lower() == "exit":
                logger.info("Exiting keyboard input mode")
                break
            text_callback(user_input)
        except KeyboardInterrupt:
            logger.info("Keyboard input interrupted by user")
            break


def process_queue():
    while not text_callback_queue.empty():
        try:
            text, is_from_ui = text_callback_queue.get_nowait()
            text_callback(text, is_from_ui)
        except queue.Empty:
            break


def handle_mic_input(config: AppConfig):
    if config.input.mic_index is None and config.input.list_devices:
        devices = sr.Microphone.list_microphone_names()
        logger.info(f"Available microphone devices: {devices}")
        return

    logger.info("Initializing microphone input mode")
    audio_queue = queue.Queue()
    result_queue = queue.Queue()
    stop_event = threading.Event()

    try:
        asr_module = FunASRRemoteASR() if config.asr.remote else WhisperASR(config.asr)
        asr_manager = ASRManager(
            asr_module, audio_queue, result_queue, stop_event)
        audio_listener = AudioListener(asr_manager, stop_event)

        logger.info(f"Starting ASR system: {asr_module.__class__.__name__}")
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
                GUI_WINDOW.mic_state_signal.connect(lambda is_on: audio_listener.resume_listening(
                ) if is_on else audio_listener.pause_listening())
                GUI_APP.exec_()
            else:
                while True:
                    process_queue()
                    time.sleep(0.1)
        except KeyboardInterrupt:
            logger.info("Microphone input interrupted by user")
            print("Operation interrupted successfully")
        finally:
            logger.info("Shutting down ASR system")
            asr_manager.stop()
            audio_listener.stop()
            if config.input.save_file:
                logger.info("Saving audio file")
                pass
    except Exception as e:
        logger.error(f"Error in microphone input: {str(e)}")


@click.command()
@click.option("--config", default=None, help="JSON filename that contains config", type=str)
@click.option("--input_mode", default="mic", help="Input mode: 'mic' for microphone, 'keyboard' for keyboard input")
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
@click.option("--remote", default=True, help="Use OpenAI whisper client", is_flag=True, type=bool)
@click.option("--hallucinate_threshold", default=400, help="Raise this to reduce hallucinations. Lower this to activate more often.", type=int)
@click.option("--phrase_time_limit", default=10, help="Phrase time limit", type=int)
@click.option("--logging_level", default="info", help="Logging level", type=click.Choice(["fatal", "error", "warning", "info", "debug"]))
@click.option("--gui", is_flag=True, help="Is Need GUI Interface")
@click.option("--gptmodel", default="gpt-4o", help="Text Callback LLM model")
@click.option("--no_sample", is_flag=True, help="Remove Sample code in Prompt")
@click.option("--no_text_callback", is_flag=True, help="Remove Text Callback")
def main(**kwargs):
    config = AppConfig.from_json(kwargs['config']) if kwargs.get(
        'config') else AppConfig.from_dict(kwargs)
    logger.info(f"Starting application with input mode: {
                config.input.input_mode}")
    logger.debug(f"Configuration: {config.to_dict()}")

    global GPTMODEL
    global GUI_WINDOW
    global GUI_APP
    global NO_SAMPLE_PROMPT
    global NO_TEXT_CALLBACK
    GPTMODEL = kwargs['gptmodel']
    NO_SAMPLE_PROMPT = kwargs['no_sample']
    NO_TEXT_CALLBACK = kwargs['no_text_callback']

    if config.gui:
        logger.info("Initializing GUI mode")

        def gui_input_callback(gui, player_input):
            text_callback(player_input, True)
        GUI_APP, GUI_WINDOW = create_ai_assistant_ui_instance()
        GUI_WINDOW.player_dialog_signal.connect(gui_input_callback)
        GUI_WINDOW.ui_exit_signal.connect(lambda: sys.exit(0))

    if config.input.input_mode == "mic":
        handle_mic_input(config)
    elif config.input.input_mode == "keyboard":
        handle_keyboard_input()


if __name__ == "__main__":
    logger.info("Application starting")
    main()
