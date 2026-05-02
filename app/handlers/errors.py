import logging

from aiogram import Router
from aiogram.exceptions import TelegramAPIError
from aiogram.types import ErrorEvent


logger = logging.getLogger(__name__)
router = Router(name=__name__)


@router.errors()
async def telegram_api_error_handler(event: ErrorEvent) -> bool:
    if isinstance(event.exception, TelegramAPIError):
        logger.exception("Telegram API error while handling update", exc_info=event.exception)
        return True
    return False
