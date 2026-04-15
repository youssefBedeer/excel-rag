import logging
import os
from logging.handlers import RotatingFileHandler

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "assets", "logs")

os.makedirs(LOG_DIR, exist_ok=True)

APP_LOG_FILE = os.path.join(LOG_DIR, "app.log")
ERROR_LOG_FILE = os.path.join(LOG_DIR, "error.log")


def get_logger(name: str = __name__) -> logging.Logger:
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%H:%M:%S"
    )

    app_handler = RotatingFileHandler(APP_LOG_FILE, maxBytes=5*1024*1024, backupCount=3)
    app_handler.setLevel(logging.INFO)
    app_handler.setFormatter(formatter)

    error_handler = RotatingFileHandler(ERROR_LOG_FILE, maxBytes=5*1024*1024, backupCount=3)
    error_handler.setLevel(logging.WARNING)
    error_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(app_handler)
    logger.addHandler(error_handler)
    logger.addHandler(console_handler)

    return logger