from .services.bot import Bot
from .services.dalle import Dalle
from .services.redis import Redis
from .settings import Settings
from .logger import logger, setup_logger


def main():
    settings = Settings()

    try:
        redis = Redis(
            settings=settings,
        )
        setup_logger(
            settings=settings,
            loggers=[redis],
        )

        dalle = Dalle(
            settings=settings,
        )
        bot = Bot(
            settings=settings,
            dalle=dalle,
        )
        bot.run()

    except Exception as ex:
        logger.exception("Error in main", ex)
