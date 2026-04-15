from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta
from urllib.parse import quote
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import (
    CONTENT_SCHEDULER_TIMEZONE,
    EXPORT_SHEETS_API_KEY,
    EXPORT_SHEETS_RANGE,
    EXPORT_SHEETS_SPREADSHEET_ID,
    EXPORT_SYNC_INTERVAL_MINUTES,
)
from app.db import get_users_for_export

logger = logging.getLogger(__name__)

EXPORT_COLUMNS = [
    "id",
    "telegram_id",
    "username",
    "created_at",
    "updated_at",
    "company",
    "contact_name",
    "contact_phone",
    "contact_email",
    "company_website",
    "simulate_consent",
    "valuation_consent",
    "last_connection_at",
    "accountants_count",
    "avg_salary",
    "express_saving_6",
    "express_saving_12",
    "meeting_booked",
    "advisory_band",
    "active_clients_count",
    "standardization_level",
    "automation_level",
    "precise_assessment",
    "margin_percent",
    "growth_band",
    "mna_interest",
    "file_downloaded",
    "uploaded_file_link",
]


def _normalize_sheet_range(sheet_range: str) -> str:
    if "!" not in sheet_range:
        return sheet_range
    sheet_name, cell_range = sheet_range.split("!", 1)
    stripped = sheet_name.strip()
    if stripped.startswith("'") and stripped.endswith("'"):
        return sheet_range

    has_special_chars = any(not char.isascii() or char in {" ", "-"} for char in stripped)
    if has_special_chars:
        return f"'{stripped}'!{cell_range}"
    return sheet_range


def _format_cell(value) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.isoformat(sep=" ", timespec="seconds")
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    return str(value)


def _build_values(rows: list[dict]) -> list[list[str]]:
    values: list[list[str]] = [EXPORT_COLUMNS]
    for row in rows:
        values.append([_format_cell(row.get(column)) for column in EXPORT_COLUMNS])
    return values


def _push_values_to_sheet(values: list[list[str]]):
    range_name = _normalize_sheet_range(EXPORT_SHEETS_RANGE)
    encoded_range = quote(range_name, safe="!:")
    url = (
        f"https://sheets.googleapis.com/v4/spreadsheets/{EXPORT_SHEETS_SPREADSHEET_ID}"
        f"/values/{encoded_range}?valueInputOption=RAW&key={EXPORT_SHEETS_API_KEY}"
    )

    payload = json.dumps(
        {
            "range": range_name,
            "majorDimension": "ROWS",
            "values": values,
        },
        ensure_ascii=False,
    ).encode("utf-8")

    req = Request(
        url=url,
        data=payload,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="PUT",
    )

    with urlopen(req, timeout=20) as response:
        response.read()


async def sync_users_export():
    if not EXPORT_SHEETS_SPREADSHEET_ID or not EXPORT_SHEETS_API_KEY:
        logger.info("Users export to sheets is disabled: missing export spreadsheet or API key.")
        return

    try:
        users = await get_users_for_export()
        values = _build_values(users)
        await asyncio.to_thread(_push_values_to_sheet, values)
        logger.info("Users export synced to sheets. Exported rows: %s", max(len(values) - 1, 0))
    except Exception as exc:  # noqa: BLE001
        logger.warning("Users export sync failed: %s", exc)


def setup_export_scheduler(scheduler: AsyncIOScheduler):
    scheduler.add_job(
        sync_users_export,
        trigger="interval",
        minutes=EXPORT_SYNC_INTERVAL_MINUTES,
        id="users_export_interval",
        coalesce=True,
        misfire_grace_time=120,
        replace_existing=True,
    )
    scheduler.add_job(
        sync_users_export,
        trigger="date",
        run_date=datetime.now(ZoneInfo(CONTENT_SCHEDULER_TIMEZONE)) + timedelta(seconds=20),
        id="users_export_startup",
        misfire_grace_time=120,
        replace_existing=True,
    )
