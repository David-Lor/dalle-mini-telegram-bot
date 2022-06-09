from .services.bot import Bot
from .settings import Settings


def main():
    settings = Settings()
    bot = Bot(settings)
    bot.run()
