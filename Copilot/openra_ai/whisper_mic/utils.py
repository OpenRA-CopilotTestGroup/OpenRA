import logging
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