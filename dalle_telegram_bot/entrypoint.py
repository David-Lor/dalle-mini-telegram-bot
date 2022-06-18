import signal
from threading import Event, Lock

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
    _teardown_event: Event
    _teardown_lock: Lock

    def setup(self):
        self.settings = Settings()
        self._teardown_event = Event()
        self._teardown_lock = Lock()

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
        try:
            self.start()
            self.wait_for_end()
        finally:
            self.teardown()

    def wait_for_end(self):
        self._teardown_event.wait()

    def teardown(self, *_):
        with self._teardown_lock:
            if self._teardown_event.is_set():
                return

            try:
                self.stop()
            finally:
                self._teardown_event.set()

    def start(self):
        logger.debug("Running app...")
        self.bot.setup()
        self.bot.start()

    def stop(self):
        logger.info("Stopping app...")
        self.bot.stop()
        logger.info("App stopped!")


def main():
    app = BotBackend()
    app.setup()

    signal.signal(signal.SIGINT, app.teardown)
    signal.signal(signal.SIGTERM, app.teardown)
    app.run()
