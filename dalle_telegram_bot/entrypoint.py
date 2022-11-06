import contextlib
import signal
from threading import Event, Lock
from typing import List

from .services.bot import Bot
from .services.common import Setupable
from .services.dalle import Dalle
from .services.mqtt import Mqtt
from .services.redis import Redis
from .settings import Settings
from .logger import logger, setup_logger


class BotBackend:
    settings: Settings
    redis: Redis
    mqtt: Mqtt
    dalle: Dalle
    bot: Bot
    _teardownable_services: List[Setupable]
    _teardown_event: Event
    _teardown_lock: Lock

    def setup(self):
        self.settings = Settings()
        self._teardown_event = Event()
        self._teardown_lock = Lock()
        self._teardownable_services = list()

        self.redis = Redis(
            settings=self.settings,
        )
        self.redis.setup()
        self._teardownable_services.append(self.redis)

        self.mqtt = Mqtt(
            settings=self.settings,
        )
        self.mqtt.setup()
        self._teardownable_services.append(self.mqtt)

        setup_logger(
            settings=self.settings,
            loggers=[self.redis, self.mqtt],
        )
        logger.debug("Initializing app...")

        self.dalle = Dalle(
            settings=self.settings,
        )
        self.bot = Bot(
            settings=self.settings,
            redis=self.redis,
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
                for fn in [self.stop, *[service.teardown for service in self._teardownable_services]]:
                    with contextlib.suppress(Exception):
                        fn()
            finally:
                self._teardown_event.set()

    # TODO Avoid or rename start/stop methods to avoid confusion with setup/teardown

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
