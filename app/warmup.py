import logging
from zoneinfo import ZoneInfo

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.db import add_event, get_all_users

logger = logging.getLogger(__name__)

WARMUP_IMAGE_URL = "https://dummyimage.com/1200x630/111827/ffffff&text=AIVEL"
WARMUP_TEXT = (
    "🔥 <b>Daily Targeted Warmup from AIVEL</b>\n\n"
    "Soon you will receive useful cases, articles, and practical insights here every day.\n"
    "For now, keep our website handy: https://aivel.ai/"
)


async def send_daily_warmup(bot: Bot):
    users = await get_all_users()
    if not users:
        logger.info("No users for daily warmup")
        return

    for user in users:
        try:
            await bot.send_photo(
                chat_id=user["telegram_id"],
                photo=WARMUP_IMAGE_URL,
                caption=WARMUP_TEXT,
                parse_mode="HTML",
            )
            await add_event(user["id"], "daily_warmup_sent")
        except Exception as exc:
            logger.warning("Failed to send warmup to %s: %s", user["telegram_id"], exc)


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=ZoneInfo("UTC"))

    scheduler.add_job(
        send_daily_warmup,
        trigger="cron",
        hour=14,
        minute=0,
        kwargs={"bot": bot},
        id="daily_warmup",
        replace_existing=True,
    )

    scheduler.start()
    return scheduler
