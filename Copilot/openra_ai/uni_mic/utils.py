import logging
import functools
import time
import os
import json
from typing_extensions import Literal
from rich.logging import RichHandler



def get_logger(name: str, level: Literal["fatal", "error", "info", "warning", "debug"]) -> logging.Logger:
    logging_level = logging._nameToLevel[level.upper()]
    rich_handler = RichHandler(level=logging_level, rich_tracebacks=True, markup=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging_level)

    if not logger.handlers:
        logger.addHandler(rich_handler)

    logger.propagate = False

    return logger

import time
import functools

def time_it(label):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            config = kwargs.get("config", None)
            if config is None:
                from uni_mic.config import AppConfig
                config = AppConfig()
            
            debug_mode = config.starter.debug_mode
            
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            elapsed_time = time.perf_counter() - start_time
            
            if debug_mode:
                print(f"[DEBUG] {label} 耗时: {elapsed_time:.2f}秒")
            return result
        return wrapper
    return decorator

class RatingManager:
    def __init__(self, prompt_dir, jsonl_path):
        self.prompt_dir = prompt_dir
        self.jsonl_path = jsonl_path
        self.ratings = self._load_ratings()

    def _load_ratings(self):
        if not os.path.exists(self.jsonl_path):
            return []
        with open(self.jsonl_path, "r", encoding="utf-8") as file:
            return [json.loads(line) for line in file]

    def _save_ratings(self):
        with open(self.jsonl_path, "w", encoding="utf-8") as file:
            for record in self.ratings:
                file.write(json.dumps(record, ensure_ascii=False) + "\n")

    def get_prompt_status(self):
        prompt_files = [
            f for f in os.listdir(self.prompt_dir) if f.endswith("_player_prompt.txt")
        ]
        rated_files = {record["prompt_file_name"] for record in self.ratings}

        rated = [f for f in prompt_files if f in rated_files]
        unrated = [f for f in prompt_files if f not in rated_files]

        return rated, unrated

    def update_rating(self, prompt_file, score):
        for record in self.ratings:
            if record["prompt_file_name"] == prompt_file:
                record["rate"] = score
                break
        else:
            self.ratings.append({"prompt_file_name": prompt_file, "rate": score})
        self._save_ratings()

    def clean_invalid_entries(self):
        prompt_files = [
            f for f in os.listdir(self.prompt_dir) if f.endswith("_player_prompt.txt")
        ]
        self.ratings = [
            record for record in self.ratings if record["prompt_file_name"] in prompt_files
        ]
        self._save_ratings()