import redis

from .logger_abc import AbstractLogger
from ..settings import Settings


class Redis(AbstractLogger):
    def __init__(self, settings: Settings):
        self._settings = settings
        self._redis = None
        if not self._settings.redis_host:
            return

        self._redis = redis.StrictRedis(
            host=self._settings.redis_host,
            port=self._settings.redis_port,
            db=self._settings.redis_db,
            **self._get_auth_kwargs(),
        )

    def log(self, data: str):
        if not self._redis or not self._settings.redis_logs_queue_name:
            return

        try:
            self._redis.rpush(
                self._settings.redis_logs_queue_name,
                data,
            )
        except Exception:
            # TODO Log errors?
            pass

    def _get_auth_kwargs(self):
        kwargs = dict()
        if self._settings.redis_username:
            kwargs["username"] = self._settings.redis_username
        if self._settings.redis_password:
            kwargs["password"] = self._settings.redis_password
        return kwargs
