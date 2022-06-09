from time import sleep
from threading import Thread, Event
from typing import Dict, Optional

import telebot
from telebot.types import Message, InputMediaPhoto

from .constants import BasicCommandsReplies, CommandGenerate
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

        self._typingaction_chatids_events: Dict[int, Event] = dict()

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

        response: Optional[DalleResponse] = None
        self.start_typing_action(message.chat.id)

        while True:
            try:
                response = self._dalle.generate(
                    prompt=prompt,
                )
            except DalleTemporarilyUnavailableException:
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
        self._bot.send_media_group(
            chat_id=message.chat.id,
            reply_to_message_id=message.message_id,
            media=images_telegram,
        )
        return True

    def start_typing_action(self, chat_id: int):
        # TODO Compatibilize when a chat_id sends multiple requests
        event = Event()
        thread = Thread(
            target=self._typing_action_worker,
            kwargs=dict(
                chat_id=chat_id,
                event=event,
            ),
            name=f"TypingActionWorker-{chat_id}",
            daemon=True
        )
        self._typingaction_chatids_events[chat_id] = event
        thread.start()

    def stop_typing_action(self, chat_id: int):
        event = self._typingaction_chatids_events.get(chat_id)
        if event:
            event.set()

    def _typing_action_worker(self, chat_id: int, event: Event):
        while not event.is_set():
            self._bot.send_chat_action(
                chat_id=chat_id,
                action="typing",
            )
            event.wait(4.5)
