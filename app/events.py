from __future__ import annotations

import html
import json
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import quote
from urllib.request import urlopen


class EventsConfigError(RuntimeError):
    pass


class EventsRequestError(RuntimeError):
    pass


@dataclass
class EventItem:
    name: str
    time_and_date: str
    where: str
    support_text: str
    link: str


def fetch_events(spreadsheet_id: str, api_key: str, sheet_range: str, timeout: int = 10) -> list[EventItem]:
    if not spreadsheet_id or not api_key:
        raise EventsConfigError("Google Sheets не настроен: добавьте GOOGLE_SHEETS_SPREADSHEET_ID и GOOGLE_SHEETS_API_KEY.")

    encoded_range = quote(sheet_range, safe="!:")
    url = (
        f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{encoded_range}"
        f"?key={api_key}&majorDimension=ROWS"
    )

    try:
        with urlopen(url, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise EventsRequestError(f"Не удалось загрузить мероприятия: {exc}") from exc

    rows = payload.get("values", [])
    events: list[EventItem] = []
    for row in rows:
        if not row:
            continue

        values = list(row) + [""] * max(0, 6 - len(row))
        _, name, time_and_date, where, support_text, link = values[:6]
        if not name.strip():
            continue

        events.append(
            EventItem(
                name=name.strip(),
                time_and_date=time_and_date.strip(),
                where=where.strip(),
                support_text=support_text.strip(),
                link=link.strip(),
            )
        )

    return events


def _truncate(text: str, max_len: int = 220) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= max_len:
        return normalized
    return normalized[: max_len - 1].rstrip() + "…"


def _format_date_header() -> str:
    now = datetime.now().strftime("%d.%m.%Y")
    return f"📅 <b>Где можно встретиться на мероприятиях</b>\n<i>Актуально на {now}</i>"


def format_events_message(events: list[EventItem]) -> str:
    if not events:
        return (
            "📅 <b>Где можно встретиться на мероприятиях</b>\n\n"
            "Сейчас в расписании пока нет событий. Загляните чуть позже."
        )

    lines = [_format_date_header(), "", "Подобрали актуальные события:"]
    for idx, event in enumerate(events, start=1):
        lines.extend(
            [
                "",
                f"<b>{idx}. {html.escape(event.name)}</b>",
                f"🗓 <b>Дата:</b> {html.escape(event.time_and_date) or 'Уточняется'}",
                f"📍 <b>Формат/место:</b> {html.escape(event.where) or 'Уточняется'}",
            ]
        )

        if event.support_text:
            lines.append(f"📝 <b>Описание:</b> {html.escape(_truncate(event.support_text))}")
        if event.link:
            safe_link = html.escape(event.link, quote=True)
            lines.append(f"🔗 <a href=\"{safe_link}\">Регистрация / детали</a>")

    lines.extend(["", "📌 Если хотите, подскажу, на какое событие лучше идти первым."])
    return "\n".join(lines)
