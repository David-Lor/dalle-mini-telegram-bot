import redis

from .logger_abc import AbstractLogger
from ..settings import Settings


class Redis(AbstractLogger):
    redis: redis.Redis

    def __init__(self, settings: Settings):
        self.settings = settings
        self.redis = redis.StrictRedis(
            host=self.settings.redis_host,
            port=self.settings.redis_port,
            db=self.settings.redis_db,
            **self._get_auth_kwargs(),
        )

    def log(self, data: str):
        if not self.redis or not self.settings.redis_logs_queue_name:
            return

        try:
            self.redis.rpush(
                self.settings.redis_logs_queue_name,
                data,
            )
        except Exception:
            # TODO Log errors?
            pass

    def _get_auth_kwargs(self):
        kwargs = dict()
        if self.settings.redis_username:
            kwargs["username"] = self.settings.redis_username
        if self.settings.redis_password:
            kwargs["password"] = self.settings.redis_password
        return kwargs
