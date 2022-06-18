import sys
import contextlib
from typing import Collection, Optional

from loguru import logger
# noinspection PyProtectedMember
from loguru._logger import context as loguru_context

from .settings import Settings
from .services.logger_abc import AbstractLogger

__all__ = ("logger", "setup_logger", "get_request_id")


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


def get_request_id() -> Optional[str]:
    """Return the current Request ID, if defined, being used by the logger"""
    with contextlib.suppress(Exception):
        context: dict = loguru_context.get()
        return context.get("request_id")
