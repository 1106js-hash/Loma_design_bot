from aiogram import Bot, Dispatcher

from app.core.config import BOT_TOKEN
from app.handlers import start, form


async def run_telegram_bot():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(start.router)
    dp.include_router(form.router)

    await dp.start_polling(bot)
