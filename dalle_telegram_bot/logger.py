import sys

from loguru import logger

from .settings import Settings

__all__ = ("logger", "setup_logger")


LoggerFormat = "<green>{time:YY-MM-DD HH:mm:ss}</green> | " \
               "<level>{level}</level> | " \
               "{function}: <level>{message}</level> | " \
               "{extra} {exception}"


def setup_logger(settings: Settings):
    logger.remove()
    logger.add(sys.stderr, level=settings.log_level.upper(), format=LoggerFormat)
