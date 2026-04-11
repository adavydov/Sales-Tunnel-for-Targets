import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
CALENDLY_API_TOKEN = os.getenv("CALENDLY_API_TOKEN")
CALENDLY_EVENT_TYPE_URI = os.getenv("CALENDLY_EVENT_TYPE_URI")
MEETING_TIMEZONE = os.getenv("MEETING_TIMEZONE", "Europe/Moscow")
GOOGLE_SHEETS_API_KEY = os.getenv("GOOGLE_SHEETS_API_KEY")
GOOGLE_SHEETS_SPREADSHEET_ID = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID")
GOOGLE_SHEETS_RANGE = os.getenv("GOOGLE_SHEETS_RANGE", "Content-events!A2:F")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не найден в .env")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL не найден в .env")
