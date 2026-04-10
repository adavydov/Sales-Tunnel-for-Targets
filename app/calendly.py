import json
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from app.config import CALENDLY_API_TOKEN, CALENDLY_EVENT_TYPE_URI, MEETING_TIMEZONE


API_BASE = "https://api.calendly.com"


class CalendlyNotConfiguredError(RuntimeError):
    pass


class CalendlyRequestError(RuntimeError):
    pass


@dataclass
class CalendlyBookingResult:
    booking_url: str
    cancel_url: str | None = None
    reschedule_url: str | None = None


def is_configured() -> bool:
    return bool(CALENDLY_API_TOKEN and CALENDLY_EVENT_TYPE_URI)


def _headers() -> dict[str, str]:
    if not is_configured():
        raise CalendlyNotConfiguredError("Calendly credentials are not configured.")
    return {
        "Authorization": f"Bearer {CALENDLY_API_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "AivelBot/1.0 (+https://aivel.ru)",
    }


def _request(method: str, path: str, *, query: dict | None = None, body: dict | None = None) -> dict:
    url = f"{API_BASE}{path}"
    if query:
        url = f"{url}?{urlencode(query)}"

    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = Request(url, method=method, headers=_headers(), data=data)

    try:
        with urlopen(req, timeout=20) as response:
            payload = response.read().decode("utf-8")
            return json.loads(payload) if payload else {}
    except HTTPError as exc:
        details = exc.read().decode("utf-8")
        if exc.code == 403 and "1010" in details:
            raise CalendlyRequestError(
                "Calendly вернул 403 (code 1010). Обычно это блокировка Cloudflare/WAF. "
                "Проверьте, что запрос идёт к api.calendly.com, у токена есть нужные scope, "
                "и попробуйте запрос с другого IP/VPN."
            ) from exc
        raise CalendlyRequestError(f"Calendly HTTP {exc.code}: {details}") from exc
    except URLError as exc:
        raise CalendlyRequestError(f"Calendly connection error: {exc}") from exc


def get_available_hour_slots(target_date: date) -> list[datetime]:
    tz = ZoneInfo(MEETING_TIMEZONE)
    start_local = datetime.combine(target_date, time(9, 0), tzinfo=tz)
    end_local = datetime.combine(target_date, time(22, 0), tzinfo=tz)

    response = _request(
        "GET",
        "/event_type_available_times",
        query={
            "event_type": CALENDLY_EVENT_TYPE_URI,
            "start_time": start_local.astimezone(ZoneInfo("UTC")).isoformat().replace("+00:00", "Z"),
            "end_time": end_local.astimezone(ZoneInfo("UTC")).isoformat().replace("+00:00", "Z"),
        },
    )
    items = response.get("collection", [])

    slots: list[datetime] = []
    for item in items:
        start_time_raw = item.get("start_time")
        if not start_time_raw:
            continue
        start_dt = datetime.fromisoformat(start_time_raw.replace("Z", "+00:00")).astimezone(tz)
        if start_dt.minute == 0 and 9 <= start_dt.hour <= 21:
            slots.append(start_dt)

    slots.sort()
    unique_slots: list[datetime] = []
    seen = set()
    for slot in slots:
        key = slot.isoformat()
        if key not in seen:
            seen.add(key)
            unique_slots.append(slot)
    return unique_slots


def is_slot_available(slot_dt_local: datetime) -> bool:
    all_slots = get_available_hour_slots(slot_dt_local.date())
    target = slot_dt_local.replace(second=0, microsecond=0)
    return any(s.replace(second=0, microsecond=0) == target for s in all_slots)


def book_slot(slot_dt_local: datetime, invitee_name: str, invitee_email: str) -> CalendlyBookingResult:
    body = {
        "event_type": CALENDLY_EVENT_TYPE_URI,
        "start_time": slot_dt_local.astimezone(ZoneInfo("UTC")).isoformat().replace("+00:00", "Z"),
        "invitee": {
            "name": invitee_name,
            "email": invitee_email,
            "timezone": MEETING_TIMEZONE,
        },
    }
    response = _request("POST", "/invitees", body=body)
    resource = response.get("resource", {})
    return CalendlyBookingResult(
        booking_url=resource.get("scheduling_url", ""),
        cancel_url=resource.get("cancel_url"),
        reschedule_url=resource.get("reschedule_url"),
    )
