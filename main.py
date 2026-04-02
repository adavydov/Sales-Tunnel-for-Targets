import asyncio
import logging

from aiogram import Bot, Dispatcher

from app.config import BOT_TOKEN
from app.db import init_db
from app.handlers.start import router as start_router
from app.materials import ensure_material_files
from app.warmup import setup_scheduler


async def main():
    logging.basicConfig(level=logging.INFO)

    ensure_material_files()
    await init_db()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(start_router)

    scheduler = setup_scheduler(bot)

    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
