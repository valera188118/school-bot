import html
import logging
from datetime import UTC
from zoneinfo import ZoneInfo

from aiogram import Bot
from aiogram.enums import ParseMode

from app.repositories.applications import Application


logger = logging.getLogger(__name__)
MOSCOW_TZ = ZoneInfo("Europe/Moscow")


class NotificationService:
    def __init__(self, *, bot: Bot, admin_chat_id: int) -> None:
        self._bot = bot
        self._admin_chat_id = admin_chat_id

    async def send_application(self, application: Application) -> None:
        created_at = application.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=UTC)
        moscow_created_at = created_at.astimezone(MOSCOW_TZ)

        username = f"@{application.username}" if application.username else "не указан"
        text = (
            "Новая заявка на обучение\n\n"
            f"Дата: {html.escape(moscow_created_at.strftime('%d.%m.%Y %H:%M'))} МСК\n"
            f"Возраст ребенка: {html.escape(application.age_range)}\n"
            f"Телефон: <code>{html.escape(application.phone)}</code>\n"
            f"Имя в Telegram: {html.escape(application.full_name or 'не указано')}\n"
            f"Username: {html.escape(username)}\n"
            f"Telegram ID: <code>{application.user_id}</code>"
        )

        logger.info("Sending application %s to admin chat %s", application.id, self._admin_chat_id)
        await self._bot.send_message(
            chat_id=self._admin_chat_id,
            text=text,
            parse_mode=ParseMode.HTML,
        )
