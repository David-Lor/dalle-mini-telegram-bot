import contextlib
import threading
import time
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
        self._sessions_last_timestamp: Dict[str, float] = dict()
        self._sessions_lock = threading.Lock()
        self._cleanup_thread = None

        telebot.apihelper.CUSTOM_REQUEST_SENDER = wait4it.wait_for_pass(
            exceptions=[TelegramBotAPITooManyRequestsException],  # TODO Add other Request errors?
            retries=self._settings.telegram_bot_ratelimit_retries_limit,
            retries_delay=self._settings.telegram_bot_ratelimit_retry_delay_seconds,
        )(self.request)

    def start(self):
        """Start the cleanup thread"""
        if self._cleanup_thread:
            return

        self._cleanup_thread = threading.Thread(
            target=self._cleanup_worker,
            name="TelegramBotAPIRequester-cleanup",
            daemon=True,
        ).start()

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
            self._sessions_last_timestamp[thread_name] = time.time()
            session = self._sessions.get(thread_name)

            if not session:
                session = requests.Session()
                self._sessions[thread_name] = session
                logger.bind(thread_name=thread_name).trace("New requests.Session created")

        return session

    def teardown(self):
        with logger.contextualize(sessions_count=len(self._sessions)):
            logger.debug("Closing TelegramBotAPI request sessions...")
            for k in list(self._sessions.keys()):
                self.stop_session(k)

            logger.info("Closed TelegramBotAPI request sessions")

    def stop_session(self, thread_name: str):
        with self._sessions_lock:
            session = self._sessions.pop(thread_name, None)
            self._sessions_last_timestamp.pop(thread_name, None)

        if not session:
            return

        with contextlib.suppress(Exception):
            logger.bind(thread_name=thread_name).trace("Stopping requests.Session")
            session.close()

    def _cleanup_worker(self):
        logger.debug("Start of TelegramBotAPIRequester requests.Sessions cleanup worker")
        while True:
            with self._sessions_lock:
                sessions_timestamps = tuple(self._sessions_last_timestamp.items())

            now = time.time()
            for session_threadname, session_timestamp in sessions_timestamps:
                if (now - session_timestamp) >= self._settings.telegram_bot_api_sessions_ttl_seconds:
                    self.stop_session(session_threadname)

            time.sleep(30)

    @staticmethod
    def _response_is_toomanyrequests(response: requests.Response) -> bool:
        return response.status_code == 429


class TelegramBotAPITooManyRequestsException(Exception):
    pass
