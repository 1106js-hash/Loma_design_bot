from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.domain.tz_states import TZState
from app.services.tz_service import TZService
from app.domain.tz_structure import SECTIONS

router = Router()

tz_service: TZService | None = None

def set_service(service: TZService):
    global tz_service
    tz_service = service

# =====================================================
# ОБЩИЙ ВХОД В TZ
# =====================================================
async def open_tz_menu(user_id: int, message: Message, state: FSMContext):
    result = await tz_service.start(user_id)

    await state.set_state(TZState.choosing_section)
    await state.update_data(answers=result["answers"])

    builder = InlineKeyboardBuilder()
    for key, data in result["sections_progress"].items():
        section = data["section"]
        answered = data["answered"]
        total = data["total"]
        status = " ✅" if answered == total and total > 0 else ""
        builder.button(
            text=f"{section['title']} ({answered}/{total}){status}",
            callback_data=f"tz_section:{key}"
        )
    builder.adjust(1)

    await message.answer(
        f"📝 Анкета проекта\n\n"
        f"📊 Общий прогресс: {result['completed']}/{result['total_sections']} разделов завершено\n\n"
        f"Выберите раздел:",
        reply_markup=builder.as_markup()
    )

# =====================================================
# START TZ
# =====================================================
@router.message(Command("tz"))
async def start_tz(message: Message, state: FSMContext):
    await open_tz_menu(message.from_user.id, message, state)

@router.callback_query(lambda c: c.data == "start_tz")
async def start_tz_from_button(callback: CallbackQuery, state: FSMContext):
    await open_tz_menu(callback.from_user.id, callback.message, state)
    await callback.answer()

# =====================================================
# CHOOSE SECTION
# =====================================================
@router.callback_query(TZState.choosing_section)
async def choose_section(callback: CallbackQuery, state: FSMContext):
    if not callback.data.startswith("tz_section:"):
        return

    section_key = callback.data.split(":")[1]
    await state.update_data(
        current_section=section_key,
        current_question=0,
        multi_selected=[],
        waiting_other_text=False,
        multi_base_answers=[]
    )
    await state.set_state(TZState.answering)
    await callback.answer()
    await send_question(callback.message, state)

# =====================================================
# SEND QUESTION
# =====================================================
async def send_question(message: Message, state: FSMContext):
    data = await state.get_data()
    question_data = tz_service.get_question(
        data["current_section"],
        data["current_question"]
    )

    section = question_data["section"]
    question = question_data["question"]

    text = (
        f"📌 Раздел: {section['title']}\n"
        f"📊 Прогресс: {question_data['current_number']}/{question_data['total_questions']}\n\n"
        f"Вопрос {question_data['current_number']}:\n"
        f"{question['text']}"
    )

    builder = InlineKeyboardBuilder()

    if question["type"] == "single_choice":
        for index, option in enumerate(question["options"]):
            builder.button(
                text=option,
                callback_data=f"tz_answer:{index}"
            )
    elif question["type"] == "multi_choice":
        selected = data.get("multi_selected", [])
        for index, option in enumerate(question["options"]):
            prefix = "✅ " if index in selected else ""
            builder.button(
                text=f"{prefix}{option}",
                callback_data=f"tz_multi:{index}"
            )
        builder.button(text="✔ Готово", callback_data="tz_multi_done")

    builder.button(text="⏭ Пропустить", callback_data="tz_skip")
    builder.adjust(1)

    await message.answer(text, reply_markup=builder.as_markup())

# =====================================================
# HANDLE CALLBACKS
# =====================================================
@router.callback_query(TZState.answering)
async def handle_callbacks(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    section_key = data["current_section"]
    question_index = data["current_question"]
    answers = data.get("answers", {})
    multi_selected = data.get("multi_selected", [])
    question_data = tz_service.get_question(section_key, question_index)
    question = question_data["question"]

    # MULTI CLICK
    if callback.data.startswith("tz_multi:"):
        index = int(callback.data.split(":")[1])
        if index in multi_selected:
            multi_selected.remove(index)
        else:
            multi_selected.append(index)
        await state.update_data(multi_selected=multi_selected)

        builder = InlineKeyboardBuilder()
        for i, opt in enumerate(question["options"]):
            prefix = "✅ " if i in multi_selected else ""
            builder.button(
                text=f"{prefix}{opt}",
                callback_data=f"tz_multi:{i}"
            )
        builder.button(text="✔ Готово", callback_data="tz_multi_done")
        builder.button(text="⏭ Пропустить", callback_data="tz_skip")
        builder.adjust(1)
        await callback.message.edit_reply_markup(
            reply_markup=builder.as_markup()
        )
        await callback.answer()
        return

    # MULTI DONE
    if callback.data == "tz_multi_done":
        selected_options = [question["options"][i] for i in multi_selected]
        await state.update_data(multi_selected=[])

        if "Другое" in selected_options:
            base_answers = [opt for opt in selected_options if opt != "Другое"]
            await state.update_data(
                waiting_other_text=True,
                multi_base_answers=base_answers
            )
            await callback.message.answer("Пожалуйста, уточните ваш вариант:")
            await callback.answer()
            return
        value = ", ".join(selected_options)

    # SINGLE
    elif callback.data.startswith("tz_answer:"):
        index = int(callback.data.split(":")[1])
        value = question["options"][index]

    # SKIP
    elif callback.data == "tz_skip":
        value = "__SKIPPED__"
    else:
        return

    result = await tz_service.process_answer(
        user_id=callback.from_user.id,
        username=callback.from_user.username or "",
        full_name=f"{callback.from_user.first_name or ''} {callback.from_user.last_name or ''}".strip(),
        section_key=section_key,
        question_index=question_index,
        answer_value=value,
        answers=answers,
        skipped_flow=None,
        skipped_index=None
    )
    await state.update_data(answers=result["answers"])
    await callback.answer()

    # =====================================================
    # SECTION FINISHED → выбор следующего действия
    # =====================================================
    if result["mode"] == "section_finished":
        # Порядок разделов
        keys_list = list(SECTIONS.keys())
        current_idx = keys_list.index(section_key)
        next_idx = current_idx + 1 if current_idx + 1 < len(keys_list) else None

        builder = InlineKeyboardBuilder()
        if next_idx is not None:
            next_section_key = keys_list[next_idx]
            builder.button(
                text=f"Заполнить следующий раздел: {SECTIONS[next_section_key]['title']}",
                callback_data=f"tz_section:{next_section_key}"
            )
        builder.button(
            text="Вернуться к списку разделов",
            callback_data="start_tz"
        )
        builder.adjust(1)
        await callback.message.answer(
            "✅ Раздел завершён. Что делать дальше?",
            reply_markup=builder.as_markup()
        )
        await state.set_state(TZState.choosing_section)
        return

    if result["mode"] == "next_question":
        await state.update_data(
            current_section=result["section_key"],
            current_question=result["question_index"],
            multi_selected=[]
        )
        await send_question(callback.message, state)

# =====================================================
# HANDLE TEXT ANSWERS
# =====================================================
@router.message(TZState.answering)
async def handle_answer(message: Message, state: FSMContext):
    data = await state.get_data()

    # текст для "Другое" в multi
    if data.get("waiting_other_text"):
        base = data.get("multi_base_answers", [])
        final_list = base + [f"Другое: {message.text}"]
        final_value = ", ".join(final_list)
        await state.update_data(waiting_other_text=False, multi_base_answers=[])
    else:
        final_value = message.text

    result = await tz_service.process_answer(
        user_id=message.from_user.id,
        username=message.from_user.username or "",
        full_name=f"{message.from_user.first_name or ''} {message.from_user.last_name or ''}".strip(),
        section_key=data["current_section"],
        question_index=data["current_question"],
        answer_value=final_value,
        answers=data.get("answers", {}),
        skipped_flow=None,
        skipped_index=None
    )
    await state.update_data(answers=result["answers"])

    if result["mode"] == "section_finished":
        keys_list = list(SECTIONS.keys())
        current_idx = keys_list.index(data["current_section"])
        next_idx = current_idx + 1 if current_idx + 1 < len(keys_list) else None

        builder = InlineKeyboardBuilder()
        if next_idx is not None:
            next_section_key = keys_list[next_idx]
            builder.button(
                text=f"Заполнить следующий раздел: {SECTIONS[next_section_key]['title']}",
                callback_data=f"tz_section:{next_section_key}"
            )
        builder.button(
            text="Вернуться к списку разделов",
            callback_data="start_tz"
        )
        builder.adjust(1)
        await message.answer(
            "✅ Раздел завершён. Что делать дальше?",
            reply_markup=builder.as_markup()
        )
        await state.set_state(TZState.choosing_section)
        return

    if result["mode"] == "next_question":
        await state.update_data(
            current_section=result["section_key"],
            current_question=result["question_index"]
        )
        await send_question(message, state)
