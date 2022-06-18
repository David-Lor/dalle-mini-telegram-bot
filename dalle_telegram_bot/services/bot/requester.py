import threading
from threading import Lock
from typing import Dict

import requests
import wait4it
import telebot.apihelper

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
        if self._settings.telegram_bot_api_sessions_enabled:
            session = self.get_session()
            r = session.request(*args, **kwargs)
        else:
            r = requests.request(*args, **kwargs)

        if self._response_is_toomanyrequests(r):
            raise TelegramBotAPITooManyRequestsException(r.json().get("description"))
        return r

    def get_session(self) -> requests.Session:
        thread_name = threading.current_thread().name
        with self._sessions_lock:
            session = self._sessions.get(thread_name)

            if not session:
                session = requests.Session()
                self._sessions[thread_name] = session
                logger.bind(thread_name=thread_name).trace("New requests.Session created")

        return session

    @staticmethod
    def _response_is_toomanyrequests(response: requests.Response) -> bool:
        return response.status_code == 429


class TelegramBotAPITooManyRequestsException(Exception):
    def __init__(self, message):
        super(message)
