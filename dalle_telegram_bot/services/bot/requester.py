import threading
from threading import Lock
from typing import Dict, Any

import requests
import wait4it
import telebot.apihelper

from ...settings import Settings
from ...logger import logger


class TelegramBotAPIRequester:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._sessions: Dict[Any, requests.Session] = dict()
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
        thread_id = threading.get_ident()
        with self._sessions_lock:
            session = self._sessions.get(thread_id)

            if not session:
                session = requests.Session()
                self._sessions[thread_id] = session
                logger.bind(thread_id=thread_id).trace("New requests.Session created")

        return session

    @staticmethod
    def _response_is_toomanyrequests(response: requests.Response) -> bool:
        return response.status_code == 429


class TelegramBotAPITooManyRequestsException(Exception):
    def __init__(self, message):
        super(message)
