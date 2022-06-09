from telebot import TeleBot
from telebot.types import Message, InputMediaPhoto

from ..dalle import Dalle, DalleTemporarilyUnavailableException


def setup_bot_handlers(bot: TeleBot, dalle: Dalle):
    @bot.message_handler(commands=["start"])
    def _handler_cmd_start(message: Message):
        bot.reply_to(message, "Hello there!")

    @bot.message_handler(commands=["help"])
    def _handler_cmd_help(message: Message):
        bot.reply_to(message, "Help me!")

    @bot.message_handler(commands=["generate"])
    def _handler_cmd_generate(message: Message):
        prompt = message.text.replace("/generate", "").strip()
        if len(prompt) < 2:
            # TODO Error message
            return

        try:
            response = dalle.generate(
                prompt=prompt,
            )
        # TODO Error messages
        except DalleTemporarilyUnavailableException:
            bot.reply_to(message, "Service temporarily unavailable")
            return
        except Exception:
            bot.reply_to(message, "Unknown error")
            return

        images_telegram = [InputMediaPhoto(image_bytes) for image_bytes in response.images_bytes]
        bot.send_media_group(
            chat_id=message.chat.id,
            reply_to_message_id=message.message_id,
            media=images_telegram,
        )
