import contextlib
import time
from collections import Counter
from threading import Lock

import telebot
from telebot.types import Message
from telebot.apihelper import ApiTelegramException

from . import constants
from ...logger import logger
from ...utils import get_uuid


@contextlib.contextmanager
def request_middleware(chat_id: int):
    request_id = get_uuid()
    start = time.time()
    with logger.contextualize(request_id=request_id):
        try:
            logger.bind(chat_id=chat_id).info("Request started")
            yield
        except Exception as ex:
            if isinstance(ex, ApiTelegramException) and ex.description == constants.ERROR_DESCRIPTION_BOT_BLOCKED_BY_USER:
                logger.info("Request completed: Bot blocked by the user")
                return
            logger.exception("Request failed", ex)
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
    def __init__(self, limit_per_chat: int):
        self._limit_per_chat = limit_per_chat
        self._counter = Counter()
        self._counter_lock = Lock()

    def increase(self, chat_id: int) -> bool:
        with self._counter_lock:
            current = self._counter[chat_id]
            if current >= self._limit_per_chat:
                return False

            self._counter[chat_id] = current + 1
            return True

    def decrease(self, chat_id: int):
        current = self._counter[chat_id]
        if current <= 0:
            return
        self._counter[chat_id] = current - 1

    def clean(self):
        with self._counter_lock:
            for k, count in self._counter.items():
                if count <= 0:
                    self._counter.pop(k)
