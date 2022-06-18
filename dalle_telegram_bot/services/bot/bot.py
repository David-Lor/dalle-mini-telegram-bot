import contextlib
from threading import Thread
from typing import Optional

import telebot
from telebot.types import Message, InputMediaPhoto, BotCommand

from . import constants
from .requester import TelegramBotAPIRequester
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
        self._polling_thread = None

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
            timeout=self._settings.dalle_generation_timeout_seconds,
        )
        self._dalle_generate_rate_limiter = RateLimiter(
            limit_per_chat=self._settings.command_generate_chat_concurrent_limit,
        )

        self._requester = None
        if self._settings.telegram_bot_ratelimit_retry:
            self._requester = TelegramBotAPIRequester(
                settings=self._settings,
            )

    def setup(self):
        """Perform initial setup (delete webhook, set commands)"""
        if self._settings.telegram_bot_delete_webhook:
            self.delete_webhook()
        if self._settings.telegram_bot_set_commands:
            self.set_commands()

    def start(self):
        """Run the bot in background, by starting a thread running the `run` method."""
        if self._polling_thread:
            return

        if self._requester:
            self._requester.start()

        self._polling_thread = Thread(
            target=self.run,
            name="TelegramBotPolling",
            daemon=True,
        )
        self._polling_thread.start()

    def run(self):
        """Run the bot in foreground. Perform initial setup (delete webhook, set commands)"""
        logger.info("Running bot with Polling")
        self._bot.infinity_polling(logger_level=None)

    def stop(self, graceful_shutdown: Optional[bool] = None):
        """Stop the bot execution.
        :param graceful_shutdown: if True, wait for pending requests to finalize (but stop accepting new requests).
                                  If false, stop inmediately. If None (default), use the configured setting.
        """
        if graceful_shutdown is None:
            graceful_shutdown = self._settings.telegram_bot_graceful_shutdown

        if graceful_shutdown:
            self._stop_gracefully()
        else:
            self._stop_force()

        if self._requester:
            self._requester.teardown()

    def set_commands(self):
        logger.debug("Setting bot commands...")
        self._bot.set_my_commands([
            BotCommand(command=k, description=v)
            for k, v in constants.COMMANDS_HELP.items()
        ])
        logger.info("Bot commands set")

    def delete_webhook(self):
        logger.info("Deleting bot webhook...")
        self._bot.delete_webhook()
        logger.info("Webhook deleted")

    def _stop_force(self):
        logger.info("Stopping bot polling (force-stop)...")
        self._bot.stop_polling()
        logger.info("Bot stopped")

    def _stop_gracefully(self):
        logger.info("Stopping bot gracefully (waiting for pending requests to end, not accepting new requests)...")
        # stop_bot() waits for remaining requests to complete
        self._bot.stop_bot()
        logger.info("Bot stopped")

    def _handler_message_entrypoint(self, message: Message):
        with request_middleware(chat_id=message.chat.id):
            with message_request_middleware(bot=self._bot, message=message):
                if self._handler_basic_command(message):
                    return
                if self._handler_command_generate(message):
                    return

    def _handler_basic_command(self, message: Message) -> bool:
        for cmd, reply_text in constants.BASIC_COMMAND_REPLIES.items():
            if message.text.startswith(cmd):
                logger.bind(command=cmd).info("Request is Basic command")

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

        logger.bind(cmd=constants.COMMAND_GENERATE).info("Request is Generate command")
        prompt = self.__command_generate_get_prompt(message)
        if not prompt:
            return True

        if not self._dalle_generate_rate_limiter.increase(message.chat.id):
            logger.bind(chat_id=message.chat.id).info("Generate command Request limit exceeded for this chat")
            self._bot.reply_to(message, constants.COMMAND_GENERATE_REPLY_RATELIMIT_EXCEEDED)
            return True

        generating_reply_message = self._bot.reply_to(message, constants.COMMAND_GENERATE_REPLY_GENERATING)
        self._generating_bot_action.start(message.chat.id)

        response: Optional[DalleResponse] = None
        try:
            response = self._dalle.generate(prompt)
        except DalleTemporarilyUnavailableException:
            pass
        finally:
            self._generating_bot_action.stop(message.chat.id)
            self._dalle_generate_rate_limiter.decrease(message.chat.id)
            with contextlib.suppress(Exception):
                self._bot.delete_message(
                    chat_id=generating_reply_message.chat.id,
                    message_id=generating_reply_message.message_id
                )

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

    def __command_generate_get_prompt(self, message: Message) -> Optional[str]:
        """Get the prompt text from a /generate command and return it.
        If the prompt is invalid, replies to the user and returns None."""
        prompt = message.text.replace(constants.COMMAND_GENERATE, "").strip()
        prompt_length = len(prompt)
        min_length = self._settings.command_generate_prompt_length_min
        max_length = self._settings.command_generate_prompt_length_max

        with logger.contextualize(prompt_length=prompt_length):
            if prompt_length < min_length:
                logger.debug("Generate command prompt too short")
                self._bot.reply_to(message, constants.COMMAND_GENERATE_PROMPT_TOO_SHORT.format(characters=min_length))
                return None

            if prompt_length > max_length:
                logger.debug("Generate command prompt too long")
                self._bot.reply_to(message, constants.COMMAND_GENERATE_PROMPT_TOO_LONG.format(characters=max_length))
                return None

            logger.debug("Generate command prompt is valid")
            return prompt
