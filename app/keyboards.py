from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def track_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Продать 100% бизнеса", callback_data="track:t1")],
        [InlineKeyboardButton(text="Остаться управляющим партнёром", callback_data="track:t2")],
        [InlineKeyboardButton(text="Сравнить оба варианта", callback_data="track:compare")],
    ])


def compare_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Выбрать T1", callback_data="track:t1")],
        [InlineKeyboardButton(text="Выбрать T2", callback_data="track:t2")],
    ])


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