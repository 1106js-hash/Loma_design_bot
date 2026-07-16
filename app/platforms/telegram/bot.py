from aiogram import Bot, Dispatcher

from app.core.config import BOT_TOKEN
from app.handlers.telegram import start, form, tz

from app.services.tz_service import TZService
from app.infrastructure.repositories.google_sheets_tz_repository import GoogleSheetsTZRepository


async def run_telegram_bot():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # === Dependency Injection ===
    repository = GoogleSheetsTZRepository()
    tz_service = TZService(repository)

    # Передаём сервис в tz router
    tz.set_service(tz_service)

    dp.include_router(start.router)
    dp.include_router(form.router)
    dp.include_router(tz.router)

    await dp.start_polling(bot)
