#!/usr/bin/env python3

import click
import time
import os
import sys
import queue
import threading
from uni_mic.log_manager import LogManager

# 在导入其他模块之前初始化 LogManager
LogManager(log_level="info")
logger = LogManager.get_logger()

from uni_mic.gui import create_ai_assistant_ui_instance
from uni_mic.audio_listener import AudioListener
from uni_mic.asr_manager import ASRManager
from uni_mic.asr_module import WhisperASR, FunASRRemoteASR, WhisperAPIASR
from uni_mic.config import AppConfig, ASRConfig, InputConfig, StarterConfig, ConfigManager
from uni_mic.config import add_options
from uni_mic.ai_factory import AIAssistantFactory
from dataclasses import asdict

class CLIManager:
    def __init__(self, config: AppConfig):
        self.config = config
        self.ai_assistant = AIAssistantFactory.create_assistant(config)
        self.text_callback_queue = queue.Queue()
        self.gui_window = None
        self.gui_app = None

    def text_callback(self, text: str, is_from_ui: bool = False):
        """处理文本输入的回调函数"""
        logger.info(f"Received text input: {repr(text)}")
        

            
        # 直接使用AI Assistant处理命令
        self.ai_assistant.handle_strategy_command(
            user_input=text,
            gui=self.gui_window
        )

    def text_callback_async(self, text: str, is_from_ui: bool = False):
        """异步处理文本输入"""
        self.text_callback_queue.put((text, is_from_ui))

    def process_queue(self):
        """处理队列中的文本输入"""
        while not self.text_callback_queue.empty():
            try:
                text, is_from_ui = self.text_callback_queue.get_nowait()
                self.text_callback(text, is_from_ui)
            except queue.Empty:
                break

    def handle_keyboard_input(self):
        """处理键盘输入"""
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

    def handle_mic_input(self):
        """处理麦克风输入"""
        logger.info("Initializing microphone input mode")
        audio_queue = queue.Queue()
        result_queue = queue.Queue()
        stop_event = threading.Event()

        try:
            # 初始化ASR模块
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
            audio_listener = AudioListener(asr_manager, stop_event)

            logger.info(f"Starting ASR system: {asr_module.__class__.__name__}")
            asr_manager.start()
            audio_listener.start()

            def process_results():
                while not asr_manager.stop_event.is_set():
                    try:
                        result = result_queue.get(timeout=0.1)
                        if result:
                            self.text_callback_async(result)
                    except queue.Empty:
                        continue

            result_thread = threading.Thread(target=process_results, daemon=True)
            result_thread.start()

            try:
                if self.gui_window:
                    self.gui_window.qt_tick_signal.connect(lambda: self.process_queue())
                    self.gui_window.mic_state_signal.connect(
                        lambda is_on: audio_listener.resume_listening() if is_on else audio_listener.pause_listening()
                    )
                    self.gui_app.exec_()
                else:
                    while True:
                        self.process_queue()
                        time.sleep(0.1)
            except KeyboardInterrupt:
                logger.info("Microphone input interrupted by user")
            finally:
                logger.info("Shutting down ASR system")
                asr_manager.stop()
                audio_listener.stop()

        except Exception as e:
            logger.error(f"Error in mic input handling: {str(e)}")

    def initialize_gui(self):
        """初始化GUI"""
        if self.config.starter.gui:
            logger.info("Initializing GUI mode")
            self.gui_app, self.gui_window = create_ai_assistant_ui_instance()
            
            def gui_input_callback(gui, player_input):
                self.text_callback(player_input, True)
                
            self.gui_window.player_dialog_signal.connect(gui_input_callback)
            self.gui_window.ui_exit_signal.connect(lambda: sys.exit(0))

@click.command()
@add_options(ASRConfig)
@add_options(InputConfig)
@add_options(StarterConfig)
def main(**kwargs):
    # 创建配置
    config = AppConfig(
        asr=ASRConfig(**{k: v for k, v in kwargs.items() if k in asdict(ASRConfig())}),
        input=InputConfig(**{k: v for k, v in kwargs.items() if k in asdict(InputConfig())}),
        starter=StarterConfig(**{k: v for k, v in kwargs.items() if k in asdict(StarterConfig())})
    )
    
    # 根据配置更新 LogManager
    LogManager(
        log_level=config.starter.logging_level,
        debug_mode=config.starter.debug_mode
    )
    
    # 设置配置管理器
    ConfigManager.set_config(config)

    # 设置API密钥
    if config.asr.api_key is None and config.asr.remote_type == "whisper":
        config.asr.api_key = os.getenv("OPENAI_API_KEY")

    # 创建CLI管理器
    cli_manager = CLIManager(config)
    
    # 初始化GUI（如果需要）
    if config.starter.gui:
        cli_manager.initialize_gui()

    # 根据输入模式处理输入
    if config.input.input_mode == "mic":
        cli_manager.handle_mic_input()
    elif config.input.input_mode == "keyboard":
        cli_manager.handle_keyboard_input()

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
