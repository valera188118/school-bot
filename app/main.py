import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.exceptions import TelegramAPIError
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import get_settings
from app.handlers.application import router as application_router
from app.handlers.errors import router as errors_router
from app.handlers.start import router as start_router
from app.repositories.applications import ApplicationsRepository, init_db
from app.services.notifications import NotificationService


logger = logging.getLogger(__name__)


async def setup_bot_commands(bot: Bot) -> None:
    commands = [
        BotCommand(command="start", description="Начать запись на пробный урок"),
        BotCommand(command="cancel", description="Сбросить текущий сценарий"),
        BotCommand(command="chat_id", description="Показать ID текущего чата"),
        BotCommand(command="video_id", description="Получить file_id стартового видео"),
    ]
    try:
        await bot.set_my_commands(commands)
    except TelegramAPIError:
        logger.warning("Could not set bot commands menu", exc_info=True)


async def main() -> None:
    settings = get_settings()
    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    bot_session = (
        AiohttpSession(proxy=settings.telegram_proxy_url)
        if settings.telegram_proxy_url
        else None
    )
    bot = Bot(token=settings.bot_token, session=bot_session)
    dispatcher = Dispatcher(storage=MemoryStorage())

    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    dispatcher["settings"] = settings
    dispatcher["applications_repository"] = ApplicationsRepository(session_factory)
    dispatcher["notification_service"] = NotificationService(
        bot=bot,
        admin_chat_id=settings.admin_chat_id,
    )

    dispatcher.include_routers(start_router, application_router, errors_router)

    try:
        await init_db(engine)
        try:
            await bot.delete_webhook(drop_pending_updates=True)
        except TelegramAPIError:
            logger.warning(
                "Could not delete webhook before polling. Polling will start anyway.",
                exc_info=True,
            )
        await setup_bot_commands(bot)
        logger.info("Bot started in long polling mode")
        await dispatcher.start_polling(
            bot,
            allowed_updates=dispatcher.resolve_used_update_types(),
        )
    finally:
        logger.info("Bot shutdown started")
        await bot.session.close()
        await engine.dispose()
        logger.info("Bot shutdown completed")


if __name__ == "__main__":
    asyncio.run(main())
