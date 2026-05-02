import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from sqlalchemy.exc import SQLAlchemyError

from app.keyboards import AGE_RANGES, phone_keyboard
from app.repositories.applications import ApplicationsRepository
from app.services.notifications import NotificationService
from app.utils.phone import normalize_phone


logger = logging.getLogger(__name__)
router = Router(name=__name__)

PHONE_PROMPT = (
    "Спасибо! Остался последний шаг😊\n\n"
    "Укажите ваш номер телефона.\n"
    "Наш администратор отправит вам расписание занятий на ближайшую неделю, "
    "согласует точное время и ответит на все вопросы 🤗"
)
INVALID_PHONE_TEXT = (
    "Похоже, номер указан некорректно. Введите российский номер в формате "
    "+7 999 123-45-67 или 8 (999) 123-45-67."
)
SUCCESS_TEXT = "Спасибо! Заявка принята. Мы скоро свяжемся с вами."
TEMPORARY_ERROR_TEXT = (
    "Не удалось принять заявку из-за временной ошибки. Пожалуйста, попробуйте еще раз."
)


class ApplicationStates(StatesGroup):
    waiting_for_phone = State()


@router.callback_query(F.data.startswith("age:"))
async def process_age(callback: CallbackQuery, state: FSMContext) -> None:
    age_range = callback.data.removeprefix("age:") if callback.data else ""
    if age_range not in AGE_RANGES:
        await callback.answer("Выберите возраст из предложенных вариантов.", show_alert=True)
        return

    await state.update_data(age_range=age_range)
    await state.set_state(ApplicationStates.waiting_for_phone)

    if callback.message:
        await callback.message.answer(PHONE_PROMPT, reply_markup=phone_keyboard())
    await callback.answer()


async def complete_application(
    message: Message,
    state: FSMContext,
    applications_repository: ApplicationsRepository,
    notification_service: NotificationService,
    phone: str,
) -> None:
    normalized_phone = normalize_phone(phone)
    if normalized_phone is None:
        await message.answer(INVALID_PHONE_TEXT)
        return

    state_data = await state.get_data()
    age_range = state_data.get("age_range")
    if age_range not in AGE_RANGES:
        await state.clear()
        await message.answer(
            "Не удалось определить возраст ребенка. Пожалуйста, начните заново с /start.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    user = message.from_user
    try:
        application = await applications_repository.create(
            user_id=user.id if user else message.chat.id,
            username=user.username if user else None,
            full_name=user.full_name if user else None,
            age_range=age_range,
            phone=normalized_phone,
        )
    except SQLAlchemyError:
        logger.exception("Failed to save application")
        await message.answer(TEMPORARY_ERROR_TEXT)
        return

    try:
        await notification_service.send_application(application)
    except TelegramAPIError:
        logger.exception("Failed to send application notification")
        await message.answer(
            "Заявка сохранена, но сейчас не удалось отправить ее администратору. "
            "Пожалуйста, попробуйте позже.",
            reply_markup=ReplyKeyboardRemove(),
        )
        await state.clear()
        return

    await state.clear()
    await message.answer(SUCCESS_TEXT, reply_markup=ReplyKeyboardRemove())


@router.message(ApplicationStates.waiting_for_phone, F.contact)
async def process_contact(
    message: Message,
    state: FSMContext,
    applications_repository: ApplicationsRepository,
    notification_service: NotificationService,
) -> None:
    await complete_application(
        message=message,
        state=state,
        applications_repository=applications_repository,
        notification_service=notification_service,
        phone=message.contact.phone_number,
    )


@router.message(ApplicationStates.waiting_for_phone, F.text)
async def process_phone(
    message: Message,
    state: FSMContext,
    applications_repository: ApplicationsRepository,
    notification_service: NotificationService,
) -> None:
    await complete_application(
        message=message,
        state=state,
        applications_repository=applications_repository,
        notification_service=notification_service,
        phone=message.text or "",
    )


@router.message(ApplicationStates.waiting_for_phone)
async def process_non_text_phone(message: Message) -> None:
    await message.answer(INVALID_PHONE_TEXT)
