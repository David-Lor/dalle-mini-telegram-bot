import telebot
from telebot.types import Message, InputMediaPhoto

from .constants import BasicCommandsReplies, CommandGenerate
from ..dalle import Dalle, DalleTemporarilyUnavailableException
from ...settings import Settings


class Bot:
    def __init__(self, settings: Settings, dalle: Dalle):
        self._settings = settings
        self._dalle = dalle
        self._bot = telebot.TeleBot(
            token=self._settings.telegram_bot_token,
            parse_mode="HTML"
        )
        self._bot.message_handler(func=lambda message: True)(self._handler_message_entrypoint)

    def run(self):
        self._bot.infinity_polling()

    def _handler_message_entrypoint(self, message: Message):
        if self._handler_basic_command(message):
            return
        self._handler_command_generate(message)

    def _handler_basic_command(self, message: Message) -> bool:
        for cmd, reply_text in BasicCommandsReplies.items():
            if message.text.startswith(cmd):
                self._bot.reply_to(
                    message=message,
                    text=reply_text,
                )
                return True
        return False

    def _handler_command_generate(self, message: Message) -> bool:
        if not message.text.startswith(CommandGenerate):
            return False

        prompt = message.text.replace(CommandGenerate, "").strip()
        if len(prompt) < 2:
            # TODO Error message
            return True

        try:
            response = self._dalle.generate(
                prompt=prompt,
            )
        # TODO Error messages
        except DalleTemporarilyUnavailableException:
            self._bot.reply_to(message, "Service temporarily unavailable")
            return True
        except Exception:
            self._bot.reply_to(message, "Unknown error")
            return True

        images_telegram = [InputMediaPhoto(image_bytes) for image_bytes in response.images_bytes]
        self._bot.send_media_group(
            chat_id=message.chat.id,
            reply_to_message_id=message.message_id,
            media=images_telegram,
        )
