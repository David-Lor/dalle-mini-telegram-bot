import telebot

from .handlers import setup_bot_handlers
from ...settings import Settings


class Bot:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._bot = telebot.TeleBot(
            token=self._settings.telegram_bot_token,
            parse_mode="HTML"
        )
        setup_bot_handlers(self._bot)

    def run(self):
        self._bot.infinity_polling()
