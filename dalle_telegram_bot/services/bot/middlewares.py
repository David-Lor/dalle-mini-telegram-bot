import contextlib
import time
import threading
from threading import Lock
from collections import Counter

import telebot
from telebot.types import Message
from telebot.apihelper import ApiTelegramException

from . import constants
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
        new_value = self._counter[chat_id] - 1
        if new_value <= 0:
            del self._counter[chat_id]
            return
        self._counter[chat_id] = new_value
