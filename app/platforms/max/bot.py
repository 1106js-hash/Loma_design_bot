import aiohttp
import asyncio
from app.core.logger import get_logger
from app.core.config import MAX_TOKEN

MAX_API_URL = "https://api.max.ru/bot"

logger = get_logger("max")


async def send_message(session, chat_id, text):
    url = f"{MAX_API_URL}{MAX_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }

    async with session.post(url, json=payload) as response:
        return await response.text()


async def run_max_bot():
    logger.info("🟢 MAX бот запущен")

    offset = 0

    async with aiohttp.ClientSession() as session:
        while True:
            url = f"{MAX_API_URL}{MAX_TOKEN}/getUpdates?offset={offset}"

            async with session.get(url) as response:
                data = await response.json()

            for update in data.get("result", []):
                offset = update["update_id"] + 1

                message = update.get("message")
                if message:
                    chat_id = message["chat"]["id"]

                    await send_message(
                        session,
                        chat_id,
                        "Привет 👋 Это тест MAX-бота"
                    )

            await asyncio.sleep(1)
