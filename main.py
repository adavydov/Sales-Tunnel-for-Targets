import asyncio
import logging

from aiogram import Bot, Dispatcher

from app.config import BOT_TOKEN
from app.db import init_db
from app.handlers.start import router as start_router


async def main():
    logging.basicConfig(level=logging.INFO)

    await init_db()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(start_router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())