import telebot

from .handlers import setup_bot_handlers
from ..dalle import Dalle
from ...settings import Settings


class Bot:
    def __init__(self, settings: Settings, dalle: Dalle):
        self._settings = settings
        self._dalle = dalle
        self._bot = telebot.TeleBot(
            token=self._settings.telegram_bot_token,
            parse_mode="HTML"
        )
        setup_bot_handlers(
            bot=self._bot,
            dalle=self._dalle,
        )

    def run(self):
        self._bot.infinity_polling()
