#!/usr/bin/env python3

import click
import time
import os
import sys
import queue
import threading
from uni_mic.log_manager import LogManager
from typing import Optional

# 在导入其他模块之前初始化 LogManager
LogManager(log_level="info")
logger = LogManager.get_logger()

from uni_mic.gui import create_ai_assistant_ui_instance, AIAssistantUI
from uni_mic.audio_listener import AudioListener
from uni_mic.asr_manager import ASRManager
from uni_mic.asr_module import WhisperASR, FunASRRemoteASR, WhisperAPIASR
from uni_mic.config import AppConfig, ASRConfig, InputConfig, StarterConfig, TTSConfig, ConfigManager
from uni_mic.config import add_options
from uni_mic.ai_factory import AIAssistantFactory
from dataclasses import asdict
from .ui_manager import UIManager

class CLIManager:
    def __init__(self, config: AppConfig):
        self.config = config
        self.ui_manager: Optional[UIManager] = None
        self.gui_window: Optional[AIAssistantUI] = None
        self.gui_app = None

        self.ai_assistant = None
        self.text_callback_queue = queue.Queue()

    def initialize_gui(self):
        """初始化GUI和UIManager"""
        if self.config.starter.gui and not self.gui_app:
            logger.info("Initializing GUI and UIManager...")
            self.gui_app, self.gui_window = create_ai_assistant_ui_instance()
            self.ui_manager = UIManager(self.gui_window)
            logger.info("GUI and UIManager initialized.")

            self.ai_assistant = AIAssistantFactory.create_assistant(self.config, self.ui_manager)
            logger.info("AI Assistant created.")

            self.gui_window.player_dialog_signal.connect(self.gui_input_callback)
            self.gui_window.ui_exit_signal.connect(self.handle_exit)
            self.gui_window.qt_tick_signal.connect(self.process_queue)
            self.gui_window.mic_state_signal.connect(self.handle_mic_toggle)

    def text_callback(self, text: str):
        """处理来自ASR或键盘的文本输入"""
        logger.info(f"Received text input for processing: {repr(text)}")
        if not self.ai_assistant:
            logger.error("AI Assistant not initialized. Cannot handle command.")
            return
            
        try:
            self.ai_assistant.handle_strategy_command(user_input=text, ui_manager=None)
        except Exception as e:
            logger.error(f"Error calling handle_strategy_command: {e}")
            logger.error(traceback.format_exc())
            if self.ui_manager:
                self.ui_manager.post_ai_dialog(f"处理内部错误: {e}", False)

    def gui_input_callback(self, gui_instance, player_input):
        """处理来自GUI输入框的文本"""
        logger.info(f"Received GUI input: {repr(player_input)}")
        self.text_callback(player_input)

    def text_callback_async(self, text: str):
        """异步处理来自ASR的文本输入"""
        self.text_callback_queue.put(text)

    def process_queue(self):
        """处理队列中的ASR文本输入"""
        processed = False
        while not self.text_callback_queue.empty():
            try:
                text = self.text_callback_queue.get_nowait()
                self.text_callback(text)
                processed = True
            except queue.Empty:
                break
            except Exception as e:
                logger.error(f"Error processing text queue: {e}")

    def handle_keyboard_input(self):
        """处理键盘输入 (如果非GUI模式)"""
        if not self.ai_assistant:
            self.ai_assistant = AIAssistantFactory.create_assistant(self.config, None)
            logger.info("AI Assistant created for keyboard mode.")

        logger.info("Starting keyboard input mode")
        while True:
            try:
                user_input = input("Enter command: ").strip()
                if user_input.lower() == "exit":
                    logger.info("Exiting keyboard input mode")
                    break
                self.text_callback(user_input)
            except KeyboardInterrupt:
                logger.info("Keyboard input interrupted by user")
                break
            except EOFError:
                logger.info("EOF detected, exiting keyboard input mode.")
                break

    def handle_mic_input(self):
        """处理麦克风输入 (如果非键盘模式)"""
        logger.info("Initializing microphone input mode")
        audio_queue = queue.Queue()
        result_queue = queue.Queue()
        stop_event = threading.Event()
        self.audio_listener = None

        try:
            if self.config.asr.remote_asr:
                if self.config.asr.remote_type == "whisper":
                    asr_module = WhisperAPIASR(self.config.asr)
                elif self.config.asr.remote_type == "funasr":
                    asr_module = FunASRRemoteASR(self.config.asr)
                else:
                    logger.error(f"Remote ASR type {self.config.asr.remote_type} not supported")
                    return
            else:
                asr_module = WhisperASR(self.config.asr)

            asr_manager = ASRManager(asr_module, audio_queue, result_queue, stop_event)
            self.audio_listener = AudioListener(asr_manager, stop_event)

            logger.info(f"Starting ASR system: {asr_module.__class__.__name__}")
            asr_manager.start()
            self.audio_listener.start()

            def process_results():
                while not asr_manager.stop_event.is_set():
                    try:
                        result = result_queue.get(timeout=0.1)
                        if result:
                            self.text_callback_async(result)
                    except queue.Empty:
                        continue
                    except Exception as e:
                        logger.error(f"Error processing ASR result queue: {e}")

            result_thread = threading.Thread(target=process_results, daemon=True, name="ASRResultProcessor")
            result_thread.start()

            if self.gui_app:
                logger.info("Starting Qt application event loop.")
                exit_code = self.gui_app.exec_()
                logger.info(f"Qt application event loop finished with code {exit_code}.")
            else:
                logger.info("Running in non-GUI mode. Press Ctrl+C to exit.")
                while True:
                    self.process_queue()
                    time.sleep(0.1)

        except KeyboardInterrupt:
            logger.info("Microphone input interrupted by user (Ctrl+C)")
        except Exception as e:
            logger.error(f"Error in mic input handling: {str(e)}")
            logger.error(traceback.format_exc())
        finally:
            logger.info("Shutting down ASR system...")
            stop_event.set()
            if self.audio_listener:
                self.audio_listener.stop()
            logger.info("ASR system shutdown complete.")

    def handle_mic_toggle(self, is_on):
        """Handles mic toggle signal from GUI"""
        if self.audio_listener:
            if is_on:
                logger.info("Resuming audio listening based on GUI toggle.")
                self.audio_listener.resume_listening()
            else:
                logger.info("Pausing audio listening based on GUI toggle.")
                self.audio_listener.pause_listening()
        else:
            logger.warning("Received mic toggle signal, but AudioListener is not initialized.")

    def handle_exit(self, source=None):
        """Handles exit signal"""
        logger.info(f"Exit signal received from {source}. Shutting down.")
        if self.gui_app:
            self.gui_app.quit()
        sys.exit(0)

@click.command()
@add_options(ASRConfig)
@add_options(InputConfig)
@add_options(StarterConfig)
@add_options(TTSConfig)
def main(**kwargs):
    config = AppConfig(
        asr=ASRConfig(**{k: v for k, v in kwargs.items() if k in asdict(ASRConfig())}),
        input=InputConfig(**{k: v for k, v in kwargs.items() if k in asdict(InputConfig())}),
        starter=StarterConfig(**{k: v for k, v in kwargs.items() if k in asdict(StarterConfig())}),
        tts=TTSConfig(**{k: v for k, v in kwargs.items() if k in asdict(TTSConfig())}),
    )
    
    LogManager(
        log_level=config.starter.logging_level,
        debug_mode=config.starter.debug_mode
    )
    
    ConfigManager.set_config(config)

    if config.asr.api_key is None and config.asr.remote_type == "whisper":
        config.asr.api_key = os.getenv("OPENAI_API_KEY")

    cli_manager = CLIManager(config)
    
    if config.starter.gui:
        cli_manager.initialize_gui()
    else:
        cli_manager.ai_assistant = AIAssistantFactory.create_assistant(config, None)
        logger.info("AI Assistant created for non-GUI mode.")

    if config.input.input_mode == "mic":
        cli_manager.handle_mic_input()
    elif config.input.input_mode == "keyboard":
        cli_manager.handle_keyboard_input()
    else:
        logger.error(f"Unsupported input mode: {config.input.input_mode}")

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
