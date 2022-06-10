from time import sleep
from typing import Optional

import telebot
from telebot.types import Message, InputMediaPhoto

from .chatactions import ActionManager
from .constants import BASIC_COMMAND_REPLIES, COMMAND_GENERATE
from ..dalle import Dalle, DalleTemporarilyUnavailableException
from ..dalle.models import DalleResponse
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

        self._typing_actions = ActionManager(
            action=self._settings.command_generate_action,
            bot=self._bot,
            settings=self._settings,
        )

    def run(self):
        self._bot.infinity_polling()

    def _handler_message_entrypoint(self, message: Message):
        if self._handler_basic_command(message):
            return
        self._handler_command_generate(message)

    def _handler_basic_command(self, message: Message) -> bool:
        for cmd, reply_text in BASIC_COMMAND_REPLIES.items():
            if message.text.startswith(cmd):
                self._bot.reply_to(
                    message=message,
                    text=reply_text,
                )
                return True
        return False

    def _handler_command_generate(self, message: Message) -> bool:
        if not message.text.startswith(COMMAND_GENERATE):
            return False

        prompt = message.text.replace(COMMAND_GENERATE, "").strip()
        if len(prompt) < 2:
            # TODO Error message
            return True

        response: Optional[DalleResponse] = None
        self.start_typing_action(message.chat.id)

        while True:
            try:
                response = self._dalle.generate(
                    prompt=prompt,
                )
            except DalleTemporarilyUnavailableException:
                # TODO Max retries; move loop logic to Dalle service
                sleep(5)
            except Exception:
                self._bot.reply_to(message, "Unknown error")
                break
            else:
                break

        self.stop_typing_action(message.chat.id)
        if not response:
            return True

        images_telegram = [InputMediaPhoto(image_bytes) for image_bytes in response.images_bytes]
        images_telegram[0].caption = prompt
        self._bot.send_media_group(
            chat_id=message.chat.id,
            reply_to_message_id=message.message_id,
            media=images_telegram,
        )
        return True

    def start_typing_action(self, chat_id: int):
        self._typing_actions.start(chat_id)

    def stop_typing_action(self, chat_id: int):
        self._typing_actions.stop(chat_id)
