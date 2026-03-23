from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="Оценить бизнес",
                callback_data="menu:sell"
            )],
            # [InlineKeyboardButton(
            #     text="Сравнить варианты",
            #     callback_data="menu:compare"
            # )],
            # [InlineKeyboardButton(
            #     text="Хочу задать вопрос",
            #     callback_data="menu:ask"
            # )],
            [InlineKeyboardButton(
                text="Материалы для ознакомления", 
                callback_data="menu:materials"
            )],
            [InlineKeyboardButton(
                text="Связаться с нами",
                callback_data="menu:call"
            )],
            [InlineKeyboardButton(
                text="Скрыть меню",
                callback_data="menu:hide"
            )],
        ]
    )


def sell_submenu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="Продать весь бизнес",
                callback_data="track:t1"
            )],
            [InlineKeyboardButton(
                text="Продать часть бизнеса / сотрудничать",
                callback_data="track:t2"
            )],
        ]
    )


def question_feedback_keyboard(question_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="Да, ответили",
                callback_data=f"question_feedback:yes:{question_id}"
            )],
            [InlineKeyboardButton(
                text="Нет, не до конца",
                callback_data=f"question_feedback:no:{question_id}"
            )],
        ]
    )


def persistent_menu_reply_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Меню")]
        ],
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="Нажмите «Меню»"
    )


def role_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Собственник", callback_data="role:owner")],
        [InlineKeyboardButton(text="Партнёр", callback_data="role:partner")],
        [InlineKeyboardButton(text="CEO", callback_data="role:ceo")],
        [InlineKeyboardButton(text="Операционный руководитель", callback_data="role:ops")],
    ])


def business_size_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Крупный", callback_data="size:large")],
        [InlineKeyboardButton(text="Средний", callback_data="size:medium")],
        [InlineKeyboardButton(text="Небольшой", callback_data="size:small")],
    ])


def timeframe_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Сейчас", callback_data="time:now")],
        [InlineKeyboardButton(text="3–6 месяцев", callback_data="time:3_6")],
        [InlineKeyboardButton(text="6–12 месяцев", callback_data="time:6_12")],
        [InlineKeyboardButton(text="Позже", callback_data="time:later")],
    ])


def motivation_keyboard(track: str) -> InlineKeyboardMarkup:
    if track == "t1":
        items = [
            ("Хочу выйти из операционки", "motivation:exit"),
            ("Нужна сделка / ликвидность", "motivation:liquidity"),
            ("Устал тащить всё на себе", "motivation:burnout"),
            ("Хочу снизить риски", "motivation:risk"),
        ]
    else:
        items = [
            ("Хочу расти быстрее", "motivation:growth"),
            ("Нужен сильный партнёр", "motivation:partner"),
            ("Хочу сохранить контроль", "motivation:control"),
            ("Нужна поддержка в масштабировании", "motivation:scale"),
        ]

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=text, callback_data=callback)]
            for text, callback in items
        ]
    )


def final_status_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="Оставить свои контакты",
                callback_data="contact:start"
            )]
        ]
    )


def contact_consent_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="Принимаю",
                callback_data="contact:accept"
            )]
        ]
    )


def contact_type_keyboard(available_types: list[str]) -> InlineKeyboardMarkup:
    labels = {
        "email": "Email",
        "telegram": "Telegram",
        "phone": "Телефон",
    }

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=labels[contact_type],
                callback_data=f"contact_type:{contact_type}"
            )]
            for contact_type in available_types
        ]
    )


def warmup_interest_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="Заинтересовался",
                callback_data="warmup:interested"
            )]
        ]
    )


def after_contact_saved_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="Оставить еще один способ связи",
                callback_data="contact:add_more"
            )],
            [InlineKeyboardButton(
                text="Ошибся при вводе данных",
                callback_data="contact:edit"
            )],
        ]
    )