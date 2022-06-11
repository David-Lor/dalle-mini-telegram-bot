from .services.bot import Bot
from .services.dalle import Dalle
from .settings import Settings
from .logger import logger, setup_logger


def main():
    settings = Settings()
    setup_logger(settings)

    try:
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
