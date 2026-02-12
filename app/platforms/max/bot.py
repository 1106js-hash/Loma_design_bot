import aiohttp
import asyncio
import ssl
from app.core.logger import get_logger
from app.core.config import MAX_TOKEN

MAX_API_URL = "https://platform-api.max.ru"

logger = get_logger("max")


async def send_message(session, chat_id, text):
    url = f"{MAX_API_URL}/messages"

    headers = {
        "Authorization": MAX_TOKEN,
        "Content-Type": "application/json"
    }

    payload = {
        "chat_id": chat_id,
        "text": text
    }

    async with session.post(url, json=payload, headers=headers) as response:
        return await response.text()


async def run_max_bot():
    logger.info("🟢 MAX бот запущен (Long Polling)")

    offset = 0

    headers = {
        "Authorization": MAX_TOKEN
    }

    # 🔥 отключаем SSL проверку для локалки
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    connector = aiohttp.TCPConnector(ssl=ssl_context)

    async with aiohttp.ClientSession(connector=connector) as session:
        while True:
            try:
                params = {
                    "offset": offset,
                    "timeout": 30
                }

                async with session.get(
                    f"{MAX_API_URL}/updates",
                    headers=headers,
                    params=params
                ) as response:

                    if response.status != 200:
                        logger.error(f"MAX API error: {response.status}")
                        await asyncio.sleep(5)
                        continue

                    data = await response.json()

                for update in data.get("updates", []):
                    offset = update["update_id"] + 1

                    message = update.get("message")
                    if message:
                        chat_id = message["chat_id"]

                        await send_message(
                            session,
                            chat_id,
                            "Привет 👋 Это тест MAX-бота"
                        )

            except Exception as e:
                logger.error(f"MAX polling error: {e}")
                await asyncio.sleep(5)

            await asyncio.sleep(1)
