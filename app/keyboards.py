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
