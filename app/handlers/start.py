from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message

from app.db import (
    add_event,
    create_user_question,
    save_profile_field,
    save_scores,
    update_question_status,
    upsert_user,
)
from app.keyboards import (
    business_size_keyboard,
    main_menu_keyboard,
    motivation_keyboard,
    persistent_menu_reply_keyboard,
    question_feedback_keyboard,
    role_keyboard,
    sell_submenu_keyboard,
    timeframe_keyboard,
)
from app.materials import COMPARE_FILES, MATERIALS_DIR
from app.scoring import build_result_text, calculate_scores
from app.states import BotFlow, LeadFlow

router = Router()

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


async def safe_delete(message: Message):
    try:
        await message.delete()
    except Exception:
        pass


async def get_db_user_id(message_or_callback: Message | CallbackQuery) -> int:
    tg_user = message_or_callback.from_user
    return await upsert_user(
        telegram_id=tg_user.id,
        username=tg_user.username,
        first_name=tg_user.first_name,
        last_name=tg_user.last_name,
    )


async def send_main_menu(
    message: Message,
    user_id: int,
    *,
    show_keyboard_hint: bool = False,
):
    await add_event(user_id, "menu_shown")

    await message.answer(
        MENU_TEXT,
        reply_markup=main_menu_keyboard(),
    )

    if show_keyboard_hint:
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
        show_keyboard_hint=True,
    )


@router.message(Command("menu"))
@router.message(F.text == "Меню")
async def open_menu_from_text(message: Message, state: FSMContext):
    user_id = await get_db_user_id(message)
    await add_event(user_id, "menu_opened_from_text")
    await state.clear()

    await send_main_menu(
        message=message,
        user_id=user_id,
        show_keyboard_hint=False,
    )


@router.callback_query(F.data == "menu:sell")
async def open_sell_submenu(callback: CallbackQuery, state: FSMContext):
    user_id = await get_db_user_id(callback)
    await add_event(user_id, "sell_submenu_opened")
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
    await callback.message.answer(QUESTION_WAIT_TEXT)
    await callback.answer()


@router.callback_query(F.data == "menu:compare")
async def open_compare_flow(callback: CallbackQuery, state: FSMContext):
    user_id = await get_db_user_id(callback)
    await add_event(user_id, "compare_opened")
    await state.clear()

    await safe_delete(callback.message)

    await callback.message.answer(COMPARE_TEXT)

    for item in COMPARE_FILES:
        file_path = MATERIALS_DIR / item["local_name"]
        await callback.message.answer_document(
            FSInputFile(file_path, filename=item["display_name"])
        )

    await callback.answer()


@router.callback_query(F.data == "menu:call")
async def organize_call(callback: CallbackQuery, state: FSMContext):
    user_id = await get_db_user_id(callback)
    await add_event(user_id, "call_requested")
    await state.clear()

    await safe_delete(callback.message)
    await callback.message.answer("Созвон организован")
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
    except Exception:
        pass

    if action == "yes":
        await update_question_status(question_id, "resolved")
        await add_event(user_id, "question_feedback_yes", str(question_id))

        await callback.message.answer("Рады, что смогли помочь!")
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

    await callback.message.answer(TRACK_1_INTRO)
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

    await callback.message.answer(TRACK_2_INTRO)
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

    result_text = build_result_text(
        track=track,
        fit_score=fit_score,
        intent_score=intent_score,
        status=status,
    )

    await callback.message.edit_text(result_text)
    await callback.answer()
    await state.clear()