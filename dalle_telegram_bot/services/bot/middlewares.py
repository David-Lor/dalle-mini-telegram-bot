import contextlib
import time
import threading
from typing import Optional

import telebot
from telebot.types import Message
from telebot.apihelper import ApiTelegramException

from . import constants
from ..redis import Redis
from ...logger import logger
from ...utils import get_uuid, exception_is_bot_blocked_by_user


@contextlib.contextmanager
def request_middleware(chat_id: int):
    request_id = get_uuid()
    start = time.time()

    with logger.contextualize(request_id=request_id):
        try:
            logger.bind(
                chat_id=chat_id,
                thread_name=threading.current_thread().name
            ).info("Request started")
            yield

        except Exception as ex:
            request_duration = round(time.time() - start, 4)
            with logger.contextualize(request_duration=request_duration):
                if exception_is_bot_blocked_by_user(ex):
                    logger.info("Request completed: Bot blocked by the user")
                    return

                if isinstance(ex, ApiTelegramException):
                    logger.bind(error_json=ex.result_json).error("Request failed")
                    return

                logger.exception("Request failed")

        else:
            request_duration = round(time.time() - start, 4)
            logger.bind(request_duration=request_duration).info("Request completed")


@contextlib.contextmanager
def message_request_middleware(bot: telebot.TeleBot, message: Message):
    try:
        yield
    except Exception as ex:
        bot.reply_to(message, constants.UNKNOWN_ERROR_REPLY)
        raise ex


class RateLimiter:
    """Service used for limiting the amount of concurrent requests per chat.
    Uses Redis for keeping the counter values.
    Call the methods `increase` and `decrease` when handling a rate-limited request, for updating the values
    and validate whether the request can be performed.
    """

    def __init__(
            self,
            redis: Redis,
            limit_per_chat: int,
            redis_key_prefix: str,
            key_ttl_seconds: Optional[float] = None,
    ):
        self._redis = redis
        self._limit_per_chat = limit_per_chat
        self._redis_key_prefix = redis_key_prefix
        self._key_ttl_milliseconds = None
        if key_ttl_seconds:
            self._key_ttl_milliseconds = int(key_ttl_seconds * 1000)

    # TODO Implement Redis locks on increase/decrease

    def increase(self, chat_id: int) -> bool:
        """To be called when a request starts for a chat.
        If the new value would exceed the `limit_per_chat`, return False and do nothing.
        Otherwise, increase the counter +1 and return True.
        """
        value = self.get_value(chat_id)

        value += 1
        if value > self._limit_per_chat:
            return False

        self.set_value(chat_id, value)
        return True

    def decrease(self, chat_id: int):
        """To be called when a request ends for a chat. Decreases -1 the amount of requests for the chat.
        """
        value = self.get_value(chat_id) - 1
        self.set_value(chat_id, value)

    def get_value(self, chat_id: int):
        """Get the current amount of requests on the counter for a chat.
        If the counter is not set or its value is negative, return 0.
        """
        key = self._get_key(chat_id)
        read_value = self._redis.get(key)
        value = int(read_value) if read_value else 0
        value = value if value >= 0 else 0
        logger.bind(chat_id=chat_id, redis_key=key, redis_value=read_value, counter_value=value).\
            debug("RateLimiter get value")
        return value

    def set_value(self, chat_id: int, value: int):
        """Set the current amount of requests on the counter for a chat.
        If the new value is negative, set it as 0.
        If the value to be set is 0, remove the key.
        """
        key = self._get_key(chat_id)
        if value < 0:
            value = 0

        with logger.contextualize(chat_id=chat_id, redis_key=key, counter_value=value):
            if value > 0:
                logger.debug("RateLimiter set value")
                self._redis.set(key, value, px=self._key_ttl_milliseconds)
            else:
                logger.debug("RateLimiter delete value")
                self._redis.delete(key)

    def _get_key(self, chat_id: int) -> str:
        return f"{self._redis_key_prefix}{chat_id}"
