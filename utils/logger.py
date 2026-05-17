import os
import sys
import logging
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler
from utils.config import get_config


_LOGGER = None


def setup_logger():
    global _LOGGER
    if _LOGGER is not None:
        return _LOGGER

    log_cfg = get_config("logging")
    level_str = log_cfg.get("level", "INFO").upper()
    level = getattr(logging, level_str, logging.INFO)
    log_file = log_cfg.get("file", "logs/port777.log")
    max_mb = log_cfg.get("max_size_mb", 10)

    log_path = Path(__file__).parent.parent / log_file
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("port777")
    logger.setLevel(level)

    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)-7s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    file_handler = RotatingFileHandler(
        str(log_path), maxBytes=max_mb * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    _LOGGER = logger
    return logger


def get_logger(name=None):
    logger = setup_logger()
    if name:
        return logging.LoggerAdapter(logger, {"prefix": name})
    return logger
