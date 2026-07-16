from app.handlers.max.router import register


def make_buttons(options):
    return [
        {
            "type": "inline_keyboard",
            "payload": {
                "buttons": [
                    [
                        {
                            "type": "callback",
                            "text": opt,
                            "payload": opt
                        }
                        for opt in options
                    ]
                ]
            }
        }
    ]


async def morning_handler(ctx):

    text = (ctx.text or "").strip().lower()
    state = ctx.state
    data = ctx.get_data()

    # =========================
    # START
    # =========================
    if text == "/morning":
        ctx.set_state("morning_day")
        ctx.update_data()

        await ctx.send(
            ctx.session,
            ctx.chat_type,
            ctx.chat_id,
            ctx.user_id,
            "🗓 За какой день внести данные?",
            attachments=make_buttons(["сегодня", "вчера", "позавчера"])
        )
        return True

    # =========================
    # DAY
    # =========================
    if state == "morning_day":

        if text == "липолиз":
            ctx.clear_state()
            await ctx.send(ctx.session, ctx.chat_type, ctx.chat_id, ctx.user_id, "Сессия завершена 💤")
            return True

        if text not in ["сегодня", "вчера", "позавчера"]:
            await ctx.send(ctx.session, ctx.chat_type, ctx.chat_id, ctx.user_id, "Выбери вариант из кнопок 👇")
            return True

        offset_map = {
            "сегодня": 0,
            "вчера": 1,
            "позавчера": 2
        }

        ctx.update_data(morning_day_offset=offset_map[text])
        ctx.set_state("morning_sleep")

        await ctx.send(
            ctx.session,
            ctx.chat_type,
            ctx.chat_id,
            ctx.user_id,
            "🌅 Доброе утро! Сколько часов ты спал(а)? (формат ч:мм, например 7:45)"
        )
        return True

    # =========================
    # SLEEP
    # =========================
    if state == "morning_sleep":

        if text == "липолиз":
            ctx.clear_state()
            await ctx.send(ctx.session, ctx.chat_type, ctx.chat_id, ctx.user_id, "Сессия завершена 💤")
            return True

        if ":" not in text:
            await ctx.send(ctx.session, ctx.chat_type, ctx.chat_id, ctx.user_id, "Пожалуйста, введи корректно, например 7:45 ⏰")
            return True

        ctx.update_data(sleep=text)
        ctx.set_state("morning_mood")

        await ctx.send(
            ctx.session,
            ctx.chat_type,
            ctx.chat_id,
            ctx.user_id,
            "Как настроение? 😊",
            attachments=make_buttons(["😀", "😐", "😪", "😠"])
        )
        return True

    # =========================
    # MOOD
    # =========================
    if state == "morning_mood":

        if text == "липолиз":
            ctx.clear_state()
            await ctx.send(ctx.session, ctx.chat_type, ctx.chat_id, ctx.user_id, "Сессия завершена 💤")
            return True

        if text not in ["😀", "😐", "😪", "😠"]:
            await ctx.send(ctx.session, ctx.chat_type, ctx.chat_id, ctx.user_id, "Выбери одно из предложенных настроений 👇")
            return True

        ctx.update_data(mood=text)
        ctx.set_state("morning_weight")

        await ctx.send(
            ctx.session,
            ctx.chat_type,
            ctx.chat_id,
            ctx.user_id,
            "⚖️ Введи свой вес (кг):",
            attachments=make_buttons(["не взвешивался"])
        )
        return True

    # =========================
    # WEIGHT
    # =========================
    if state == "morning_weight":

        if text == "липолиз":
            ctx.clear_state()
            await ctx.send(ctx.session, ctx.chat_type, ctx.chat_id, ctx.user_id, "Сессия завершена 💤")
            return True

        if text == "не взвешивался":
            weight = ""
        else:
            try:
                weight = float(text.replace(",", "."))
            except:
                await ctx.send(ctx.session, ctx.chat_type, ctx.chat_id, ctx.user_id, "Введи число, например 86 или 86.5 ⚖️")
                return True

        data = ctx.get_data()

        # просто вывод (без сервисов)
        await ctx.send(
            ctx.session,
            ctx.chat_type,
            ctx.chat_id,
            ctx.user_id,
            f"✅ Данные:\nСон: {data.get('sleep')}\nНастроение: {data.get('mood')}\nВес: {weight}"
        )

        ctx.clear_state()
        return True

    return False


register(morning_handler)