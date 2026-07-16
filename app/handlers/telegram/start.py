from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from app.platforms.telegram.keyboards import start_keyboard
from app.domain.states import FormState

router = Router()

START_TEXT = (
    "Выберите удобный формат работы:\n\n"
    "📝 Заполнить подробное ТЗ\n"
    "📩 Или оставить заявку — и мы свяжемся с вами"
)


@router.message(CommandStart())
async def start(message: Message):
    await message.answer(
        START_TEXT,
        reply_markup=start_keyboard()
    )


# ================================
# КНОПКА "Оставить заявку"
# ================================

@router.callback_query(lambda c: c.data == "start_form")
async def start_form_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Как вас зовут?")
    await state.set_state(FormState.name)
    await callback.answer()
