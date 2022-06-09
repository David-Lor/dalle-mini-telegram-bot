from .services.bot import Bot
from .services.dalle import Dalle
from .settings import Settings


def main():
    settings = Settings()
    dalle = Dalle(
        settings=settings,
    )
    bot = Bot(
        settings=settings,
        dalle=dalle,
    )
    bot.run()
