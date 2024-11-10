#!/usr/bin/env python3

import click
# import torch
import speech_recognition as sr
from typing import Optional
import time
import os

from .rafuncs import handle_strategy_command
from .whisper_mic import WhisperMic

CACHED_PROMPTS = []
CACHED_TIME = 0.0
LAST_TIME = 0.0
GPTMODEL = "gpt-4o"
def text_callback(text: str):
    print(repr(text))
    global CACHED_PROMPTS
    global CACHED_TIME
    global GPTMODEL
    CACHED_PROMPTS.append(text)
    full_text = ",".join(CACHED_PROMPTS)
    full_text = full_text.removesuffix("\u6267\u884c\u547d\u4ee4")
    print("The strategy command is: ", full_text)
    handle_strategy_command(prompt=full_text, model=GPTMODEL)
    CACHED_PROMPTS.clear()

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

def handle_mic_input(**kwargs):
    if kwargs.get('list_devices', False):
        print("Possible devices: ", sr.Microphone.list_microphone_names())
        return

    mic = WhisperMic(**kwargs, text_callback=text_callback)

    try:
        mic.listen_loop()
    except KeyboardInterrupt:
        print("Operation interrupted successfully")
    finally:
        if kwargs.get('save_file', False):
            mic.file.close()

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
def main(**kwargs):
    global GPTMODEL
    GPTMODEL = kwargs['gptmodel']

    if kwargs['input_mode'] == "mic":
        handle_mic_input(**kwargs)
    elif kwargs['input_mode'] == "keyboard":
        handle_keyboard_input()

if __name__ == "__main__":
    main()
