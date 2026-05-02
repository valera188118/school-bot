import logging

from aiogram import Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from app.config import Settings
from app.keyboards import age_keyboard


router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.message(CommandStart())
async def command_start(message: Message, state: FSMContext, settings: Settings) -> None:
    await state.clear()
    if settings.start_video_file_id:
        try:
            await message.answer_video(settings.start_video_file_id)
        except TelegramAPIError:
            logger.exception("Failed to send start video")
    await message.answer(settings.school_text, reply_markup=age_keyboard())


@router.message(Command("cancel"))
async def command_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "Сценарий сброшен. Чтобы начать заново, отправьте /start.",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(Command("chat_id"))
async def command_chat_id(message: Message) -> None:
    await message.answer(f"ID текущего чата: {message.chat.id}")


@router.message(Command("video_id"))
async def command_video_id(message: Message) -> None:
    if not message.video:
        await message.answer("Отправьте видео вместе с подписью /video_id.")
        return

    await message.answer(f"START_VIDEO_FILE_ID={message.video.file_id}")
