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

from uni_mic.config import ConfigManager

def time_it(label):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                config = ConfigManager.get_config()  # 运行时动态获取 config
            except ValueError:
                print("[ERROR] config 未初始化，无法获取 debug_mode")
                return func(*args, **kwargs)

            debug_mode = getattr(config.starter, "debug_mode", False)
            
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            elapsed_time = time.perf_counter() - start_time
            
            if debug_mode:
                print(f"[DEBUG] {label} 耗时: {elapsed_time:.2f}秒")
            return result
        return wrapper
    return decorator