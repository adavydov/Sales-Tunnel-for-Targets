from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.db import add_event, save_profile_field, save_scores, upsert_user
from app.keyboards import (
    business_size_keyboard,
    compare_keyboard,
    motivation_keyboard,
    role_keyboard,
    timeframe_keyboard,
    track_keyboard,
)
from app.scoring import build_result_text, calculate_scores
from app.states import LeadFlow

router = Router()


async def get_db_user_id(message_or_callback) -> int:
    tg_user = message_or_callback.from_user
    return await upsert_user(
        telegram_id=tg_user.id,
        username=tg_user.username,
        first_name=tg_user.first_name,
        last_name=tg_user.last_name,
    )


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    user_id = await get_db_user_id(message)
    await add_event(user_id, "start")
    await state.clear()
    await state.set_state(LeadFlow.choosing_track)

    await message.answer(
        "Привет. Я помогу определить, какой сценарий вам ближе.\n\n"
        "Выберите вариант:",
        reply_markup=track_keyboard(),
    )


@router.callback_query(LeadFlow.choosing_track, F.data.startswith("track:"))
async def process_track(callback: CallbackQuery, state: FSMContext):
    user_id = await get_db_user_id(callback)
    action = callback.data.split(":", 1)[1]

    if action == "compare":
        await add_event(user_id, "compare_opened")
        await callback.message.edit_text(
            "Коротко:\n\n"
            "T1 — если вы рассматриваете продажу 100% бизнеса.\n"
            "T2 — если хотите остаться в роли управляющего партнёра и усилить позицию.\n\n"
            "Выберите основной трек:",
            reply_markup=compare_keyboard(),
        )
        await callback.answer()
        return

    await save_profile_field(user_id, "track", action)
    await add_event(user_id, "track_selected", action)

    await state.update_data(
        db_user_id=user_id,
        track=action,
    )
    await state.set_state(LeadFlow.role)

    await callback.message.edit_text(
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