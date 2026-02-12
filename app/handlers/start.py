from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart

from app.platforms.telegram.keyboards import start_form_keyboard
from app.domain.states import FormState
from aiogram.fsm.context import FSMContext

router = Router()

START_TEXT = (
    "Данная информация поможет мне учесть все-все ваши пожелания "
    "и сделать для вас самый крутой проект.\n\n"
    "Анкета большая, но обещаю вам — она будет легкой и веселой в заполнении.\n\n"
    "А если какие-то вопросы покажутся сложными и непонятными, "
    "просто пропускайте их, я вам потом с радостью помогу."
)

@router.message(CommandStart())
async def start(message: Message):
    await message.answer(
        START_TEXT,
        reply_markup=start_form_keyboard()
    )

@router.callback_query(lambda c: c.data == "start_form")
async def start_form(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Как вас зовут?")
    await state.set_state(FormState.name)
    await callback.answer()
