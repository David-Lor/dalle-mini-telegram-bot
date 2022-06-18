import redis

from .logger_abc import AbstractLogger
from ..settings import Settings


class Redis(AbstractLogger):
    def __init__(self, settings: Settings):
        self._settings = settings
        self._redis = None
        if not self._settings.redis_host:
            return

        self._redis = redis.Redis(
            host=self._settings.redis_host,
            port=self._settings.redis_port,
            db=self._settings.redis_db,
        )

    def log(self, data: str):
        if not self._redis or not self._settings.redis_logs_queue_name:
            return

        self._redis.rpush(
            self._settings.redis_logs_queue_name,
            data,
        )
