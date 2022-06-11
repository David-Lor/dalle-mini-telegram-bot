from typing import Optional

import telebot
from telebot.types import Message, InputMediaPhoto

from . import constants
from .chatactions import ActionManager
from .middlewares import request_middleware, message_request_middleware, RateLimiter
from ..dalle import Dalle, DalleTemporarilyUnavailableException
from ..dalle.models import DalleResponse
from ...settings import Settings
from ...logger import logger


class Bot:
    def __init__(self, settings: Settings, dalle: Dalle):
        self._settings = settings
        self._dalle = dalle

        self._bot = telebot.TeleBot(
            token=self._settings.telegram_bot_token,
            parse_mode="HTML",
            threaded=True,
            num_threads=settings.telegram_bot_threads,
        )
        self._bot.message_handler(func=lambda message: True)(self._handler_message_entrypoint)

        self._generating_bot_action = ActionManager(
            action=self._settings.command_generate_action,
            bot=self._bot,
            settings=self._settings,
        )
        self._dalle_generate_rate_limiter = RateLimiter(
            limit_per_chat=self._settings.command_generate_chat_concurrent_limit,
        )

    def run(self):
        logger.info("Running bot with Polling")
        self._bot.infinity_polling()

    def _handler_message_entrypoint(self, message: Message):
        with request_middleware(chat_id=message.chat.id):
            with message_request_middleware(bot=self._bot, message=message):
                if self._handler_basic_command(message):
                    return
                self._handler_command_generate(message)

    def _handler_basic_command(self, message: Message) -> bool:
        for cmd, reply_text in constants.BASIC_COMMAND_REPLIES.items():
            if message.text.startswith(cmd):
                logger.info(f"Request is Basic command: {message.text}")

                disable_link_preview = cmd in constants.BASIC_COMMAND_DISABLE_LINK_PREVIEWS
                self._bot.reply_to(
                    message=message,
                    text=reply_text,
                    disable_web_page_preview=disable_link_preview,
                )
                return True

        return False

    def _handler_command_generate(self, message: Message) -> bool:
        if not message.text.startswith(constants.COMMAND_GENERATE):
            return False

        logger.info("Request is Generate command")
        prompt = message.text.replace(constants.COMMAND_GENERATE, "").strip()
        if len(prompt) < 2:
            self._bot.reply_to(message, constants.COMMAND_GENERATE_PROMPT_TOO_SHORT)
            return True

        if not self._dalle_generate_rate_limiter.increase(message.chat.id):
            logger.bind(chat_id=message.chat.id).info("Generate command Request limit exceeded for this chat")
            self._bot.reply_to(message, constants.COMMAND_GENERATE_REPLY_RATELIMIT_EXCEEDED)
            return True

        response: Optional[DalleResponse] = None
        self._generating_bot_action.start(message.chat.id)

        try:
            response = self._dalle.generate(prompt)
        except DalleTemporarilyUnavailableException:
            pass
        finally:
            self._generating_bot_action.stop(message.chat.id)
            self._dalle_generate_rate_limiter.decrease(message.chat.id)

        if not response:
            self._bot.reply_to(message, constants.COMMAND_GENERATE_REPLY_TEMPORARILY_UNAVAILABLE)
            return True

        images_telegram = [InputMediaPhoto(image_bytes) for image_bytes in response.images_bytes]
        images_telegram[0].caption = prompt
        self._bot.send_media_group(
            chat_id=message.chat.id,
            reply_to_message_id=message.message_id,
            media=images_telegram,
        )
        return True
