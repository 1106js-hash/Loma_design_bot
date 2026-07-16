from app.handlers.max.router import register


START_TEXT = (
    "Выберите удобный формат работы:\n\n"
    "📝 Заполнить подробное ТЗ\n"
    "📩 Или оставить заявку — и мы свяжемся с вами"
)


async def start_handler(ctx):

    if ctx.text.strip().lower() != "/start":
        return False

    await ctx.send(
        ctx.session,
        ctx.chat_type,
        ctx.chat_id,
        ctx.user_id,
        START_TEXT
    )

    return True


register(start_handler)