import sys
from typing import Collection

from loguru import logger

from .settings import Settings
from .services.logger_abc import AbstractLogger

__all__ = ("logger", "setup_logger")


LoggerFormat = "<green>{time:YY-MM-DD HH:mm:ss}</green> | " \
               "<level>{level}</level> | " \
               "{function}: <level>{message}</level> | " \
               "{extra} {exception}"


def setup_logger(settings: Settings, loggers: Collection[AbstractLogger]):
    logger.remove()
    logger.add(sys.stderr, level=settings.log_level.upper(), format=LoggerFormat)

    for custom_logger in (loggers or []):
        logger.add(
            custom_logger.log,
            level="TRACE",
            enqueue=True,
            serialize=True,  # record provided as JSON string to the handler
        )
