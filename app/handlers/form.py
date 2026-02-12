from aiogram import Router
from aiogram.types import Message, FSInputFile
from aiogram.fsm.context import FSMContext

from app.domain.states import FormState
from app.infrastructure.docx_generator import generate_docx
from app.infrastructure.google_sheets import GoogleSheetsService


router = Router()


@router.message(FormState.name)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Ваш номер телефона:")
    await state.set_state(FormState.phone)


@router.message(FormState.phone)
async def get_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await message.answer("Ваш email:")
    await state.set_state(FormState.email)


@router.message(FormState.email)
async def get_email(message: Message, state: FSMContext):
    await state.update_data(email=message.text)

    data = await state.get_data()

    sheets = GoogleSheetsService()
    sheets.append_start_form(
        user_id=message.from_user.id,
        name=data.get("name"),
        phone=data.get("phone"),
        email=data.get("email"),
    )

    file_path = generate_docx(data, user_id=message.from_user.id)
    doc = FSInputFile(file_path)

    await message.answer_document(
        document=doc,
        caption="Спасибо! Я подготовил документ."
    )

    await state.clear()

