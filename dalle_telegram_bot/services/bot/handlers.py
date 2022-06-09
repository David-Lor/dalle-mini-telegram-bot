from telebot import TeleBot
from telebot.types import Message


def setup_bot_handlers(bot: TeleBot):
    @bot.message_handler(commands=["start"])
    def _handler_cmd_start(message: Message):
        bot.reply_to(message, "Hello there!")

    @bot.message_handler(commands=["help"])
    def _handler_cmd_help(message: Message):
        bot.reply_to(message, "Help me!")
