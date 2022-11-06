import redis

from .common import Setupable
from .logger_abc import AbstractLogger
from ..settings import Settings
from ..logger import logger


class Redis(Setupable, AbstractLogger):
    _redis: redis.Redis

    def __init__(self, settings: Settings):
        self._settings = settings
        self._redis = redis.StrictRedis(
            host=self._settings.redis_host,
            port=self._settings.redis_port,
            db=self._settings.redis_db,
            **self._get_auth_kwargs(),
        )

    def setup(self):
        logger.debug("Redis initialized")

    def teardown(self):
        logger.debug("Closing Redis...")
        self._redis.close()
        logger.debug("Redis closed")

    def log(self, data: str):
        queue_name = self._settings.redis_logs_queue_name
        if not self._redis or not queue_name:
            return

        # noinspection PyBroadException
        try:
            self._redis.rpush(queue_name, data)
        except Exception:
            # TODO Log errors?
            pass

    def set(self, key: str, value, **kwargs):
        with logger.contextualize(redis_key=key, redis_value=value, redis_set_kwargs=kwargs):
            logger.trace("Redis SET...")

            try:
                r = self._redis.set(key, value, **kwargs)
                logger.bind(redis_result=r).trace("Redis SET OK")
            except Exception as ex:
                logger.error("Redis SET failed")
                raise ex

    def get(self, key: str, default=None):
        with logger.contextualize(redis_key=key):
            logger.trace("Redis GET...")

            try:
                r = self._redis.get(key)
            except Exception as ex:
                logger.error("Redis GET failed")
                raise ex

            if r is not None:
                logger.bind(redis_result=r).trace("Redis GET OK")
            else:
                logger.trace("Redis GET not found")
                r = default

            return r

    def delete(self, *keys: str) -> int:
        with logger.contextualize(redis_keys=keys):
            logger.trace("Redis DELETE...")

            try:
                r = self._redis.delete(*keys)
                logger.bind(redis_result=r).trace("Redis DELETE OK")
                return r
            except Exception as ex:
                logger.error("Redis DELETE failed")
                raise ex

    def _get_auth_kwargs(self):
        kwargs = dict()
        if self._settings.redis_username:
            kwargs["username"] = self._settings.redis_username
        if self._settings.redis_password:
            kwargs["password"] = self._settings.redis_password
        return kwargs
