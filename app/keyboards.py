from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def persistent_main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Menu")],
            [KeyboardButton(text="Simulate Savings")],
            [KeyboardButton(text="Valuation simulator")],
        ],
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="Choose an action",
    )


def menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Book a meeting (corporate or accounting firm)", callback_data="stub:book_meeting")],
            [InlineKeyboardButton(text="Meet us at events", callback_data="stub:events")],
            [InlineKeyboardButton(text="Simulate savings with AIVEL", callback_data="tool:simulate")],
            [InlineKeyboardButton(text="Accounting firm Valuation Simulator", callback_data="tool:valuation")],
            [InlineKeyboardButton(text="Our products & services", callback_data="stub:products")],
            [InlineKeyboardButton(text="Videos & Case studies", callback_data="stub:videos")],
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
