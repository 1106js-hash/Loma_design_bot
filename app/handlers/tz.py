from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.domain.tz_states import TZState
from app.domain.tz_structure import SECTIONS
from app.infrastructure.google_sheets import GoogleSheetsService

router = Router()


# =======================
# СТАРТ АНКЕТЫ
# =======================

@router.message(Command("tz"))
async def start_tz(message: Message, state: FSMContext):
    await state.set_state(TZState.choosing_section)

    # 🔥 Восстанавливаем ответы из Google Sheets
    sheets = GoogleSheetsService()
    restored_answers = sheets.get_user_answers(
        user_id=message.from_user.id
    )

    await state.update_data(answers=restored_answers)

    completed, total_sections = await calculate_sections_progress(state)

    builder = InlineKeyboardBuilder()

    data = await state.get_data()
    answers = data.get("answers", {})

    for key, section in SECTIONS.items():
        answered, total = calculate_section_progress(answers, section)

        status = " ✅" if answered == total and total > 0 else ""

        builder.button(
            text=f"{section['title']} ({answered}/{total}){status}",
            callback_data=f"tz_section:{key}"
        )

    builder.button(
        text="✏ Заполнить пропущенные",
        callback_data="tz_fill_skipped"
    )

    builder.adjust(1)

    await message.answer(
        f"📝 Анкета проекта\n\n"
        f"📊 Общий прогресс: {completed}/{total_sections} разделов завершено\n\n"
        f"Выберите раздел:",
        reply_markup=builder.as_markup()
    )




# =======================
# ВЫБОР РАЗДЕЛА
# =======================

@router.callback_query(TZState.choosing_section)
async def choose_section(callback: CallbackQuery, state: FSMContext):

    data = await state.get_data()
    answers = data.get("answers", {})

    # =====================
    # ЗАПОЛНИТЬ ПРОПУЩЕННЫЕ
    # =====================
    if callback.data == "tz_fill_skipped":

        sheets = GoogleSheetsService()
        skipped_questions = sheets.get_skipped_questions(
            user_id=callback.from_user.id
        )

        if not skipped_questions:
            await callback.answer()
            await callback.message.answer("✅ Нет пропущенных вопросов")
            return

        # сохраняем список пропусков в FSM
        await state.update_data(
            skipped_flow=skipped_questions,
            skipped_index=0
        )

        section_key, question_id = skipped_questions[0]

        question_index = next(
            i for i, q in enumerate(SECTIONS[section_key]["questions"])
            if q["id"] == question_id
        )

        await state.update_data(
            current_section=section_key,
            current_question=question_index,
            multi_selected=[]
        )

        await state.set_state(TZState.answering)
        await callback.answer()

        await send_question(callback.message, state)
        return


    # =====================
    # ОБЫЧНЫЙ ВЫБОР РАЗДЕЛА
    # =====================
    if not callback.data.startswith("tz_section:"):
        return

    section_key = callback.data.split(":")[1]

    await state.update_data(
        current_section=section_key,
        current_question=0,
        multi_selected=[]
    )

    await state.set_state(TZState.answering)
    await callback.answer()

    await send_question(callback.message, state)



# =======================
# ОТПРАВКА ВОПРОСА
# =======================

async def send_question(message: Message, state: FSMContext):
    data = await state.get_data()

    section_key = data["current_section"]
    question_index = data["current_question"]

    section = SECTIONS[section_key]
    question = section["questions"][question_index]

    total_questions = len(section["questions"])
    current_number = question_index + 1

    text = (
        f"📌 Раздел: {section['title']}\n"
        f"📊 Прогресс: {current_number}/{total_questions}\n\n"
        f"Вопрос {current_number}:\n"
        f"{question['text']}"
)


    builder = InlineKeyboardBuilder()

    # SINGLE CHOICE
    if question["type"] == "single_choice":
        for option in question["options"]:
            builder.button(
                text=option,
                callback_data=f"tz_answer:{option}"
            )

    # MULTI CHOICE
    elif question["type"] == "multi_choice":
        selected = data.get("multi_selected", [])

        for option in question["options"]:
            prefix = "✅ " if option in selected else ""
            builder.button(
                text=f"{prefix}{option}",
                callback_data=f"tz_multi:{option}"
            )

        builder.button(
            text="✔ Готово",
            callback_data="tz_multi_done"
        )

    # Кнопка пропустить всегда
    builder.button(
        text="⏭ Пропустить",
        callback_data="tz_skip"
    )

    builder.adjust(1)

    await message.answer(text, reply_markup=builder.as_markup())


@router.callback_query(TZState.answering)
async def handle_callbacks(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    section_key = data["current_section"]
    question_index = data["current_question"]

    section = SECTIONS[section_key]
    question = section["questions"][question_index]

    callback_data = callback.data
    answers = data.get("answers", {})

    # =====================
    # MULTI TOGGLE
    # =====================
    if callback_data.startswith("tz_multi:"):
        option = callback_data.replace("tz_multi:", "")
        selected = data.get("multi_selected", [])

        if option in selected:
            selected.remove(option)
        else:
            selected.append(option)

        await state.update_data(multi_selected=selected)

        await callback.answer()

        await callback.message.edit_reply_markup(
            reply_markup=await rebuild_multi_keyboard(state, question)
        )
        return

    # =====================
    # СОХРАНЕНИЕ ОТВЕТА
    # =====================

    if callback_data == "tz_multi_done":
        selected = data.get("multi_selected", [])
        answers[str(question["id"])] = ", ".join(selected)

        await state.update_data(
            answers=answers,
            multi_selected=[]
        )

    elif callback_data.startswith("tz_answer:"):
        value = callback_data.replace("tz_answer:", "")
        answers[str(question["id"])] = value

        await state.update_data(
            answers=answers
        )

    elif callback_data == "tz_skip":
        answers[str(question["id"])] = "__SKIPPED__"

        await state.update_data(
            answers=answers
        )

    else:
        return


    # сохраняем в Google Sheets
    sheets = GoogleSheetsService()
    sheets.upsert_tz_answer(
        user_id=callback.from_user.id,
        section=section_key,
        question_id=question["id"],
        answer=answers[str(question["id"])]
    )

    await state.update_data(answers=answers)

    data = await state.get_data()

    await callback.answer()


    # =====================
    # ЕСЛИ РЕЖИМ ПРОПУСКОВ
    # =====================
    if data.get("skipped_flow"):
        skipped_flow = data["skipped_flow"]
        skipped_index = data["skipped_index"] + 1

        if skipped_index < len(skipped_flow):
            section_key, question_id = skipped_flow[skipped_index]

            question_index = next(
                i for i, q in enumerate(SECTIONS[section_key]["questions"])
                if q["id"] == question_id
            )

            await state.update_data(
                skipped_index=skipped_index,
                current_section=section_key,
                current_question=question_index,
                multi_selected=[]
            )

            await send_question(callback.message, state)
        else:
            await state.update_data(
                skipped_flow=None,
                skipped_index=None
            )
            await callback.message.answer("✅ Все пропущенные заполнены")
            await state.set_state(TZState.choosing_section)

    # =====================
    # ОБЫЧНЫЙ РЕЖИМ
    # =====================
    else:
        if question_index + 1 < len(section["questions"]):
            await state.update_data(
                current_question=question_index + 1,
                multi_selected=[]
            )
            await send_question(callback.message, state)
        else:
            await callback.message.answer("✅ Раздел завершён")
            await state.set_state(TZState.choosing_section)

# =======================
# TEXT ОТВЕТЫ
# =======================

@router.message(TZState.answering)
async def handle_answer(message: Message, state: FSMContext):
    data = await state.get_data()

    section_key = data["current_section"]
    question_index = data["current_question"]

    section = SECTIONS[section_key]
    question = section["questions"][question_index]

    if question["type"] != "text":
        return

    answers = data.get("answers", {})
    answers[str(question["id"])] = message.text

    sheets = GoogleSheetsService()
    sheets.upsert_tz_answer(
        user_id=message.from_user.id,
        section=section_key,
        question_id=question["id"],
        answer=message.text
    )

    await state.update_data(answers=answers)

    data = await state.get_data()

    # =====================
    # ЕСЛИ РЕЖИМ ПРОПУСКОВ
    # =====================
    if data.get("skipped_flow"):
        skipped_flow = data["skipped_flow"]
        skipped_index = data["skipped_index"] + 1

        if skipped_index < len(skipped_flow):
            next_section, question_id = skipped_flow[skipped_index]

            next_question_index = next(
                i for i, q in enumerate(SECTIONS[next_section]["questions"])
                if q["id"] == question_id
            )

            await state.update_data(
                skipped_index=skipped_index,
                current_section=next_section,
                current_question=next_question_index,
                multi_selected=[]
            )

            await send_question(message, state)

        else:
            await state.update_data(
                skipped_flow=None,
                skipped_index=None
            )

            await message.answer("✅ Все пропущенные заполнены")
            await state.set_state(TZState.choosing_section)

    # =====================
    # ОБЫЧНЫЙ РЕЖИМ
    # =====================
    else:
        if question_index + 1 < len(section["questions"]):
            await state.update_data(
                current_question=question_index + 1,
                multi_selected=[]
            )
            await send_question(message, state)
        else:
            await message.answer("✅ Раздел завершён")
            await state.set_state(TZState.choosing_section)


# =======================
# ОБЩИЙ ПРОГРЕСС РАЗДЕЛОВ
# =======================

async def calculate_sections_progress(state: FSMContext):
    data = await state.get_data()
    answers = data.get("answers", {})

    completed = 0

    for key, section in SECTIONS.items():
        section_complete = True

        for question in section["questions"]:
            qid = str(question["id"])

            # нет ответа
            if qid not in answers:
                section_complete = False
                break

            # был пропуск
            if answers[qid] == "__SKIPPED__":
                section_complete = False
                break

        if section_complete:
            completed += 1

    return completed, len(SECTIONS)

def calculate_section_progress(answers: dict, section: dict):
    total = len(section["questions"])
    answered = 0

    for question in section["questions"]:
        qid = str(question["id"])
        if qid in answers and answers[qid] != "__SKIPPED__":
            answered += 1

    return answered, total

# =======================
# ПЕРЕРИСОВКА MULTI
# =======================

async def rebuild_multi_keyboard(state: FSMContext, question):
    data = await state.get_data()
    selected = data.get("multi_selected", [])

    builder = InlineKeyboardBuilder()

    for option in question["options"]:
        prefix = "✅ " if option in selected else ""
        builder.button(
            text=f"{prefix}{option}",
            callback_data=f"tz_multi:{option}"
        )

    builder.button(
        text="✔ Готово", callback_data="tz_multi_done")
    builder.button(
        text="⏭ Пропустить", callback_data="tz_skip")

    builder.adjust(1)

    return builder.as_markup()

