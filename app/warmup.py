# import logging
# from zoneinfo import ZoneInfo

# from apscheduler.schedulers.asyncio import AsyncIOScheduler
# from aiogram import Bot

# from app.db import get_all_users, get_random_warmup_message, log_warmup_delivery
# from app.keyboards import warmup_interest_keyboard

# logger = logging.getLogger(__name__)


# async def send_hourly_warmup(bot: Bot):
#     warmup_message = await get_random_warmup_message()
#     if not warmup_message:
#         logger.info("Нет активных прогревных сообщений")
#         return

#     users = await get_all_users()
#     if not users:
#         logger.info("Нет пользователей для прогрева")
#         return

#     text = f"{warmup_message['title']}\n\n{warmup_message['body']}"

#     for user in users:
#         try:
#             await bot.send_message(
#                 chat_id=user["telegram_id"],
#                 text=text,
#                 reply_markup=warmup_interest_keyboard(),
#             )
#             await log_warmup_delivery(user["id"], warmup_message["id"])
#         except Exception as e:
#             logger.warning(
#                 "Не удалось отправить прогрев пользователю %s: %s",
#                 user["telegram_id"],
#                 e,
#             )


# def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
#     scheduler = AsyncIOScheduler(timezone=ZoneInfo("Europe/Berlin"))

#     scheduler.add_job(
#         send_hourly_warmup,
#         trigger="cron",
#         minute=0,
#         kwargs={"bot": bot},
#         id="hourly_warmup",
#         replace_existing=True,
#     )

#     scheduler.start()
#     return scheduler