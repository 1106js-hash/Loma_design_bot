from app.handlers.max.router import register

# состояния формы
FORM_NAME = "FormState_name"
FORM_PHONE = "FormState_phone"
FORM_EMAIL = "FormState_email"

async def form_handler(ctx):
    # ввод имени
    if ctx.state == FORM_NAME:
        ctx.update_data(name=ctx.text)
        ctx.set_state(FORM_PHONE)
        await ctx.send(ctx.session, ctx.chat_type, ctx.chat_id, ctx.user_id, "Ваш номер телефона:")
        return True

    # ввод телефона
    if ctx.state == FORM_PHONE:
        ctx.update_data(phone=ctx.text)
        ctx.set_state(FORM_EMAIL)
        await ctx.send(ctx.session, ctx.chat_type, ctx.chat_id, ctx.user_id, "Ваш email:")
        return True

    # ввод email
    if ctx.state == FORM_EMAIL:
        ctx.update_data(email=ctx.text)
        data = ctx.get_data()
        # TODO: сюда можно добавить сохранение через GoogleSheetsTZRepository / docx_generator
        ctx.clear_state()
        await ctx.send(ctx.session, ctx.chat_type, ctx.chat_id, ctx.user_id, "Спасибо! Форма принята ✅")
        return True

    return False

# регистрация handler в router
register(form_handler)