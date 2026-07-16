import aiohttp
import asyncio
import ssl

from app.core.logger import get_logger
from app.core.config import MAX_TOKEN

from app.handlers.max.router import handle_message
from app.handlers.max.context import Context

# handlers
import app.handlers.max.start
import app.handlers.max.form
import app.handlers.max.tz
import app.handlers.max.morning

MAX_API_URL = "https://platform-api.max.ru"
logger = get_logger("max")


# =========================
# SEND
# =========================
async def send_message(session, chat_type, chat_id, user_id, text, attachments=None):

    if not text:
        text = " "

    if chat_type == "dialog":
        url = f"{MAX_API_URL}/messages?user_id={user_id}"
    else:
        url = f"{MAX_API_URL}/messages?chat_id={chat_id}"

    headers = {
        "Authorization": MAX_TOKEN,
        "Content-Type": "application/json"
    }

    payload = {
        "text": str(text)
    }

    if attachments:
        payload["attachments"] = attachments

    logger.info(f"📦 PAYLOAD: {payload}")

    async with session.post(url, json=payload, headers=headers) as response:
        result = await response.text()
        logger.info(f"MAX SEND STATUS: {response.status}")
        logger.info(f"MAX SEND RESPONSE: {result}")
        return result


# =========================
# POLLING
# =========================
async def run_max_bot():

    logger.info("🟢 MAX бот запущен")

    marker = None
    headers = {"Authorization": MAX_TOKEN}

    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    connector = aiohttp.TCPConnector(ssl=ssl_context)

    async with aiohttp.ClientSession(connector=connector) as session:

        while True:
            try:
                params = {}
                if marker:
                    params["marker"] = marker

                async with session.get(
                    f"{MAX_API_URL}/updates",
                    headers=headers,
                    params=params
                ) as response:

                    if response.status != 200:
                        await asyncio.sleep(5)
                        continue

                    data = await response.json()

                marker = data.get("marker")

                for update in data.get("updates", []):

                    # =========================
                    # CALLBACK
                    # =========================
                    if update.get("update_type") == "message_callback":

                        logger.info(f"🔘 CALLBACK: {update}")

                        callback = update.get("callback", {})
                        value = callback.get("payload")

                        message = update.get("message", {})
                        recipient = message.get("recipient", {})

                        user = callback.get("user", {})  # 🔥 ВАЖНО

                        ctx = Context(
                            session=session,
                            chat_type=recipient.get("chat_type"),
                            chat_id=recipient.get("chat_id"),
                            user_id=user.get("user_id"),  # 🔥 ФИКС
                            user_name=user.get("first_name", ""),
                            text=value,
                            send=send_message
                        )

                        await handle_message(ctx)
                        continue

                    # =========================
                    # MESSAGE
                    # =========================
                    if update.get("update_type") != "message_created":
                        continue

                    message = update.get("message", {})
                    recipient = message.get("recipient", {})
                    sender = message.get("sender", {})
                    body = message.get("body", {})

                    text = body.get("text")
                    if isinstance(text, dict):
                        text = text.get("text")

                    if not text:
                        continue

                    logger.info(f"📩 MESSAGE: {text}")

                    ctx = Context(
                        session=session,
                        chat_type=recipient.get("chat_type"),
                        chat_id=recipient.get("chat_id"),
                        user_id=sender.get("user_id"),
                        user_name=sender.get("first_name", ""),
                        text=text,
                        send=send_message
                    )

                    await handle_message(ctx)

            except Exception as e:
                logger.error(f"MAX ERROR: {e}")
                await asyncio.sleep(5)

            await asyncio.sleep(0.1)