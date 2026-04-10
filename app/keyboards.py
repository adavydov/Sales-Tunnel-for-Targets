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
            [InlineKeyboardButton(text="✅ Начать точную оценку", callback_data="simulate:mode:precise")],
            [InlineKeyboardButton(text="📊 Скачать Excel-файл", callback_data="simulate:mode:pro")],
        ]
    )


def simulate_results_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Пройти точную оценку", callback_data="simulate:mode:precise")],
            [InlineKeyboardButton(text="📅 Записаться на встречу", callback_data="stub:book_meeting")],
            [InlineKeyboardButton(text="↩️ Вернуться к выбору режима", callback_data="simulate:mode:menu")],
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
            [InlineKeyboardButton(text="📈 Хотите точнее? +3 вопроса", callback_data="simulate:precise:more")],
            [InlineKeyboardButton(text="↩️ Вернуться к выбору режима", callback_data="simulate:mode:menu")],
        ]
    )


def simulate_plus3_standardization_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Высокая", callback_data="simulate:plus3:std:high")],
            [InlineKeyboardButton(text="Средняя", callback_data="simulate:plus3:std:medium")],
            [InlineKeyboardButton(text="Низкая", callback_data="simulate:plus3:std:low")],
        ]
    )


def simulate_plus3_automation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Нет, всё вручную", callback_data="simulate:plus3:auto:none")],
            [InlineKeyboardButton(text="Частично", callback_data="simulate:plus3:auto:partial")],
            [InlineKeyboardButton(text="Есть CRM/системы", callback_data="simulate:plus3:auto:crm")],
            [InlineKeyboardButton(text="Продвинутая (RPA/боты)", callback_data="simulate:plus3:auto:rpa")],
        ]
    )


def simulate_plus3_advisory_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Менее 5%", callback_data="simulate:plus3:advisory:lt5")],
            [InlineKeyboardButton(text="5-15%", callback_data="simulate:plus3:advisory:5_15")],
            [InlineKeyboardButton(text="15-25%", callback_data="simulate:plus3:advisory:15_25")],
            [InlineKeyboardButton(text="Более 25%", callback_data="simulate:plus3:advisory:gt25")],
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
