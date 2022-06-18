import contextlib
import threading
from threading import Lock
from typing import Dict, Union
from types import ModuleType

import requests
import wait4it
import telebot.apihelper

from . import constants
from ...settings import Settings
from ...logger import logger


class TelegramBotAPIRequester:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._sessions: Dict[str, requests.Session] = dict()
        self._sessions_lock = Lock()

        telebot.apihelper.CUSTOM_REQUEST_SENDER = wait4it.wait_for_pass(
            exceptions=[TelegramBotAPITooManyRequestsException],
            retries=self._settings.telegram_bot_ratelimit_retries_limit,
            retries_delay=self._settings.telegram_bot_ratelimit_retry_delay_seconds,
        )(self.request)

    def request(self, *args, **kwargs):
        requester = self.get_session()
        r = requester.request(*args, **kwargs)

        if self._response_is_toomanyrequests(r):
            raise TelegramBotAPITooManyRequestsException(r.json().get("description"))
        return r

    def get_session(self) -> Union[requests.Session, ModuleType]:
        if not self._settings.telegram_bot_api_sessions_enabled:
            return requests

        thread_name = threading.current_thread().name
        if not thread_name.startswith(constants.PYTELEGRAMBOTAPI_THREAD_WORKER_STARTNAME):
            return requests

        with self._sessions_lock:
            session = self._sessions.get(thread_name)

            if not session:
                session = requests.Session()
                self._sessions[thread_name] = session
                logger.bind(thread_name=thread_name).trace("New requests.Session created")

        return session

    def teardown(self):
        logger.bind(sessions_count=len(self._sessions)).debug("Closing TelegramBotAPI request sessions...")
        closed_count = 0
        for k in list(self._sessions.keys()):
            with contextlib.suppress(Exception):
                self._sessions.pop(k).close()
                closed_count += 1

        logger.bind(closed_sessions_count=closed_count).info("Closed TelegramBotAPI request sessions")

    @staticmethod
    def _response_is_toomanyrequests(response: requests.Response) -> bool:
        return response.status_code == 429


class TelegramBotAPITooManyRequestsException(Exception):
    def __init__(self, message):
        super(message)
