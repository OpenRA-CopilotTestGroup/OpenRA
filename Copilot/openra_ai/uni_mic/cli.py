#!/usr/bin/env python3

import click
import time
import os
import sys
import queue
import threading
import asyncio

from uni_mic.rafuncs import handle_strategy_command, RAFunctions
from uni_mic.gui import create_ai_assistant_ui_instance
from uni_mic.audio_listener import AudioListener
from uni_mic.utils import get_logger
from uni_mic.asr_manager import ASRManager
from uni_mic.asr_module import WhisperASR, FunASRRemoteASR, WhisperAPIASR
from uni_mic.config import AppConfig, ASRConfig, InputConfig, StarterConfig, ConfigManager
from uni_mic.config import add_options
from dataclasses import asdict

logger = get_logger("cli", 'info')

CACHED_PROMPTS = []
CACHED_TIME = 0.0
LAST_TIME = 0.0
STARTERCONFIG = None
GUI_WINDOW = None
GUI_APP = None
NO_SAMPLE_PROMPT = False
NO_TEXT_CALLBACK = False
text_callback_queue = queue.Queue()


async def text_callback(text: str, ra_functions: RAFunctions, is_from_ui: bool = False):
    if not is_from_ui and ra_functions.gui:
        ra_functions.gui.add_player_dialog(text)
    await ra_functions.handle_strategy_command(text)


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
    # i think it's no use
    # if config.input.mic_index is None and config.input.list_devices:
    #     devices = sr.Microphone.list_microphone_names()
    #     logger.info(f"Available microphone devices: {devices}")
    #     return

    logger.info("Initializing microphone input mode")
    audio_queue = queue.Queue()
    result_queue = queue.Queue()
    stop_event = threading.Event()

    try:
        if config.asr.remote_asr:
            if config.asr.remote_type == "whisper":
                asr_module = WhisperAPIASR(config.asr)
            elif config.asr.remote_type == "funasr":
                asr_module = FunASRRemoteASR(config.asr)
            else:
                logger.error(
                    f"Remote ASR type {config.asr.remote_type} not supported")
                return
        else:
            asr_module = WhisperASR(config.asr)
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
        logger.error(f"Error: {str(e)}")


@click.command()
@add_options(ASRConfig)
@add_options(InputConfig)
@add_options(StarterConfig)
def main(**kwargs):
    config = AppConfig(
        asr=ASRConfig(**{k: v for k, v in kwargs.items() if k in asdict(ASRConfig())}),
        input=InputConfig(**{k: v for k, v in kwargs.items() if k in asdict(InputConfig())}),
        starter=StarterConfig(**{k: v for k, v in kwargs.items() if k in asdict(StarterConfig())})
    )
    
    gui_window = None
    if config.starter.gui:
        app, gui_window = create_ai_assistant_ui_instance()
    
    ra_functions = RAFunctions(config.starter, gui_window)
    
    if gui_window:
        gui_window.player_dialog_signal.connect(
            lambda gui, text: asyncio.create_task(text_callback(text, ra_functions, True))
        )

    ConfigManager.set_config(config)

    global GUI_WINDOW
    global GUI_APP
    global NO_SAMPLE_PROMPT
    global NO_TEXT_CALLBACK
    global STARTERCONFIG

    STARTERCONFIG = config.starter
    NO_TEXT_CALLBACK = config.starter.no_text_callback


    if config.asr.api_key is None and config.asr.remote_type == "whisper":
        config.asr.api_key = os.getenv("OPENAI_API_KEY")

    if config.input.input_mode == "mic":
        handle_mic_input(config)
    elif config.input.input_mode == "keyboard":
        handle_keyboard_input()

import traceback
def handle_exception(exc_type, exc_value, exc_traceback):
    print("捕获到异常:")
    traceback.print_exception(exc_type, exc_value, exc_traceback)
    sys.exit(1)

sys.excepthook = handle_exception

import atexit

def on_exit():
    print("程序正在退出...")
    print("".join(traceback.format_stack()))


atexit.register(on_exit)

if __name__ == "__main__":
    logger.info("Application starting")
    main()
