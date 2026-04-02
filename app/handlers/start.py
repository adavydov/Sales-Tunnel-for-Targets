import logging
import re

from aiogram import F, Router
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from app.db import add_event, save_profile_field, upsert_user
from app.keyboards import menu_keyboard, persistent_main_keyboard, tool_consent_keyboard
from app.states import OnboardingFlow, ToolConsentFlow

router = Router()
logger = logging.getLogger(__name__)

URL_RE = re.compile(r"^(https?://)?(www\.)?[A-Za-z0-9\-]+(\.[A-Za-z0-9\-]+)+(/.*)?$", re.IGNORECASE)

ONBOARDING_PROMO_TEXT = (
    "🚀 <b>Добро пожаловать в AIVEL bot</b>\n\n"
    "Это удобный ассистент для компаний, где вы сможете:\n"
    "• получать таргетированные прогревы каждый день;\n"
    "• быстро запускать симуляции экономии;\n"
    "• использовать valuation-оценку для accounting firm;\n"
    "• находить кейсы, видео и полезные материалы.\n\n"
    "С этого момента вам доступен базовый функционал: каждый день в 14:00 будет приходить"
    " прогрев с материалами, ссылками и обновлениями."
)

TOOL_PLACEHOLDER_TEXT = (
    "Спасибо! Соглашения приняты ✅\n\n"
    "Инструмент пока в режиме заглушки."
    " На следующем шаге здесь будет полноценная интерактивная симуляция."
)

CONSENT_TEXT = (
    "Чтобы воспользоваться этим инструментом, подтвердите ознакомление с условиями:\n\n"
    "1. NDA from AIVEL side for user's confidential data input.\n"
    "2. Acceptance of terms including personal data privacy policy, "
    "acceptance for receive marketing communication."
)

MENU_TEXT = "Выберите раздел (пока везде заглушки):"


async def get_db_user_id(message_or_callback: Message | CallbackQuery) -> int:
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
    await state.clear()
    await state.update_data(db_user_id=user_id)
    await state.set_state(OnboardingFlow.company)

    await add_event(user_id, "start")
    await message.answer(
        "Введите название вашей компании.",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(OnboardingFlow.company, F.text)
async def onboarding_company(message: Message, state: FSMContext):
    company = message.text.strip()
    if not company:
        await message.answer("Название компании не может быть пустым. Введите его текстом.")
        return

    data = await state.get_data()
    user_id = data["db_user_id"]

    await save_profile_field(user_id, "company", company)
    await add_event(user_id, "onboarding_company_saved", company)

    await state.set_state(OnboardingFlow.website)
    await message.answer(
        "Прикрепите www-ссылку на сайт компании (если сайта нет, отправьте: Нет сайта)."
    )


@router.message(OnboardingFlow.company)
async def onboarding_company_invalid(message: Message):
    await message.answer("Пожалуйста, введите название компании текстом.")


@router.message(OnboardingFlow.website, F.text)
async def onboarding_website(message: Message, state: FSMContext):
    website_raw = message.text.strip()
    website_value = website_raw

    if website_raw.lower() in {"нет", "нет сайта", "no", "none", "-"}:
        website_value = "not_provided"
    elif not URL_RE.match(website_raw):
        await message.answer("Ссылка выглядит некорректно. Пример: www.company.com или https://company.com")
        return

    data = await state.get_data()
    user_id = data["db_user_id"]

    await save_profile_field(user_id, "company_website", website_value)
    await add_event(user_id, "onboarding_website_saved", website_value)

    await state.clear()
    await message.answer(ONBOARDING_PROMO_TEXT, parse_mode="HTML")
    await message.answer(
        "Готово! Основные кнопки уже на клавиатуре ниже.",
        reply_markup=persistent_main_keyboard(),
    )


@router.message(OnboardingFlow.website)
async def onboarding_website_invalid(message: Message):
    await message.answer("Пожалуйста, отправьте ссылку текстом или напишите «Нет сайта».")


@router.message(StateFilter(None), F.text == "Menu")
async def open_menu(message: Message):
    user_id = await get_db_user_id(message)
    await add_event(user_id, "menu_opened")
    await message.answer(MENU_TEXT, reply_markup=menu_keyboard())


@router.message(StateFilter(None), F.text == "Simulate Savings")
async def open_simulate_from_keyboard(message: Message, state: FSMContext):
    user_id = await get_db_user_id(message)
    await add_event(user_id, "tool_open_requested", "simulate")

    await state.clear()
    await state.update_data(db_user_id=user_id, tool_name="simulate", consent_nda=False, consent_terms=False)
    await state.set_state(ToolConsentFlow.waiting)

    await message.answer(
        CONSENT_TEXT,
        reply_markup=tool_consent_keyboard(False, False, "simulate"),
    )


@router.message(StateFilter(None), F.text == "Valuation simulator")
async def open_valuation_from_keyboard(message: Message, state: FSMContext):
    user_id = await get_db_user_id(message)
    await add_event(user_id, "tool_open_requested", "valuation")

    await state.clear()
    await state.update_data(db_user_id=user_id, tool_name="valuation", consent_nda=False, consent_terms=False)
    await state.set_state(ToolConsentFlow.waiting)

    await message.answer(
        CONSENT_TEXT,
        reply_markup=tool_consent_keyboard(False, False, "valuation"),
    )


@router.callback_query(F.data == "tool:simulate")
async def open_simulate_from_menu(callback: CallbackQuery, state: FSMContext):
    user_id = await get_db_user_id(callback)
    await add_event(user_id, "tool_open_requested", "simulate")

    await state.clear()
    await state.update_data(db_user_id=user_id, tool_name="simulate", consent_nda=False, consent_terms=False)
    await state.set_state(ToolConsentFlow.waiting)

    await callback.message.answer(
        CONSENT_TEXT,
        reply_markup=tool_consent_keyboard(False, False, "simulate"),
    )
    await callback.answer()


@router.callback_query(F.data == "tool:valuation")
async def open_valuation_from_menu(callback: CallbackQuery, state: FSMContext):
    user_id = await get_db_user_id(callback)
    await add_event(user_id, "tool_open_requested", "valuation")

    await state.clear()
    await state.update_data(db_user_id=user_id, tool_name="valuation", consent_nda=False, consent_terms=False)
    await state.set_state(ToolConsentFlow.waiting)

    await callback.message.answer(
        CONSENT_TEXT,
        reply_markup=tool_consent_keyboard(False, False, "valuation"),
    )
    await callback.answer()


@router.callback_query(ToolConsentFlow.waiting, F.data.startswith("consent:toggle:"))
async def toggle_consent(callback: CallbackQuery, state: FSMContext):
    key = callback.data.split(":")[-1]
    data = await state.get_data()

    nda_checked = data.get("consent_nda", False)
    terms_checked = data.get("consent_terms", False)
    tool_name = data.get("tool_name", "simulate")

    if key == "nda":
        nda_checked = not nda_checked
    elif key == "terms":
        terms_checked = not terms_checked

    await state.update_data(consent_nda=nda_checked, consent_terms=terms_checked)

    await callback.message.edit_reply_markup(
        reply_markup=tool_consent_keyboard(nda_checked, terms_checked, tool_name)
    )
    await callback.answer()


@router.callback_query(ToolConsentFlow.waiting, F.data.startswith("consent:submit:"))
async def submit_consent(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = data["db_user_id"]
    tool_name = data.get("tool_name", "simulate")

    nda_checked = data.get("consent_nda", False)
    terms_checked = data.get("consent_terms", False)

    if not nda_checked or not terms_checked:
        await callback.answer("Нужно отметить оба пункта перед продолжением.", show_alert=True)
        return

    await save_profile_field(user_id, f"{tool_name}_consent", "accepted")
    await add_event(user_id, "tool_consent_accepted", tool_name)

    await state.clear()
    await callback.message.answer(TOOL_PLACEHOLDER_TEXT, reply_markup=persistent_main_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("stub:"))
async def menu_stub(callback: CallbackQuery):
    await callback.answer("Раздел в разработке. Скоро добавим функционал.", show_alert=True)
