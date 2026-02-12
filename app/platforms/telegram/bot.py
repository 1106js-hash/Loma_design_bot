from aiogram import Bot, Dispatcher

from app.core.config import BOT_TOKEN
from app.handlers import start, form, tz


async def run_telegram_bot():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(start.router)
    dp.include_router(form.router)
    dp.include_router(tz.router)


    await dp.start_polling(bot)
