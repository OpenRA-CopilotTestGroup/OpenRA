#!/usr/bin/env python3

import click
#import torch
import speech_recognition as sr
from typing import Optional
import time

from rafuncs import handle_strategy_command
from whisper_mic import WhisperMic

CACHED_PROMPTS = []
CACHED_TIME = 0.0
LAST_TIME = 0.0

def text_callback(text: str):
    print(repr(text))
    global CACHED_PROMPTS
    global CACHED_TIME
    if text.endswith("执行预设命令"):
        CACHED_PROMPTS.append(text)
        full_text = ",".join(CACHED_PROMPTS)
        full_text = full_text.removesuffix("执行预设命令")
        print("the strategy command is: ", full_text)
        handle_strategy_command(index=0)
        CACHED_PROMPTS.clear()
    elif text.endswith("执行命令"):
        CACHED_PROMPTS.append(text)
        full_text = ",".join(CACHED_PROMPTS)
        full_text = full_text.removesuffix("执行命令")
        print("the strategy command is: ", full_text)
        handle_strategy_command(prompt=full_text)
        CACHED_PROMPTS.clear()
    else:
        # handle_command(text)
        new_time = time.time()
        if CACHED_PROMPTS and new_time - CACHED_TIME > 10.0:
            full_text = ",".join(CACHED_PROMPTS)
            print("the strategy command is: ", full_text)
            handle_strategy_command(prompt=full_text)
            CACHED_PROMPTS.clear()
            CACHED_TIME = new_time
        print("cache ", text)
        CACHED_PROMPTS.append(text)


@click.command()
@click.option("--model", default="large", help="Model to use", type=click.Choice(["tiny","base", "small","medium","large","large-v2","large-v3"]))
@click.option("--device", default="mps", help="Device to use", type=click.Choice(["mps"]))
@click.option("--language", default="zh", help="language model",type=click.Choice(["en", "zh"]))
@click.option("--verbose", default=False, help="Whether to print verbose output", is_flag=True,type=bool)
@click.option("--prompt", default=None, help="prompt", type=str)
@click.option("--prefix", default=None, help="prefix", type=str)
@click.option("--ignore_text_without_prefix", default=False, help="ignore text without prefix", is_flag=True, type=bool)
@click.option("--remove_prefix", default=False, help="remove prefix", is_flag=True, type=bool)
@click.option("--initial_prompt", default="以下是普通话的句子。", help="initial_prompt", type=str)
@click.option("--enable_post_processing", default=False, help="enable post_processing", is_flag=True, type=bool)
@click.option("--post_prompt", default=None, help="post_prompt", type=str)
@click.option("--energy", default=300, help="Energy level for mic to detect", type=int)
@click.option("--dynamic_energy", default=False,is_flag=True, help="Flag to enable dynamic energy", type=bool)
@click.option("--pause", default=1.2, help="Pause time before entry ends", type=float)
@click.option("--save_file",default=False, help="Flag to save file", is_flag=True,type=bool)
@click.option("--mic_index", default=None, help="Mic index to use", type=int)
@click.option("--list_devices",default=False, help="Flag to list devices", is_flag=True,type=bool)
@click.option("--faster",default=False, help="Use faster_whisper implementation", is_flag=True,type=bool)
@click.option("--remote", default=False, help="Use openAI whisper client", is_flag=True, type=bool)
@click.option("--hallucinate_threshold",default=400, help="Raise this to reduce hallucinations.  Lower this to activate more often.", is_flag=True,type=int)
@click.option("--phrase_time_limit", default=10, help="phrase time limit", type=int)
@click.option("--logging_level", default="info", help="logging_level", type=click.Choice(["fatal", "error", "warning", "info", "debug"]))
@click.option("--config", default=None, help="json filename that contains config", type=str)
def main(
    model: str, language: str, verbose: bool, energy: int, pause: float, dynamic_energy: bool, save_file: bool, device: str,
    mic_index: Optional[int], list_devices: bool, faster: bool, hallucinate_threshold: int,
    prompt: Optional[str], prefix: Optional[str], initial_prompt: Optional[str], remote: bool,
    enable_post_processing: bool, post_prompt: Optional[str], ignore_text_without_prefix: bool, remove_prefix: bool,
    phrase_time_limit: int,
    logging_level: str,
    config: Optional[str]
) -> None:
    if list_devices:
        print("Possible devices: ",sr.Microphone.list_microphone_names())
        return
    mic = WhisperMic(
        model=model, language=language, verbose=verbose, energy=energy,
        pause=pause, dynamic_energy=dynamic_energy, save_file=save_file,
        device=device,mic_index=mic_index,
        faster=faster,
        hallucinate_threshold=hallucinate_threshold,
        text_callback=text_callback,
        prompt=prompt,
        prefix=prefix,
        ignore_text_without_prefix=ignore_text_without_prefix,
        remove_prefix=remove_prefix,
        initial_prompt=initial_prompt,
        remote=remote,
        enable_post_processing=enable_post_processing,
        post_prompt=post_prompt,
        phrase_time_limit=phrase_time_limit,
        logging_level=logging_level,
        config=config
    )

    try:
        print(98)
        mic.listen_loop()
        print(99)
    except KeyboardInterrupt:
        print("Operation interrupted successfully")
    finally:
        if save_file:
            mic.file.close()


if __name__ == "__main__":
    main()
