import re
import logging

from aiogram import F, Router
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message, ReplyKeyboardRemove

from app.db import (
    add_event,
    create_user_question,
    save_profile_field,
    save_scores,
    update_question_status,
    upsert_contact,
    upsert_user,
    get_filled_contact_types,
)
from app.keyboards import (
    business_size_keyboard,
    contact_consent_keyboard,
    contact_type_keyboard,
    final_status_keyboard,
    main_menu_keyboard,
    motivation_keyboard,
    persistent_menu_reply_keyboard,
    question_feedback_keyboard,
    role_keyboard,
    sell_submenu_keyboard,
    timeframe_keyboard,
    after_contact_saved_keyboard,
)
from app.materials import MATERIAL_FILES, MATERIALS_DIR
from app.scoring import build_result_screen, calculate_scores
from app.states import BotFlow, ContactFlow, LeadFlow

router = Router()
logger = logging.getLogger(__name__)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
TG_RE = re.compile(r"^@?[A-Za-z0-9_]{5,32}$")
PHONE_RE = re.compile(r"^\+?[0-9()\-\s]{7,20}$")

MENU_TEXT = (
    "Здравствуйте!\n\n"
    "Это бот, в котором можно разобраться в вариантах продажи бизнеса "
    "или сотрудничества, а также задать вопрос по теме.\n\n"
    "Выберите, что вам сейчас актуально:"
)

SELL_SUBMENU_TEXT = (
    "Хороший шаг.\n\n"
    "Выберите подходящий вариант:"
)

QUESTION_WAIT_TEXT = (
    "Ожидаем ваш вопрос.\n\n"
    "Напишите его одним сообщением в свободной форме."
)

QUESTION_REASK_TEXT = (
    "Задайте свой вопрос одним сообщением."
)

QUESTION_FOLLOW_UP_TEXT = (
    "Ваш вопрос очень важен для нас, ответим в ближайшее время.\n\n"
    "Мы ответили на ваш вопрос?"
)

COMPARE_TEXT = (
    "Ниже кратко разница между вариантами:\n\n"
    "1. Полная продажа бизнеса — сценарий, в котором рассматривается передача "
    "100% бизнеса.\n"
    "2. Продажа части бизнеса / сотрудничество — сценарий, в котором вы сохраняете "
    "участие в бизнесе и рассматриваете партнерскую модель.\n\n"
    "Ниже прикреплены 3 файла:"
)

TRACK_1_INTRO = (
    "Трек 1: продажа всего бизнеса.\n\n"
    "Ответьте на несколько коротких вопросов."
)

TRACK_2_INTRO = (
    "Трек 2: продажа части бизнеса / сотрудничество.\n\n"
    "Ответьте на несколько коротких вопросов."
)

CONTACT_SAFETY_TEXT = (
    "Мы используем контактные данные только для связи по вашему запросу.\n\n"
    "Информация не будет использоваться для посторонних целей и не передается "
    "третьим лицам вне рабочего процесса.\n\n"
    "Если вы согласны, нажмите кнопку ниже."
)

CONTACT_TYPE_PROMPTS = {
    "email": "Введите ваш email одним сообщением.",
    "telegram": "Введите ваш Telegram в формате @username.",
    "phone": "Введите ваш номер телефона одним сообщением.",
}

CONTACT_ORDER = ["email", "telegram", "phone"]

INVALID_CONTACT_MESSAGES = {
    "email": "Email введен некорректно. Пример: name@example.com",
    "telegram": "Telegram должен начинаться с @ и содержать только буквы, цифры и _. Пример: @my_username",
    "phone": "Телефон введен некорректно. Пример: +79991234567",
}

CONTACT_INFO = "Связаться с нами можно по следующим контактам:\nEmail: example@company.com\nТелефон: +7 999 123 45 67\nTelegram: @example_contact"



async def safe_delete(message: Message):
    try:
        await message.delete()
    except Exception as exc:
        logger.warning("Не удалось удалить сообщение: %s", exc)


async def get_db_user_id(message_or_callback: Message | CallbackQuery) -> int:
    tg_user = message_or_callback.from_user
    return await upsert_user(
        telegram_id=tg_user.id,
        username=tg_user.username,
        first_name=tg_user.first_name,
        last_name=tg_user.last_name,
    )


def normalize_contact(contact_type: str, raw_value: str) -> str | None:
    value = raw_value.strip()

    if contact_type == "email":
        value = value.lower()
        return value if EMAIL_RE.match(value) else None

    if contact_type == "telegram":
        if not value.startswith("@"):
            return None

        username = value[1:]
        if not re.match(r"^[A-Za-z0-9_]{5,32}$", username):
            return None

        return value

    if contact_type == "phone":
        return value if PHONE_RE.match(value) else None

    return None


def get_missing_contact_types(filled_types: list[str]) -> list[str]:
    return [contact_type for contact_type in CONTACT_ORDER if contact_type not in filled_types]


def sort_contact_types(contact_types: list[str]) -> list[str]:
    return [contact_type for contact_type in CONTACT_ORDER if contact_type in contact_types]


async def send_post_contact_success(message: Message, text: str):
    await message.answer(
        text,
        reply_markup=after_contact_saved_keyboard(),
    )



async def send_main_menu(message: Message, user_id: int, *, with_keyboard: bool):
    await add_event(user_id, "menu_shown")

    await message.answer(
        MENU_TEXT,
        reply_markup=main_menu_keyboard(),
    )

    if with_keyboard:
        await message.answer(
            "Кнопка «Меню» доступна на клавиатуре ниже.",
            reply_markup=persistent_menu_reply_keyboard(),
        )


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    user_id = await get_db_user_id(message)
    await add_event(user_id, "start")
    await state.clear()

    await send_main_menu(
        message=message,
        user_id=user_id,
        with_keyboard=True,
    )


@router.message(StateFilter(None), Command("menu"))
@router.message(StateFilter(None), F.text == "Меню")
async def open_menu_from_text(message: Message, state: FSMContext):
    user_id = await get_db_user_id(message)
    await add_event(user_id, "menu_opened_from_text")
    await state.clear()

    await send_main_menu(
        message=message,
        user_id=user_id,
        with_keyboard=False,
    )


@router.callback_query(F.data == "menu:sell")
@router.callback_query(F.data == "warmup:interested")
async def open_sell_submenu(callback: CallbackQuery, state: FSMContext):
    user_id = await get_db_user_id(callback)
    source = "warmup" if callback.data == "warmup:interested" else "menu"
    await add_event(user_id, "sell_submenu_opened", source)
    await state.clear()

    await safe_delete(callback.message)

    await callback.message.answer(
        SELL_SUBMENU_TEXT,
        reply_markup=sell_submenu_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "menu:ask")
async def open_question_flow(callback: CallbackQuery, state: FSMContext):
    user_id = await get_db_user_id(callback)
    await add_event(user_id, "question_flow_opened")
    await state.clear()
    await state.set_state(BotFlow.awaiting_question)

    await safe_delete(callback.message)
    await callback.message.answer(
        QUESTION_WAIT_TEXT,
        reply_markup=ReplyKeyboardRemove(),
    )
    await callback.answer()


# @router.callback_query(F.data == "menu:compare")
# async def open_compare_flow(callback: CallbackQuery, state: FSMContext):
#     user_id = await get_db_user_id(callback)
#     await add_event(user_id, "compare_opened")
#     await state.clear()

#     await safe_delete(callback.message)
#     await callback.message.answer(COMPARE_TEXT)

#     for item in COMPARE_FILES:
#         file_path = MATERIALS_DIR / item["local_name"]
#         await callback.message.answer_document(
#             FSInputFile(file_path, filename=item["display_name"])
#         )

#     await callback.answer()


@router.callback_query(F.data == "menu:call")
async def organize_call(callback: CallbackQuery, state: FSMContext):
    user_id = await get_db_user_id(callback)
    await add_event(user_id, "call_requested")
    await state.clear()

    await safe_delete(callback.message)
    await callback.message.answer(CONTACT_INFO)
    await callback.answer()


@router.callback_query(F.data == "menu:hide")
async def hide_menu(callback: CallbackQuery, state: FSMContext):
    user_id = await get_db_user_id(callback)
    await add_event(user_id, "menu_hidden")
    await state.clear()

    await safe_delete(callback.message)
    await callback.answer("Меню скрыто")


@router.message(BotFlow.awaiting_question, F.text)
async def handle_user_question(message: Message, state: FSMContext):
    user_id = await get_db_user_id(message)
    question_text = message.text.strip()

    question_id = await create_user_question(user_id, question_text)
    await add_event(user_id, "question_submitted", question_text)

    await state.clear()

    await message.answer(
        QUESTION_FOLLOW_UP_TEXT,
        reply_markup=question_feedback_keyboard(question_id),
    )


@router.message(BotFlow.awaiting_question)
async def handle_non_text_question(message: Message):
    await message.answer("Пожалуйста, отправьте вопрос текстом одним сообщением.")


@router.callback_query(F.data.startswith("question_feedback:"))
async def handle_question_feedback(callback: CallbackQuery, state: FSMContext):
    user_id = await get_db_user_id(callback)
    _, action, question_id_raw = callback.data.split(":")
    question_id = int(question_id_raw)

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception as exc:
        logger.warning("Не удалось очистить inline-клавиатуру: %s", exc)

    if action == "yes":
        await update_question_status(question_id, "resolved")
        await add_event(user_id, "question_feedback_yes", str(question_id))
        await state.clear()

        await callback.message.answer(
            "Рады, что смогли помочь!",
            reply_markup=persistent_menu_reply_keyboard(),
        )
        await callback.answer()
        return

    await update_question_status(question_id, "not_resolved")
    await add_event(user_id, "question_feedback_no", str(question_id))
    await state.set_state(BotFlow.awaiting_question)

    await callback.message.answer(QUESTION_REASK_TEXT)
    await callback.answer()


@router.callback_query(F.data == "track:t1")
async def start_track_1(callback: CallbackQuery, state: FSMContext):
    user_id = await get_db_user_id(callback)
    await add_event(user_id, "track_selected", "t1")
    await save_profile_field(user_id, "track", "t1")

    await state.clear()
    await state.update_data(
        db_user_id=user_id,
        track="t1",
    )
    await state.set_state(LeadFlow.role)

    await safe_delete(callback.message)

    await callback.message.answer(
        TRACK_1_INTRO,
        reply_markup=ReplyKeyboardRemove(),
    )
    await callback.message.answer(
        "Кто вы в компании?",
        reply_markup=role_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "track:t2")
async def start_track_2(callback: CallbackQuery, state: FSMContext):
    user_id = await get_db_user_id(callback)
    await add_event(user_id, "track_selected", "t2")
    await save_profile_field(user_id, "track", "t2")

    await state.clear()
    await state.update_data(
        db_user_id=user_id,
        track="t2",
    )
    await state.set_state(LeadFlow.role)

    await safe_delete(callback.message)

    await callback.message.answer(
        TRACK_2_INTRO,
        reply_markup=ReplyKeyboardRemove(),
    )
    await callback.message.answer(
        "Кто вы в компании?",
        reply_markup=role_keyboard(),
    )
    await callback.answer()


@router.callback_query(LeadFlow.role, F.data.startswith("role:"))
async def process_role(callback: CallbackQuery, state: FSMContext):
    role = callback.data.split(":", 1)[1]
    data = await state.get_data()
    user_id = data["db_user_id"]

    await save_profile_field(user_id, "role", role)
    await add_event(user_id, "role_selected", role)

    await state.update_data(role=role)
    await state.set_state(LeadFlow.business_size)

    await callback.message.edit_text(
        "Какой масштаб бизнеса?",
        reply_markup=business_size_keyboard(),
    )
    await callback.answer()


@router.callback_query(LeadFlow.business_size, F.data.startswith("size:"))
async def process_business_size(callback: CallbackQuery, state: FSMContext):
    business_size = callback.data.split(":", 1)[1]
    data = await state.get_data()
    user_id = data["db_user_id"]

    await save_profile_field(user_id, "business_size", business_size)
    await add_event(user_id, "size_selected", business_size)

    await state.update_data(business_size=business_size)
    await state.set_state(LeadFlow.timeframe)

    await callback.message.edit_text(
        "Когда задача актуальна?",
        reply_markup=timeframe_keyboard(),
    )
    await callback.answer()


@router.callback_query(LeadFlow.timeframe, F.data.startswith("time:"))
async def process_timeframe(callback: CallbackQuery, state: FSMContext):
    timeframe = callback.data.split(":", 1)[1]
    data = await state.get_data()
    user_id = data["db_user_id"]
    track = data["track"]

    await save_profile_field(user_id, "timeframe", timeframe)
    await add_event(user_id, "timeframe_selected", timeframe)

    await state.update_data(timeframe=timeframe)
    await state.set_state(LeadFlow.motivation)

    await callback.message.edit_text(
        "Что сейчас главный мотив?",
        reply_markup=motivation_keyboard(track),
    )
    await callback.answer()


@router.callback_query(LeadFlow.motivation, F.data.startswith("motivation:"))
async def process_motivation(callback: CallbackQuery, state: FSMContext):
    motivation = callback.data.split(":", 1)[1]
    data = await state.get_data()
    user_id = data["db_user_id"]

    track = data["track"]
    role = data["role"]
    business_size = data["business_size"]
    timeframe = data["timeframe"]

    await save_profile_field(user_id, "motivation", motivation)
    await add_event(user_id, "motivation_selected", motivation)

    fit_score, intent_score, status = calculate_scores(
        track=track,
        role=role,
        business_size=business_size,
        timeframe=timeframe,
        motivation=motivation,
    )

    await save_scores(user_id, fit_score, intent_score, status)
    await add_event(user_id, "status_calculated", status)

    await state.update_data(
        result_status=status,
        fit_score=fit_score,
        intent_score=intent_score,
    )
    await state.set_state(ContactFlow.waiting_contact_start)

    result_text = build_result_screen(track=track, status=status)

    await callback.message.edit_text(
        result_text,
        reply_markup=final_status_keyboard(),
    )
    await callback.answer()


@router.callback_query(ContactFlow.waiting_contact_start, F.data == "contact:start")
async def start_contact_flow(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = data["db_user_id"]

    await add_event(user_id, "contact_flow_started")

    await state.set_state(ContactFlow.waiting_consent)

    await callback.message.answer(
        CONTACT_SAFETY_TEXT,
        reply_markup=contact_consent_keyboard(),
    )
    await callback.answer()


@router.callback_query(ContactFlow.waiting_consent, F.data == "contact:accept")
async def accept_contact_consent(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = data["db_user_id"]

    await add_event(user_id, "contact_consent_accepted")

    filled_types = sort_contact_types(await get_filled_contact_types(user_id))
    missing_types = get_missing_contact_types(filled_types)

    await safe_delete(callback.message)

    if not missing_types:
        await state.clear()
        await callback.message.answer(
            "У вас уже заполнены все способы связи. Больше ничего добавлять не нужно.",
            reply_markup=persistent_menu_reply_keyboard(),
        )

        await callback.answer()
        return

    await state.update_data(contact_mode="new")
    await state.set_state(ContactFlow.waiting_contact_type)

    await callback.message.answer(
        "Продолжаем заполнение контактов.",
        reply_markup=ReplyKeyboardRemove(),
    )
    await callback.message.answer(
        "Выберите, в каком формате хотите оставить контакт:",
        reply_markup=contact_type_keyboard(missing_types),
    )
    await callback.answer()


@router.callback_query(ContactFlow.waiting_contact_type, F.data.startswith("contact_type:"))
async def choose_contact_type(callback: CallbackQuery, state: FSMContext):
    contact_type = callback.data.split(":", 1)[1]
    data = await state.get_data()
    user_id = data["db_user_id"]
    contact_mode = data.get("contact_mode", "new")

    await add_event(user_id, "contact_type_selected", f"{contact_mode}:{contact_type}")

    await state.update_data(contact_type=contact_type)
    await state.set_state(ContactFlow.waiting_contact_value)

    await callback.message.answer(CONTACT_TYPE_PROMPTS[contact_type])
    await callback.answer()


@router.message(ContactFlow.waiting_contact_value, F.text)
async def save_contact_value(message: Message, state: FSMContext):
    data = await state.get_data()
    user_id = data["db_user_id"]
    contact_type = data["contact_type"]
    contact_mode = data.get("contact_mode", "new")

    normalized = normalize_contact(contact_type, message.text)

    if not normalized:
        await message.answer(INVALID_CONTACT_MESSAGES[contact_type])
        return

    await upsert_contact(user_id, contact_type, normalized)

    if contact_mode == "edit":
        await add_event(user_id, "contact_updated", f"{contact_type}:{normalized}")
        await state.clear()
        await send_post_contact_success(
            message,
            "Данные обновлены. Скоро с вами свяжутся.",
        )
        return

    await add_event(user_id, "contact_saved", f"{contact_type}:{normalized}")
    await state.clear()
    await send_post_contact_success(
        message,
        "Спасибо, скоро с вами свяжутся.",
    )


@router.message(ContactFlow.waiting_contact_value)
async def save_contact_non_text(message: Message):
    await message.answer("Пожалуйста, отправьте контакт одним текстовым сообщением.")



@router.callback_query(StateFilter(None), F.data == "contact:add_more")
async def add_more_contact(callback: CallbackQuery, state: FSMContext):
    user_id = await get_db_user_id(callback)
    filled_types = sort_contact_types(await get_filled_contact_types(user_id))
    missing_types = get_missing_contact_types(filled_types)

    await add_event(user_id, "contact_add_more_clicked")

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception as exc:
        logger.warning("Не удалось очистить inline-клавиатуру: %s", exc)

    if not missing_types:
        await callback.message.answer(
            "У вас уже заполнены все способы связи, больше ничего оставлять не нужно."
        )
        await callback.answer()
        return

    await state.clear()
    await state.update_data(
        db_user_id=user_id,
        contact_mode="new",
    )
    await state.set_state(ContactFlow.waiting_contact_type)

    await callback.message.answer(
        "Добавим еще один способ связи.",
        reply_markup=ReplyKeyboardRemove(),
    )
    await callback.message.answer(
        "Выберите, какой контакт хотите оставить:",
        reply_markup=contact_type_keyboard(missing_types),
    )
    await callback.answer()


@router.callback_query(StateFilter(None), F.data == "contact:edit")
async def edit_contact(callback: CallbackQuery, state: FSMContext):
    user_id = await get_db_user_id(callback)
    filled_types = sort_contact_types(await get_filled_contact_types(user_id))

    await add_event(user_id, "contact_edit_clicked")

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception as exc:
        logger.warning("Не удалось очистить inline-клавиатуру: %s", exc)

    if not filled_types:
        await callback.message.answer("Сначала оставьте хотя бы один способ связи.")
        await callback.answer()
        return

    await state.clear()

    if len(filled_types) == 1:
        contact_type = filled_types[0]

        await state.update_data(
            db_user_id=user_id,
            contact_mode="edit",
            contact_type=contact_type,
        )
        await state.set_state(ContactFlow.waiting_contact_value)

        await callback.message.answer(
            "Пришлите корректные данные.",
            reply_markup=ReplyKeyboardRemove(),
        )
        await callback.message.answer(CONTACT_TYPE_PROMPTS[contact_type])
        await callback.answer()
        return

    await state.update_data(
        db_user_id=user_id,
        contact_mode="edit",
    )
    await state.set_state(ContactFlow.waiting_contact_type)

    await callback.message.answer(
        "Выберите, какой способ связи хотите исправить:",
        reply_markup=ReplyKeyboardRemove(),
    )
    await callback.message.answer(
        "Выберите тип контакта:",
        reply_markup=contact_type_keyboard(filled_types),
    )
    await callback.answer()


@router.callback_query(F.data == "menu:materials")
async def send_materials(callback: CallbackQuery):
    await callback.message.answer("Вот материалы для ознакомления:")
    for f in MATERIAL_FILES:
        path = MATERIALS_DIR / f
        await callback.message.answer_document(FSInputFile(path, filename=f))
    await callback.answer()