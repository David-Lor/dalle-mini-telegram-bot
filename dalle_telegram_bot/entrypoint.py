from .services.bot import Bot
from .services.dalle import Dalle
from .settings import Settings
from .logger import setup_logger


def main():
    settings = Settings()
    setup_logger(settings)
    dalle = Dalle(
        settings=settings,
    )
    bot = Bot(
        settings=settings,
        dalle=dalle,
    )
    bot.run()
