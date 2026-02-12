import asyncio
from app.platforms.telegram.bot import run_telegram_bot
from app.platforms.max.bot import run_max_bot


async def main():
    print("🤖 Боты запускаются...")
    await asyncio.gather(
        run_telegram_bot(),
        run_max_bot()
    )


if __name__ == "__main__":
    asyncio.run(main())
