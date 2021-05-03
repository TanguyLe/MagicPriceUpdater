from logging import config

DATE_FMT = "%Y-%m-%dT%H-%M-%S"


def set_log_conf() -> None:
    config.dictConfig(
        config={
            "version": 1,
            "handlers": {
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "INFO",
                    "formatter": "default",
                    "filename": "mpu.log",
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
                    "datefmt": DATE_FMT,
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
                "dicttoxml": {
                    "handlers": ["console", "file"],
                    "level": "WARN",
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
