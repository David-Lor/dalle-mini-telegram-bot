import signal
from threading import Thread

from .services.bot import Bot
from .services.dalle import Dalle
from .services.redis import Redis
from .settings import Settings
from .logger import logger, setup_logger


class BotBackend:
    settings: Settings
    redis: Redis
    dalle: Dalle
    bot: Bot

    def setup(self):
        self.settings = Settings()

        self.redis = Redis(
            settings=self.settings,
        )
        setup_logger(
            settings=self.settings,
            loggers=[self.redis],
        )
        logger.debug("Initializing app...")

        self.dalle = Dalle(
            settings=self.settings,
        )
        self.bot = Bot(
            settings=self.settings,
            dalle=self.dalle,
        )
        logger.debug("App initialized")

    def run(self):
        logger.debug("Running app...")
        self.bot.run()

    def teardown(self, *_):
        logger.info("Stopping app...")
        self.bot.stop()
        logger.info("App stopped!")


def main():
    app = BotBackend()
    app.setup()

    Thread(
        target=app.run,
        daemon=True,
    ).start()
    signal.signal(signal.SIGINT, app.teardown)
    signal.signal(signal.SIGTERM, app.teardown)
    signal.pause()
