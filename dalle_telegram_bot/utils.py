import shortuuid
from telebot.apihelper import ApiTelegramException

__all__ = ("get_uuid", "exception_is_bot_blocked_by_user")


def get_uuid() -> str:
    return shortuuid.uuid()


def exception_is_bot_blocked_by_user(ex: Exception) -> bool:
    return isinstance(ex, ApiTelegramException) and ex.description == "Forbidden: bot was blocked by the user"
