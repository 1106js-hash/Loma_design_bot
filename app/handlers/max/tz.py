from app.handlers.max.router import register
from app.services.tz_service import TZService

# состояния TZ
TZ_CHOOSING = "TZ_choosing_section"
TZ_ANSWERING = "TZ_answering"

tz_service: TZService | None = None

def set_service(service: TZService):
    global tz_service
    tz_service = service

async def tz_handler(ctx):
    if ctx.text.strip().lower() == "/tz":
        # старт анкеты
        result = await tz_service.start(ctx.user_id)
        ctx.set_state(TZ_CHOOSING)
        ctx.update_data(answers=result["answers"])
        await ctx.send(ctx.session, ctx.chat_type, ctx.chat_id, ctx.user_id, "📝 Анкета запущена")
        return True

    # выбор раздела
    if ctx.state == TZ_CHOOSING:
        section_key = ctx.text.strip()
        ctx.update_data(current_section=section_key, current_question=0)
        ctx.set_state(TZ_ANSWERING)
        await ctx.send(ctx.session, ctx.chat_type, ctx.chat_id, ctx.user_id, f"Вы выбрали раздел {section_key}")
        return True

    # ответы на вопросы
    if ctx.state == TZ_ANSWERING:
        data = ctx.get_data()
        section_key = data.get("current_section")
        question_index = data.get("current_question", 0)

        question_data = tz_service.get_question(section_key, question_index)
        answer_value = ctx.text

        result = await tz_service.process_answer(
            user_id=ctx.user_id,
            username="",
            full_name=ctx.user_name,
            section_key=section_key,
            question_index=question_index,
            answer_value=answer_value,
            answers=data.get("answers", {}),
            skipped_flow=None,
            skipped_index=None
        )

        ctx.update_data(answers=result["answers"])

        # следующий вопрос
        if result["mode"] == "next_question":
            ctx.update_data(current_section=result["section_key"], current_question=result["question_index"])
            await ctx.send(ctx.session, ctx.chat_type, ctx.chat_id, ctx.user_id, "Следующий вопрос:")
        elif result["mode"] == "section_finished":
            ctx.set_state(TZ_CHOOSING)
            await ctx.send(ctx.session, ctx.chat_type, ctx.chat_id, ctx.user_id, "Раздел завершён ✅")
        return True

    return False

register(tz_handler)