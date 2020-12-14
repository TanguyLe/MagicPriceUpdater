import functools
import logging
import sys
from contextlib import contextmanager
from logging import config
from pathlib import Path
from typing import Callable


def set_log_conf(log_path: Path) -> None:
    config.dictConfig(
        config={
            "version": 1,
            "handlers": {
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "INFO",
                    "formatter": "default",
                    "filename": log_path / "mpu.log",
                    "mode": "a",
                    "maxBytes": 1048576,
                    "backupCount": 10,
                },
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                    "stream": "ext://sys.stdout",
                },
            },
            "formatters": {
                "default": {
                    "format": "%(asctime)s %(name)-30s %(levelname)-8s %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                }
            },
            "loggers": {
                "": {  # root logger
                    "handlers": ["console", "file"],
                    "level": "INFO",
                    "propagate": False,
                },
                "mpu": {
                    "handlers": ["console", "file"],
                    "level": "INFO",
                    "propagate": False,
                },
                "mpu_strategies": {
                    "handlers": ["console", "file"],
                    "level": "INFO",
                    "propagate": False,
                },
                "__main__": {  # if __name__ == "__main__"
                    "handlers": ["console", "file"],
                    "level": "INFO",
                    "propagate": False,
                },
            },
        }
    )


class StreamToLogger:
    """Fake file-like stream object that redirects writes to a logger instance."""

    def __init__(self, logger, level):
        self.logger = logger
        self.level = level

    def write(self, message):
        message = message.rstrip().lstrip(logging.getLevelName(self.level) + ": ")
        if message not in ["", "\n"]:
            self.logger.log(self.level, message)


@contextmanager
def redirect_stdout_and_err_to_logger(logger: logging.Logger):
    """Redirects stdout and stderr to a logger"""
    previous_stdout = sys.stdout
    previous_stderr = sys.stderr

    sys.stdout = StreamToLogger(logger=logger, level=logging.INFO)
    sys.stderr = StreamToLogger(logger=logger, level=logging.ERROR)

    try:
        yield
    finally:
        sys.stdout = previous_stdout
        sys.stderr = previous_stderr


def log_setup(func: Callable):
    """wrapper to factoriser the logger setup"""

    set_log_conf(log_path=Path.cwd())

    @functools.wraps(wrapped=func)
    def wrapped_func(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapped_func
