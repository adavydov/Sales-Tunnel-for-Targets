import calendar
from datetime import date, datetime

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def persistent_main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Меню бота")],
            [KeyboardButton(text="Калькулятор экономии")],
            [KeyboardButton(text="Оценка стоимости фирмы")],
        ],
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="Выберите раздел",
    )


def menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Записаться на встречу", callback_data="stub:book_meeting")],
            [InlineKeyboardButton(text="Встретиться на мероприятиях", callback_data="stub:events")],
            [InlineKeyboardButton(text="Продукты и услуги", callback_data="stub:products")],
            [InlineKeyboardButton(text="Видео и кейсы (скоро)", callback_data="stub:videos")],
        ]
    )


def website_optional_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Нет сайта", callback_data="onboarding:no_site")],
        ]
    )


def tool_consent_keyboard(nda_checked: bool, terms_checked: bool, tool_name: str) -> InlineKeyboardMarkup:
    nda_icon = "✅" if nda_checked else "⬜"
    terms_icon = "✅" if terms_checked else "⬜"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{nda_icon} NDA from AIVEL side", callback_data="consent:toggle:nda")],
            [InlineKeyboardButton(text=f"{terms_icon} Terms + Privacy + Marketing", callback_data="consent:toggle:terms")],
            [InlineKeyboardButton(text="Соглашаюсь", callback_data=f"consent:submit:{tool_name}")],
            [InlineKeyboardButton(text="Назад", callback_data="consent:back")],
        ]
    )


def simulate_mode_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⚡ Начать экспресс-оценку", callback_data="simulate:mode:express")],
            [InlineKeyboardButton(text="📊 Скачать Excel-файл", callback_data="simulate:mode:pro")],
            [InlineKeyboardButton(text="↩️ Назад", callback_data="simulate:back")],
        ]
    )


def simulate_results_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📅 Записаться на встречу", callback_data="stub:book_meeting")],
            [InlineKeyboardButton(text="📈 Хотите точнее? +5 вопросов", callback_data="simulate:precise:more5")],
            [InlineKeyboardButton(text="📊 Скачать Excel-файл", callback_data="simulate:mode:pro")],
            [InlineKeyboardButton(text="↩️ Назад", callback_data="simulate:back")],
        ]
    )


def simulate_skip_question_keyboard(question_key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Пропустить вопрос", callback_data=f"simulate:express:skip:{question_key}")],
            [InlineKeyboardButton(text="Назад", callback_data="simulate:back")],
        ]
    )


def simulate_precise_skip_keyboard(callback_data: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Пропустить вопрос", callback_data=callback_data)],
        ]
    )


def simulate_contacts_choice_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Поделиться", callback_data="simulate:contacts:share")],
            [InlineKeyboardButton(text="Пропустить вопрос", callback_data="simulate:contacts:skip")],
        ]
    )


def simulate_contact_field_keyboard(skip_callback: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Пропустить поле", callback_data=skip_callback)],
        ]
    )


def simulate_precise_ops_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="40-50%", callback_data="simulate:precise:ops:40_50")],
            [InlineKeyboardButton(text="50-70%", callback_data="simulate:precise:ops:50_70")],
            [InlineKeyboardButton(text="70%+", callback_data="simulate:precise:ops:70_plus")],
        ]
    )


def simulate_precise_complex_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Да, много (>30%)", callback_data="simulate:precise:complex:many")],
            [InlineKeyboardButton(text="Некоторые (10–30%)", callback_data="simulate:precise:complex:some")],
            [InlineKeyboardButton(text="Мало (<10%)", callback_data="simulate:precise:complex:few")],
        ]
    )


def simulate_precise_results_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📅 Записаться на встречу", callback_data="stub:book_meeting")],
            [InlineKeyboardButton(text="📈 Хотите точнее? +5 вопросов", callback_data="simulate:precise:more5")],
            [InlineKeyboardButton(text="↩️ Назад", callback_data="simulate:back")],
        ]
    )


def simulate_plus3_standardization_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Высокая стандартизация",
                    callback_data="simulate:plus3:std:high",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Средняя стандартизация",
                    callback_data="simulate:plus3:std:medium",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Низкая стандартизация",
                    callback_data="simulate:plus3:std:low",
                )
            ],
            [InlineKeyboardButton(text="Пропустить вопрос", callback_data="simulate:plus3:std:skip")],
        ]
    )


def simulate_plus3_automation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Нет, всё вручную — только 1С и Excel", callback_data="simulate:plus3:auto:none")],
            [
                InlineKeyboardButton(
                    text="Частично — макросы, автовыгрузки, шаблоны, таск-менеджер",
                    callback_data="simulate:plus3:auto:partial",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Да, есть системы — используем RPA/ботов/AI",
                    callback_data="simulate:plus3:auto:systems",
                )
            ],
            [InlineKeyboardButton(text="Пропустить вопрос", callback_data="simulate:plus3:auto:skip")],
        ]
    )


def simulate_plus3_advisory_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Менее 10%", callback_data="simulate:plus3:advisory:lt10")],
            [InlineKeyboardButton(text="10-20%", callback_data="simulate:plus3:advisory:10_20")],
            [InlineKeyboardButton(text="Более 20%", callback_data="simulate:plus3:advisory:gt20")],
            [InlineKeyboardButton(text="Пропустить вопрос", callback_data="simulate:plus3:advisory:skip")],
        ]
    )


def simulate_growth_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Нет", callback_data="simulate:post:growth:none")],
            [InlineKeyboardButton(text="Да, обычный рост +5–20%", callback_data="simulate:post:growth:normal")],
            [InlineKeyboardButton(text="Да, быстрый рост >20%", callback_data="simulate:post:growth:fast")],
        ]
    )


def simulate_mna_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Да", callback_data="simulate:post:mna:yes")],
            [InlineKeyboardButton(text="Нет", callback_data="simulate:post:mna:no")],
        ]
    )


def simulate_deep_assessment_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Скачать Excel-файл", callback_data="simulate:deep:download")],
            [InlineKeyboardButton(text="↩️ Назад", callback_data="simulate:deep:back")],
        ]
    )


def simulate_deep_wait_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Отправил по почте", callback_data="simulate:deep:sent_email")],
            [InlineKeyboardButton(text="↩️ Назад", callback_data="simulate:deep:back_wait")],
        ]
    )


def meeting_calendar_keyboard(year: int, month: int) -> InlineKeyboardMarkup:
    cal = calendar.Calendar(firstweekday=0)
    month_days = cal.monthdayscalendar(year, month)
    month_name = datetime(year, month, 1).strftime("%B %Y")

    inline_keyboard = [[InlineKeyboardButton(text=month_name, callback_data="meeting:noop")]]
    inline_keyboard.append(
        [InlineKeyboardButton(text=day, callback_data="meeting:noop") for day in ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]]
    )

    today = date.today()
    for week in month_days:
        row = []
        for d in week:
            if d == 0:
                row.append(InlineKeyboardButton(text=" ", callback_data="meeting:noop"))
                continue
            selected = date(year, month, d)
            if selected < today:
                row.append(InlineKeyboardButton(text="·", callback_data="meeting:noop"))
            else:
                row.append(
                    InlineKeyboardButton(
                        text=str(d),
                        callback_data=f"meeting:date:pick:{selected.isoformat()}",
                    )
                )
        inline_keyboard.append(row)

    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1
    inline_keyboard.append(
        [
            InlineKeyboardButton(text="◀️", callback_data=f"meeting:date:nav:{prev_year}-{prev_month:02d}"),
            InlineKeyboardButton(text="Назад", callback_data="meeting:back"),
            InlineKeyboardButton(text="▶️", callback_data=f"meeting:date:nav:{next_year}-{next_month:02d}"),
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


def meeting_slots_keyboard(slot_values: list[str]) -> InlineKeyboardMarkup:
    inline_keyboard = [[InlineKeyboardButton(text=slot, callback_data=f"meeting:slot:{slot}")] for slot in slot_values]
    inline_keyboard.append([InlineKeyboardButton(text="Другое время", callback_data="meeting:slot:other")])
    inline_keyboard.append([InlineKeyboardButton(text="Назад", callback_data="meeting:back")])
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


def meeting_custom_time_keyboard() -> InlineKeyboardMarkup:
    rows = []
    for hour in range(9, 22):
        rows.append([InlineKeyboardButton(text=f"{hour:02d}:00", callback_data=f"meeting:time:{hour:02d}:00")])
    rows.append([InlineKeyboardButton(text="Назад", callback_data="meeting:back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def meeting_waiting_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Назад", callback_data="meeting:back")],
        ]
    )


def calendly_meeting_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Открыть Calendly", url="https://calendly.com/4davyd0vcreate/30min")],
        ]
    )
