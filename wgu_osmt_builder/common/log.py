# wgu_osmt_builder/log.py
import os
import logging


def configure_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    level = logging.getLevelName((os.getenv("LOG_LEVEL") or "INFO").upper())
    logger.setLevel(level)
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logger.addHandler(h)
    return logger
