import requests
import wait4it
import telebot.apihelper

from ...settings import Settings


class TelegramBotAPIRequester:
    def __init__(self, settings: Settings):
        self._settings = settings
        telebot.apihelper.CUSTOM_REQUEST_SENDER = wait4it.wait_for_pass(
            exceptions=[TelegramBotAPITooManyRequestsException],
            retries=self._settings.telegram_bot_ratelimit_retries_limit,
            retries_delay=self._settings.telegram_bot_ratelimit_retry_delay_seconds,
        )(self.request)

    def request(self, *args, **kwargs):
        r = requests.request(*args, **kwargs)
        if self._response_is_toomanyrequests(r):
            raise TelegramBotAPITooManyRequestsException(r.json().get("description"))
        return r

    @staticmethod
    def _response_is_toomanyrequests(response: requests.Response) -> bool:
        return response.status_code == 429


class TelegramBotAPITooManyRequestsException(Exception):
    def __init__(self, message):
        super(message)
