import logging
import re
from datetime import date, datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo

from aiogram import F, Router
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message, ReplyKeyboardRemove

from app.calendly import (
    CalendlyNotConfiguredError,
    CalendlyRequestError,
    book_slot,
    get_available_hour_slots,
    is_configured as calendly_is_configured,
    is_slot_available,
)
from app.config import MEETING_TIMEZONE
from app.config import GOOGLE_SHEETS_API_KEY, GOOGLE_SHEETS_RANGE, GOOGLE_SHEETS_SPREADSHEET_ID
from app.db import add_event, get_tool_consent, save_funnel_fields, save_profile_field, upsert_user
from app.events import EventsConfigError, EventsRequestError, fetch_events, format_events_message
from app.keyboards import (
    meeting_calendar_keyboard,
    calendly_meeting_keyboard,
    meeting_registration_check_keyboard,
    meeting_custom_time_keyboard,
    meeting_slots_keyboard,
    meeting_waiting_keyboard,
    menu_keyboard,
    persistent_main_keyboard,
    simulate_deep_assessment_keyboard,
    simulate_deep_wait_keyboard,
    simulate_mode_keyboard,
    simulate_plus3_advisory_keyboard,
    simulate_plus3_automation_keyboard,
    simulate_plus3_standardization_keyboard,
    simulate_growth_keyboard,
    simulate_mna_keyboard,
    simulate_contact_field_keyboard,
    simulate_contacts_choice_keyboard,
    simulate_precise_skip_keyboard,
    simulate_results_keyboard,
    simulate_skip_question_keyboard,
    tool_consent_keyboard,
)
from app.scoring import (
    calculate_express_operation_savings,
    calculate_precise_savings_from_express,
)
from app.states import MeetingBookingFlow, SimulateFlow, ToolConsentFlow

router = Router()
logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[2]

URL_RE = re.compile(r"^(https?://)?(www\.)?[A-Za-z0-9\-]+(\.[A-Za-z0-9\-]+)+(/.*)?$", re.IGNORECASE)

ONBOARDING_PROMO_TEXT = (
    "👋 Добро пожаловать в Aivel!\n"
    "Мы автоматизируем до 95% бухгалтерских операций с помощью AI. "
    "Забудьте о проблемах с наймом — фокусируйтесь на продажах и клиентах.\n\n"
    "Что здесь:\n"
    "📊 Новости, события, новые партнёры\n"
    "💰 Калькулятор вашей экономии\n"
    "📈 Оценка стоимости вашей фирмы\n"
    "📅 Запись на встречу со специалистом\n\n"
    "Выберите раздел в меню ниже 👇"
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

MENU_TEXT = "Меню бота:"
BOOK_MEETING_TEXT = "Давайте запишем вас на встречу в Calendly."
SIMULATE_MODE_TEXT = (
    "💰 <b>Калькулятор экономии с Aivel</b>\n\n"
    "Выберите уровень детализации расчёта:\n\n"
    "⚡ <b>Экспресс-оценка (1 минута)</b>\n"
    "2 вопроса → мгновенный результат\n"
    "Для первого знакомства и быстрой оценки порядка цифр\n\n"
    "📊 <b>Профессиональная оценка (60–90 минут)</b>\n"
    "Excel-опросник: ~45 полей данных → максимальная точность\n"
    "Полный финансовый анализ с моделированием ROI, NPV, и планом внедрения"
)
SIMULATE_PRO_TEXT = (
    "🎯 Серьёзно рассматриваете внедрение? Загрузите Excel — получите полный бизнес-кейс от нашей команды.\n"
    "📥 Скачать Excel-файл\n"
    "📤 Заполнили? Загрузить обратно или отправьте это на: success@aivel.ai\n"
    "После загрузки мы подготовим детальный бизнес-кейс и свяжемся с вами в течение 2 рабочих дней.\n\n"
    "📊 Что внутри Excel-опросника?\n\n"
    "1️⃣ Цифры (Лист 1) — 20 полей, 25-30 минут\n"
    "• Выручка и прибыль за 3 года\n"
    "• Структура клиентов и средний чек\n"
    "• Отток и концентрация выручки\n"
    "• Маржинальность и повторяемость\n\n"
    "2️⃣ Компания и рынок (Лист 2) — 15 полей, 10-15 минут\n"
    "• Профиль компании и юрструктура\n"
    "• Рыночная позиция и конкуренты\n"
    "• Структура услуг и допродажи\n"
    "• Технологии и автоматизация\n\n"
    "3️⃣ Основатели (Лист 3) — 10 полей, 5-10 минут\n"
    "• Состав собственников\n"
    "• Роль в операционке\n"
    "• Предпочтения по сделке\n"
    "• Интерес к M&A\n\n"
    "Итого: 45 полей, 30-40 минут\n"
    "Можно заполнять частями, сохранять, возвращаться. Все поля с подсказками и примерами."
)
SIMULATE_PRO_MISSING_TEXT = (
    "Не удалось найти Excel-файл в проекте.\n"
    "Пожалуйста, добавьте .xlsx в репозиторий (например, в app/assets/) и попробуйте снова."
)
STANDARDIZATION_LABELS = {
    "high": "Высокая",
    "medium": "Средняя",
    "low": "Низкая",
}
AUTOMATION_LABELS = {
    "none": "Нет, всё вручную",
    "partial": "Частично",
    "systems": "Да, есть системы",
}
ADVISORY_LABELS = {
    "lt10": "Менее 10%",
    "10_20": "10-20%",
    "gt20": "Более 20%",
}
WAIT_FILE_TEXT = (
    "Ожидаем ваш файл.\n\n"
    "Вы можете загрузить Excel сюда или нажать «Отправил по почте», если уже отправили на success@aivel.ai."
)
THANKS_DEEP_TEXT = "Спасибо! С вами свяжутся в течение 2 рабочих дней."
THANKS_TOOL_TEXT = "Спасибо, что воспользовались нашим инструментом, надеемся он оказался полезным."
MEETING_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
DEFAULT_EXPRESS_ACCOUNTANTS = 15
DEFAULT_EXPRESS_SALARY = 120000



async def get_db_user_id(message_or_callback: Message | CallbackQuery) -> int:
    tg_user = message_or_callback.from_user
    return await upsert_user(
        telegram_id=tg_user.id,
        username=tg_user.username,
        first_name=tg_user.first_name,
        last_name=tg_user.last_name,
    )


async def send_onboarding_complete(message: Message):
    await message.answer(ONBOARDING_PROMO_TEXT, parse_mode="HTML", reply_markup=persistent_main_keyboard())


def parse_positive_int(raw_value: str) -> int | None:
    normalized = raw_value.replace(" ", "").replace(",", "").replace("_", "")
    if not normalized.isdigit():
        return None
    value = int(normalized)
    return value if value > 0 else None


def format_mln_range(min_savings_rub: int, max_savings_rub: int) -> str:
    min_mln = round(min_savings_rub / 1_000_000)
    max_mln = round(max_savings_rub / 1_000_000)
    if max_mln < min_mln:
        max_mln = min_mln
    return f"{min_mln}-{max_mln} млн ₽/год"


def format_rub(value: float) -> str:
    return f"{int(round(value)):,}".replace(",", " ")


async def ask_precise_standardization_question(message: Message):
    await message.answer(
        "5️⃣ Насколько стандартизированы ваши процессы?\n"
        "“При высокой стандартизации вы достигнете результатов на 30% быстрее”\n\n"
        "Выберите вариант ответа:\n"
        "• Высокая стандартизация: есть регламенты, чек-листы, единая методология для всех бухгалтеров\n"
        "• Средняя стандартизация: базовые стандарты есть, но много ручной работы и решений “на месте”\n"
        "• Низкая стандартизация: каждый бухгалтер работает по-своему, процессы не описаны\n",
        parse_mode="HTML",
        reply_markup=simulate_plus3_standardization_keyboard(),
    )


async def send_express_result(message: Message, state: FSMContext):
    data = await state.get_data()
    accountants = int(data["express_accountants"])
    salary = int(data["express_salary"])
    result = calculate_express_operation_savings(accountants, salary)

    text = (
        "🎯 <b>Ваши результаты с Aivel:</b>\n\n"
        "Шаги расчёта через 6 месяцев и через 12 месяцев\n\n"
        "1. <b>Число высвобождаемых бухгалтеров</b>\n"
        f"• через 6 месяцев: <b>{result['released_6']}</b>\n"
        f"• через 12 месяцев: <b>{result['released_12']}</b>\n\n"
        "2. <b>Сохраняемая месячная зарплатная масса</b>\n"
        f"• через 6 месяцев: <b>{format_rub(result['payroll_saved_6'])} ₽ в месяц</b>\n"
        f"• через 12 месяцев: <b>{format_rub(result['payroll_saved_12'])} ₽ в месяц</b>\n\n"
        "3. <b>Новая стоимость операций на базе искусственного интеллекта</b>\n"
        f"• через 6 месяцев: <b>{format_rub(result['ai_cost_6'])} ₽ в месяц</b>\n"
        f"• через 12 месяцев: <b>{format_rub(result['ai_cost_12'])} ₽ в месяц</b>\n\n"
        "4. <b>Чистая экономия в месяц</b>\n"
        f"• через 6 месяцев: <b>{format_rub(result['net_6'])} ₽ в месяц</b>\n"
        f"• через 12 месяцев: <b>{format_rub(result['net_12'])} ₽ в месяц</b>\n\n"
        "⚠️ Это быстрая прикидка экономии на коленке. Для точного расчёта пройдите детальную оценку.\n"
        "Дисклеймер: стоимость услуг AIVEL в среднем составляет 1/5 от операций, "
        "основанных на ручном труде; данный расчёт не является коммерческим предложением, "
        "а представляет собой оценку эффекта от внедрения технологического комплекса AIVEL TECH SUITE."
    )

    user_id = data.get("db_user_id")
    if user_id:
        await save_funnel_fields(
            int(user_id),
            accountants_count=accountants,
            avg_salary=salary,
            express_saving_6=result["net_6"],
            express_saving_12=result["net_12"],
        )
        await add_event(
            int(user_id),
            "simulate_express_completed",
            f"accountants={accountants};salary={salary};net6={format_rub(result['net_6'])};net12={format_rub(result['net_12'])}",
        )

    await state.set_state(SimulateFlow.mode_select)
    await message.answer(text, parse_mode="HTML", reply_markup=simulate_results_keyboard())


def find_excel_template() -> Path | None:
    xlsx_candidates = sorted(PROJECT_ROOT.rglob("*.xlsx"))
    if not xlsx_candidates:
        return None

    preferred = [path for path in xlsx_candidates if "aivel" in path.name.lower() or "calculator" in path.name.lower()]
    return preferred[0] if preferred else xlsx_candidates[0]


def is_excel_filename(filename: str | None) -> bool:
    if not filename:
        return False
    lowered = filename.lower()
    return lowered.endswith(".xlsx") or lowered.endswith(".xls") or lowered.endswith(".xlsm")


async def send_simulate_mode_menu(target: Message | CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(SimulateFlow.mode_select)

    if isinstance(target, CallbackQuery):
        await target.message.answer(
            SIMULATE_MODE_TEXT,
            parse_mode="HTML",
            reply_markup=simulate_mode_keyboard(),
        )
        await target.answer()
        return

    await target.answer(
        SIMULATE_MODE_TEXT,
        parse_mode="HTML",
        reply_markup=simulate_mode_keyboard(),
    )


async def ensure_simulate_consent(callback: CallbackQuery, state: FSMContext) -> bool:
    user_id = await get_db_user_id(callback)
    already_accepted = await get_tool_consent(user_id, "simulate")
    if already_accepted:
        return True

    await open_tool_flow(callback, state, "simulate")
    return False


async def return_to_base_state(message: Message, state: FSMContext, text: str):
    await state.clear()
    await message.answer(text, reply_markup=persistent_main_keyboard())


async def delete_message_safe(message: Message):
    try:
        await message.delete()
    except TelegramBadRequest:
        return


async def start_meeting_booking(message: Message, state: FSMContext):
    if not calendly_is_configured():
        await message.answer(
            "Calendly пока не настроен. Проверьте CALENDLY_API_TOKEN и CALENDLY_EVENT_TYPE_URI.",
            reply_markup=persistent_main_keyboard(),
        )
        await state.clear()
        return

    await state.clear()
    await state.set_state(MeetingBookingFlow.waiting_email)
    await message.answer(
        "📅 Запись на встречу через Calendly.\n\n"
        "Отправьте, пожалуйста, ваш email, чтобы мы могли забронировать слот.",
        reply_markup=meeting_waiting_keyboard(),
    )


def format_slot_label(slot_dt: datetime) -> str:
    return slot_dt.strftime("%H:%M")


async def send_excel_and_wait_for_user(callback: CallbackQuery, state: FSMContext):
    excel_path = find_excel_template()
    if excel_path is None:
        await callback.message.answer(SIMULATE_PRO_MISSING_TEXT)
        await callback.answer("Excel-файл пока не найден", show_alert=True)
        return

    await callback.message.answer(SIMULATE_PRO_TEXT)
    await callback.message.answer_document(
        document=FSInputFile(excel_path),
        caption="📥 Excel-опросник для профессиональной оценки",
    )
    user_id = await get_db_user_id(callback)
    await save_funnel_fields(user_id, file_downloaded=True)
    await add_event(user_id, "simulate_pro_excel_sent", excel_path.name)
    await state.set_state(SimulateFlow.precise_wait_excel)
    await callback.message.answer(WAIT_FILE_TEXT, reply_markup=simulate_deep_wait_keyboard())
    await callback.answer()


async def open_tool_flow(message_or_callback: Message | CallbackQuery, state: FSMContext, tool_name: str):
    user_id = await get_db_user_id(message_or_callback)
    await add_event(user_id, "tool_open_requested", tool_name)

    already_accepted = await get_tool_consent(user_id, tool_name)
    if already_accepted:
        if tool_name == "simulate":
            await send_simulate_mode_menu(message_or_callback, state)
            return

        if isinstance(message_or_callback, CallbackQuery):
            await message_or_callback.message.answer(
                TOOL_PLACEHOLDER_TEXT,
                reply_markup=persistent_main_keyboard(),
            )
            await message_or_callback.answer()
            return

        await message_or_callback.answer(
            TOOL_PLACEHOLDER_TEXT,
            reply_markup=persistent_main_keyboard(),
        )
        return

    await state.clear()
    await state.update_data(
        db_user_id=user_id,
        tool_name=tool_name,
        consent_nda=False,
        consent_terms=False,
    )
    await state.set_state(ToolConsentFlow.waiting)

    if isinstance(message_or_callback, CallbackQuery):
        await message_or_callback.message.answer(
            CONSENT_TEXT,
            reply_markup=tool_consent_keyboard(False, False, tool_name),
        )
        await message_or_callback.message.answer(
            " ",
            reply_markup=ReplyKeyboardRemove(),
        )
        await message_or_callback.answer()
        return

    await message_or_callback.answer(
        CONSENT_TEXT,
        reply_markup=tool_consent_keyboard(False, False, tool_name),
    )
    await message_or_callback.answer(
        " ",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    user_id = await get_db_user_id(message)
    await state.clear()
    await add_event(user_id, "start")
    await send_onboarding_complete(message)


@router.message(StateFilter(None), F.text == "Меню бота")
async def open_menu(message: Message):
    user_id = await get_db_user_id(message)
    await add_event(user_id, "menu_opened")
    await message.answer(MENU_TEXT, reply_markup=menu_keyboard())


@router.message(StateFilter(None), F.text == "Калькулятор экономии")
async def open_simulate_from_keyboard(message: Message, state: FSMContext):
    await open_tool_flow(message, state, "simulate")


@router.message(StateFilter(None), F.text == "Оценка стоимости фирмы")
async def open_valuation_from_keyboard(message: Message, state: FSMContext):
    await open_tool_flow(message, state, "valuation")


@router.callback_query(F.data == "tool:simulate")
async def open_simulate_from_menu(callback: CallbackQuery, state: FSMContext):
    await open_tool_flow(callback, state, "simulate")


@router.callback_query(F.data == "tool:valuation")
async def open_valuation_from_menu(callback: CallbackQuery, state: FSMContext):
    await open_tool_flow(callback, state, "valuation")


@router.callback_query(ToolConsentFlow.waiting, F.data == "consent:back")
async def consent_back(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = data["db_user_id"]
    tool_name = data.get("tool_name", "unknown")

    await add_event(user_id, "tool_consent_back", tool_name)
    await state.clear()
    await callback.message.delete()
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

    await callback.message.delete()
    if tool_name == "simulate":
        await send_simulate_mode_menu(callback, state)
        return

    await state.clear()
    await callback.message.answer(TOOL_PLACEHOLDER_TEXT, reply_markup=persistent_main_keyboard())
    await callback.answer()


@router.callback_query(F.data == "stub:book_meeting")
async def book_meeting(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer(
        "Откройте Calendly по кнопке ниже 👇",
        reply_markup=calendly_meeting_keyboard(),
        disable_web_page_preview=True,
    )
    await callback.message.answer(
        "Вы зарегистрировались?",
        reply_markup=meeting_registration_check_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "stub:events")
async def show_events(callback: CallbackQuery):
    await callback.answer()
    loading_message = await callback.message.answer("⏳ Собираем информацию о ближайших мероприятиях...")

    try:
        events = fetch_events(
            spreadsheet_id=str(GOOGLE_SHEETS_SPREADSHEET_ID or ""),
            api_key=str(GOOGLE_SHEETS_API_KEY or ""),
            sheet_range=GOOGLE_SHEETS_RANGE,
        )
    except EventsConfigError:
        await delete_message_safe(loading_message)
        await callback.message.answer(
            "⚠️ Раздел мероприятий временно недоступен: не настроен доступ к Google Sheets."
        )
        return
    except EventsRequestError as exc:
        await delete_message_safe(loading_message)
        await callback.message.answer(f"⚠️ Не удалось получить данные мероприятий. {exc}")
        return

    await delete_message_safe(loading_message)
    await callback.message.answer(
        format_events_message(events),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )


@router.callback_query(F.data == "meeting:external:yes")
async def meeting_external_confirmed(callback: CallbackQuery, state: FSMContext):
    await delete_message_safe(callback.message)
    user_id = await get_db_user_id(callback)
    await save_funnel_fields(user_id, meeting_booked=True)
    await add_event(user_id, "meeting_external_confirmed", "yes")
    await return_to_base_state(callback.message, state, "Отлично! Спасибо за регистрацию на встречу 🙌")
    await callback.answer()


@router.callback_query(F.data == "meeting:external:no")
async def meeting_external_declined(callback: CallbackQuery, state: FSMContext):
    await delete_message_safe(callback.message)
    user_id = await get_db_user_id(callback)
    await add_event(user_id, "meeting_external_confirmed", "no")
    await return_to_base_state(callback.message, state, "Хорошо, вернули вас в главное меню.")
    await callback.answer()


@router.callback_query(F.data == "meeting:noop")
async def meeting_noop(callback: CallbackQuery):
    await callback.answer()


@router.callback_query(
    MeetingBookingFlow.waiting_email,
    F.data == "meeting:back",
)
@router.callback_query(
    MeetingBookingFlow.waiting_date,
    F.data == "meeting:back",
)
@router.callback_query(
    MeetingBookingFlow.waiting_custom_time,
    F.data == "meeting:back",
)
@router.callback_query(SimulateFlow.precise_wait_excel, F.data == "meeting:back")
async def meeting_back(callback: CallbackQuery, state: FSMContext):
    await return_to_base_state(callback.message, state, "Спасибо, вернёмся к этому позже.")
    await callback.answer()


@router.message(MeetingBookingFlow.waiting_email, F.text)
async def meeting_email_step(message: Message, state: FSMContext):
    email = message.text.strip().lower()
    if not MEETING_EMAIL_RE.match(email):
        await message.answer("Пожалуйста, отправьте корректный email. Пример: name@company.com")
        return

    now = datetime.now(ZoneInfo(MEETING_TIMEZONE))
    await state.update_data(meeting_email=email)
    user_id = await get_db_user_id(message)
    await save_funnel_fields(user_id, contact_email=email)
    await state.set_state(MeetingBookingFlow.waiting_date)
    await message.answer(
        "Выберите дату созвона:",
        reply_markup=meeting_calendar_keyboard(now.year, now.month),
    )


@router.callback_query(MeetingBookingFlow.waiting_date, F.data.startswith("meeting:date:nav:"))
async def meeting_date_nav(callback: CallbackQuery):
    _, _, _, ym = callback.data.split(":")
    year_str, month_str = ym.split("-")
    year, month = int(year_str), int(month_str)
    await callback.message.edit_reply_markup(reply_markup=meeting_calendar_keyboard(year, month))
    await callback.answer()


@router.callback_query(MeetingBookingFlow.waiting_date, F.data.startswith("meeting:date:pick:"))
async def meeting_date_pick(callback: CallbackQuery, state: FSMContext):
    selected = date.fromisoformat(callback.data.split(":")[-1])
    await state.update_data(meeting_date=selected.isoformat())

    try:
        slots = get_available_hour_slots(selected)
    except (CalendlyRequestError, CalendlyNotConfiguredError) as exc:
        await callback.message.answer(f"Не удалось получить слоты Calendly: {exc}")
        await callback.answer()
        return

    first_five = [format_slot_label(slot) for slot in slots[:5]]
    await state.update_data(meeting_slot_candidates=first_five)
    await callback.message.answer(
        "Свободные слоты на выбранную дату:",
        reply_markup=meeting_slots_keyboard(first_five),
    )
    await callback.answer()


@router.callback_query(MeetingBookingFlow.waiting_date, F.data.startswith("meeting:slot:"))
async def meeting_slot_pick(callback: CallbackQuery, state: FSMContext):
    value = callback.data.removeprefix("meeting:slot:")
    if value == "other":
        await state.set_state(MeetingBookingFlow.waiting_custom_time)
        await callback.message.answer(
            "Выберите удобное время:",
            reply_markup=meeting_custom_time_keyboard(),
        )
        await callback.answer()
        return

    data = await state.get_data()
    selected_date = date.fromisoformat(data["meeting_date"])
    hour, minute = map(int, value.split("-") if "-" in value else value.split(":"))
    slot_dt = datetime.combine(selected_date, time(hour, minute), ZoneInfo(MEETING_TIMEZONE))

    try:
        if not is_slot_available(slot_dt):
            await callback.message.answer("Этот слот уже недоступен. Выберите другое время.")
            await callback.answer()
            return

        tg_user = callback.from_user
        invitee_name = f"{tg_user.first_name or ''} {tg_user.last_name or ''}".strip() or "Aivel Client"
        booking = book_slot(slot_dt, invitee_name, str(data["meeting_email"]))
    except CalendlyRequestError as exc:
        await callback.message.answer(f"Не удалось забронировать слот: {exc}")
        await callback.answer()
        return

    user_id = await get_db_user_id(callback)
    await save_funnel_fields(user_id, meeting_booked=True)
    await add_event(user_id, "meeting_booked", slot_dt.isoformat())
    await return_to_base_state(
        callback.message,
        state,
        f"✅ Встреча забронирована!\nСсылка: {booking.booking_url}",
    )
    await callback.answer()


@router.callback_query(MeetingBookingFlow.waiting_custom_time, F.data.startswith("meeting:time:"))
async def meeting_custom_time_pick(callback: CallbackQuery, state: FSMContext):
    _, _, hh, mm = callback.data.split(":")
    data = await state.get_data()
    selected_date = date.fromisoformat(data["meeting_date"])
    slot_dt = datetime.combine(selected_date, time(int(hh), int(mm)), ZoneInfo(MEETING_TIMEZONE))

    try:
        if not is_slot_available(slot_dt):
            await callback.message.answer(
                "Слот недоступен. Выберите другое время:",
                reply_markup=meeting_custom_time_keyboard(),
            )
            await callback.answer()
            return

        tg_user = callback.from_user
        invitee_name = f"{tg_user.first_name or ''} {tg_user.last_name or ''}".strip() or "Aivel Client"
        booking = book_slot(slot_dt, invitee_name, str(data["meeting_email"]))
    except CalendlyRequestError as exc:
        await callback.message.answer(f"Не удалось забронировать слот: {exc}")
        await callback.answer()
        return

    user_id = await get_db_user_id(callback)
    await save_funnel_fields(user_id, meeting_booked=True)
    await add_event(user_id, "meeting_booked_custom", slot_dt.isoformat())
    await return_to_base_state(
        callback.message,
        state,
        f"✅ Встреча забронирована!\nСсылка: {booking.booking_url}",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("stub:"))
async def menu_stub(callback: CallbackQuery):
    await callback.answer("Раздел в разработке. Скоро добавим функционал.", show_alert=True)


@router.callback_query(SimulateFlow.mode_select, F.data == "simulate:mode:menu")
async def simulate_mode_menu(callback: CallbackQuery, state: FSMContext):
    await send_simulate_mode_menu(callback, state)


@router.callback_query(SimulateFlow.mode_select, F.data == "simulate:back")
async def simulate_back_to_main(callback: CallbackQuery, state: FSMContext):
    await return_to_base_state(callback.message, state, THANKS_TOOL_TEXT)
    await callback.answer()


@router.callback_query(SimulateFlow.mode_select, F.data == "simulate:mode:express")
async def simulate_mode_express(callback: CallbackQuery, state: FSMContext):
    if not await ensure_simulate_consent(callback, state):
        return

    user_id = await get_db_user_id(callback)
    await add_event(user_id, "simulate_mode_selected", "express")

    await state.update_data(db_user_id=user_id)
    await state.set_state(SimulateFlow.express_accountants)
    await callback.message.answer(
        "⚡ <b>Экспресс-оценка</b>\n\nОтветьте на 2 простых вопроса.\n\n"
        "1️⃣ Сколько у вас бухгалтеров (чел.) задействовано в выполнении следующих операций:\n"
        "• Обработка входящих запросов и документов\n"
        "• Первичные документы\n"
        "• Акты сверки\n"
        "• Работа с банк-клиентом\n\n"
        "Напишите свой ответ сообщением.\n"
        f"Например: {DEFAULT_EXPRESS_ACCOUNTANTS}",
        parse_mode="HTML",
        reply_markup=simulate_skip_question_keyboard("accountants"),
    )
    await callback.answer()


@router.callback_query(SimulateFlow.mode_select, F.data == "simulate:mode:precise")
async def simulate_mode_precise(callback: CallbackQuery, state: FSMContext):
    if not await ensure_simulate_consent(callback, state):
        return

    user_id = await get_db_user_id(callback)
    await add_event(user_id, "simulate_mode_selected", "precise")

    data = await state.get_data()
    await state.update_data(
        precise_accountants=int(data.get("express_accountants", DEFAULT_EXPRESS_ACCOUNTANTS)),
        precise_salary=int(data.get("express_salary", DEFAULT_EXPRESS_SALARY)),
    )
    await state.set_state(SimulateFlow.precise_advisory)
    await callback.message.answer(
        "✅ <b>Точная оценка</b>\n\n"
        "3️⃣ Какой % клиентов требует нестандартных консультаций / advisory работы?\n"
        "Сложные налоговые кейсы, реструктуризация, M&A-поддержка, специальные отраслевые требования\n\n"
        "Выберите вариант ответа:\n"
        "• Менее 10% — почти все клиенты стандартные\n"
        "• 10-20% — есть несколько сложных клиентов\n"
        "• >20% — заметная доля advisory\n",
        parse_mode="HTML",
        reply_markup=simulate_plus3_advisory_keyboard(),
    )
    await callback.answer()


@router.callback_query(SimulateFlow.mode_select, F.data == "simulate:mode:pro")
async def simulate_mode_pro(callback: CallbackQuery, state: FSMContext):
    if not await ensure_simulate_consent(callback, state):
        return

    user_id = await get_db_user_id(callback)
    await add_event(user_id, "simulate_mode_selected", "pro")

    await send_excel_and_wait_for_user(callback, state)


@router.message(SimulateFlow.express_accountants, F.text)
async def simulate_express_accountants(message: Message, state: FSMContext):
    accountants = parse_positive_int(message.text.strip())
    if accountants is None:
        await message.answer("Введите количество бухгалтеров целым числом. Пример: 15")
        return

    await state.update_data(express_accountants=accountants)
    user_id = (await state.get_data()).get("db_user_id")
    if user_id:
        await save_funnel_fields(int(user_id), accountants_count=accountants)
    await state.set_state(SimulateFlow.express_salary)
    await message.answer(
        "2️⃣ Средняя зарплата бухгалтера (₽/мес, включая налоги)?\n\n"
        "Напишите свой ответ сообщением.\n"
        f"Например: {DEFAULT_EXPRESS_SALARY}",
        parse_mode="HTML",
        reply_markup=simulate_skip_question_keyboard("salary"),
    )


@router.callback_query(SimulateFlow.express_accountants, F.data == "simulate:express:skip:accountants")
async def simulate_express_skip_accountants(callback: CallbackQuery, state: FSMContext):
    await state.update_data(express_accountants=DEFAULT_EXPRESS_ACCOUNTANTS)
    user_id = (await state.get_data()).get("db_user_id")
    if user_id:
        await save_funnel_fields(int(user_id), accountants_count=DEFAULT_EXPRESS_ACCOUNTANTS)
    await state.set_state(SimulateFlow.express_salary)
    await callback.message.answer(
        "2️⃣ Средняя зарплата бухгалтера (₽/мес, включая налоги)?\n\n"
        "Напишите свой ответ сообщением.\n"
        f"Например: {DEFAULT_EXPRESS_SALARY}",
        parse_mode="HTML",
        reply_markup=simulate_skip_question_keyboard("salary"),
    )
    await callback.answer()


@router.message(SimulateFlow.express_salary, F.text)
async def simulate_express_salary(message: Message, state: FSMContext):
    salary = parse_positive_int(message.text.strip())
    if salary is None:
        await message.answer("Введите среднюю зарплату бухгалтера числом в ₽. Пример: 80000")
        return

    await state.update_data(express_salary=salary)
    user_id = (await state.get_data()).get("db_user_id")
    if user_id:
        await save_funnel_fields(int(user_id), avg_salary=salary)
    await send_express_result(message, state)


@router.callback_query(SimulateFlow.express_salary, F.data == "simulate:express:skip:salary")
async def simulate_express_skip_salary(callback: CallbackQuery, state: FSMContext):
    await state.update_data(express_salary=DEFAULT_EXPRESS_SALARY)
    user_id = (await state.get_data()).get("db_user_id")
    if user_id:
        await save_funnel_fields(int(user_id), avg_salary=DEFAULT_EXPRESS_SALARY)
    await send_express_result(callback.message, state)
    await callback.answer()


@router.message(SimulateFlow.precise_clients, F.text & (F.text.casefold() != "пропустить"))
async def simulate_precise_clients(message: Message, state: FSMContext):
    clients = parse_positive_int(message.text.strip())
    if clients is None:
        await message.answer("Введите количество активных клиентов целым числом. Пример: 120")
        return

    await state.update_data(precise_clients=clients)
    user_id = (await state.get_data()).get("db_user_id")
    if user_id:
        await save_funnel_fields(int(user_id), active_clients_count=clients)
    await state.set_state(SimulateFlow.precise_contacts)
    await message.answer(
        "Поделитесь с нами вашими контактными данными (Ваше имя, Email, Телефон, Компания, Вебсайт)\n",
        parse_mode="HTML",
        reply_markup=simulate_contacts_choice_keyboard(),
    )


@router.message(SimulateFlow.precise_margin, F.text & (F.text.casefold() != "пропустить"))
async def simulate_precise_margin(message: Message, state: FSMContext):
    margin = parse_positive_int(message.text.strip())
    if margin is None or margin > 100:
        await message.answer("Введите валовую маржу числом от 1 до 100. Пример: 35")
        return

    await state.update_data(precise_margin=margin)
    user_id = (await state.get_data()).get("db_user_id")
    if user_id:
        await save_funnel_fields(int(user_id), margin_percent=margin)
    await finalize_precise_assessment(message, state)


@router.callback_query(SimulateFlow.mode_select, F.data.in_({"simulate:precise:more", "simulate:precise:more5"}))
async def simulate_precise_more(callback: CallbackQuery, state: FSMContext):
    if not await ensure_simulate_consent(callback, state):
        return

    data = await state.get_data()
    await state.update_data(
        precise_accountants=int(data.get("express_accountants", DEFAULT_EXPRESS_ACCOUNTANTS)),
        precise_salary=int(data.get("express_salary", DEFAULT_EXPRESS_SALARY)),
    )
    await state.set_state(SimulateFlow.precise_advisory)
    await callback.message.answer(
        "✅ <b>Точная оценка</b>\n\n"
        "3️⃣ Какой % клиентов требует нестандартных консультаций / advisory работы?\n"
        "Сложные налоговые кейсы, реструктуризация, M&A-поддержка, специальные отраслевые требования\n\n"
        "Выберите вариант ответа:\n"
        "• Менее 10% — почти все клиенты стандартные\n"
        "• 10-20% — есть несколько сложных клиентов\n"
        "• >20% — заметная доля advisory\n",
        parse_mode="HTML",
        reply_markup=simulate_plus3_advisory_keyboard(),
    )
    await callback.answer()


@router.callback_query(SimulateFlow.precise_standardization, F.data.startswith("simulate:plus3:std:"))
async def simulate_plus3_standardization(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[-1]
    if value != "skip" and value not in STANDARDIZATION_LABELS:
        await callback.answer("Некорректный вариант", show_alert=True)
        return

    normalized = "medium" if value == "skip" else value
    await state.update_data(plus3_standardization=normalized)
    user_id = (await state.get_data()).get("db_user_id")
    if user_id:
        await save_funnel_fields(int(user_id), standardization_level=normalized)
    await state.set_state(SimulateFlow.precise_automation)
    await callback.message.answer(
        "6️⃣ Используете ли вы сейчас какие-то инструменты автоматизации?\n\n",
        parse_mode="HTML",
        reply_markup=simulate_plus3_automation_keyboard(),
    )
    await callback.answer()


@router.callback_query(SimulateFlow.precise_automation, F.data.startswith("simulate:plus3:auto:"))
async def simulate_plus3_automation(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[-1]
    if value != "skip" and value not in AUTOMATION_LABELS:
        await callback.answer("Некорректный вариант", show_alert=True)
        return

    normalized = "partial" if value == "skip" else value
    await state.update_data(plus3_automation=normalized)
    user_id = (await state.get_data()).get("db_user_id")
    if user_id:
        await save_funnel_fields(int(user_id), automation_level=normalized)
    await state.set_state(SimulateFlow.precise_margin)
    await callback.message.answer(
        "7️⃣ Текущая валовая маржа (%)?\n\n"
        "Напишите свой ответ сообщением.\n"
        "Например: 35",
        parse_mode="HTML",
        reply_markup=simulate_precise_skip_keyboard("simulate:precise:margin:skip"),
    )
    await callback.answer()


@router.callback_query(SimulateFlow.precise_advisory, F.data.startswith("simulate:plus3:advisory:"))
async def simulate_plus3_advisory(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[-1]
    if value != "skip" and value not in ADVISORY_LABELS:
        await callback.answer("Некорректный вариант", show_alert=True)
        return

    normalized = "10_20" if value == "skip" else value
    await state.update_data(plus3_advisory=normalized)
    user_id = (await state.get_data()).get("db_user_id")
    if user_id:
        await save_funnel_fields(int(user_id), advisory_band=normalized)
    await state.set_state(SimulateFlow.precise_clients)
    await callback.message.answer(
        "4️⃣ Количество активных клиентов?\n\n"
        "Напишите свой ответ сообщением.\n"
        "Например: 120",
        parse_mode="HTML",
        reply_markup=simulate_precise_skip_keyboard("simulate:precise:clients:skip"),
    )
    await callback.answer()


@router.callback_query(SimulateFlow.precise_clients, F.data == "simulate:precise:clients:skip")
async def simulate_precise_clients_skip(callback: CallbackQuery, state: FSMContext):
    await state.update_data(precise_clients=0)
    user_id = (await state.get_data()).get("db_user_id")
    if user_id:
        await save_funnel_fields(int(user_id), active_clients_count=0)
    await state.set_state(SimulateFlow.precise_contacts)
    await callback.message.answer(
        "Поделитесь с нами вашими контактными данными (Ваше имя, Email, Телефон, Компания, Вебсайт)\n",
        parse_mode="HTML",
        reply_markup=simulate_contacts_choice_keyboard(),
    )
    await callback.answer()


@router.message(SimulateFlow.precise_clients, F.text.casefold() == "пропустить")
async def simulate_precise_clients_skip_text(message: Message, state: FSMContext):
    await state.update_data(precise_clients=0)
    user_id = (await state.get_data()).get("db_user_id")
    if user_id:
        await save_funnel_fields(int(user_id), active_clients_count=0)
    await state.set_state(SimulateFlow.precise_contacts)
    await message.answer(
        "Поделитесь с нами вашими контактными данными (Ваше имя, Email, Телефон, Компания, Вебсайт)\n",
        parse_mode="HTML",
        reply_markup=simulate_contacts_choice_keyboard(),
    )


@router.callback_query(SimulateFlow.precise_contacts, F.data == "simulate:contacts:skip")
async def simulate_contacts_skip(callback: CallbackQuery, state: FSMContext):
    await delete_message_safe(callback.message)
    await state.update_data(precise_contacts="")
    await state.set_state(SimulateFlow.precise_standardization)
    await ask_precise_standardization_question(callback.message)
    await callback.answer()


@router.callback_query(SimulateFlow.precise_contacts, F.data == "simulate:contacts:share")
async def simulate_contacts_share(callback: CallbackQuery, state: FSMContext):
    await delete_message_safe(callback.message)
    await state.set_state(SimulateFlow.precise_contact_name)
    await callback.message.answer(
        "Введите ваше имя:",
        reply_markup=simulate_contact_field_keyboard("simulate:contacts:name:skip"),
    )
    await callback.answer()


@router.message(SimulateFlow.precise_contact_name, F.text)
async def simulate_contact_name(message: Message, state: FSMContext):
    name = message.text.strip()
    await state.update_data(contact_name=name)
    user_id = (await state.get_data()).get("db_user_id")
    if user_id:
        await save_funnel_fields(int(user_id), contact_name=name)
    await state.set_state(SimulateFlow.precise_contact_email)
    await message.answer(
        "Введите ваш Email:",
        reply_markup=simulate_contact_field_keyboard("simulate:contacts:email:skip"),
    )


@router.callback_query(SimulateFlow.precise_contact_name, F.data == "simulate:contacts:name:skip")
async def simulate_contact_name_skip(callback: CallbackQuery, state: FSMContext):
    await state.update_data(contact_name="")
    user_id = (await state.get_data()).get("db_user_id")
    if user_id:
        await save_funnel_fields(int(user_id), contact_name="")
    await state.set_state(SimulateFlow.precise_contact_email)
    await callback.message.answer(
        "Введите ваш Email:",
        reply_markup=simulate_contact_field_keyboard("simulate:contacts:email:skip"),
    )
    await callback.answer()


@router.message(SimulateFlow.precise_contact_email, F.text)
async def simulate_contact_email(message: Message, state: FSMContext):
    email = message.text.strip()
    await state.update_data(contact_email=email)
    user_id = (await state.get_data()).get("db_user_id")
    if user_id:
        await save_funnel_fields(int(user_id), contact_email=email)
    await state.set_state(SimulateFlow.precise_contact_phone)
    await message.answer(
        "Введите ваш телефон:",
        reply_markup=simulate_contact_field_keyboard("simulate:contacts:phone:skip"),
    )


@router.callback_query(SimulateFlow.precise_contact_email, F.data == "simulate:contacts:email:skip")
async def simulate_contact_email_skip(callback: CallbackQuery, state: FSMContext):
    await state.update_data(contact_email="")
    user_id = (await state.get_data()).get("db_user_id")
    if user_id:
        await save_funnel_fields(int(user_id), contact_email="")
    await state.set_state(SimulateFlow.precise_contact_phone)
    await callback.message.answer(
        "Введите ваш телефон:",
        reply_markup=simulate_contact_field_keyboard("simulate:contacts:phone:skip"),
    )
    await callback.answer()


@router.message(SimulateFlow.precise_contact_phone, F.text)
async def simulate_contact_phone(message: Message, state: FSMContext):
    phone = message.text.strip()
    await state.update_data(contact_phone=phone)
    user_id = (await state.get_data()).get("db_user_id")
    if user_id:
        await save_funnel_fields(int(user_id), contact_phone=phone)
    await state.set_state(SimulateFlow.precise_contact_company)
    await message.answer(
        "Введите название вашей компании:",
        reply_markup=simulate_contact_field_keyboard("simulate:contacts:company:skip"),
    )


@router.callback_query(SimulateFlow.precise_contact_phone, F.data == "simulate:contacts:phone:skip")
async def simulate_contact_phone_skip(callback: CallbackQuery, state: FSMContext):
    await state.update_data(contact_phone="")
    user_id = (await state.get_data()).get("db_user_id")
    if user_id:
        await save_funnel_fields(int(user_id), contact_phone="")
    await state.set_state(SimulateFlow.precise_contact_company)
    await callback.message.answer(
        "Введите название вашей компании:",
        reply_markup=simulate_contact_field_keyboard("simulate:contacts:company:skip"),
    )
    await callback.answer()


@router.message(SimulateFlow.precise_contact_company, F.text)
async def simulate_contact_company(message: Message, state: FSMContext):
    company = message.text.strip()
    await state.update_data(contact_company=company)
    user_id = (await state.get_data()).get("db_user_id")
    if user_id:
        await save_profile_field(int(user_id), "company", company)
    await state.set_state(SimulateFlow.precise_contact_website)
    await message.answer(
        "Введите сайт вашей компании:",
        reply_markup=simulate_contact_field_keyboard("simulate:contacts:website:skip"),
    )


@router.callback_query(SimulateFlow.precise_contact_company, F.data == "simulate:contacts:company:skip")
async def simulate_contact_company_skip(callback: CallbackQuery, state: FSMContext):
    await state.update_data(contact_company="")
    user_id = (await state.get_data()).get("db_user_id")
    if user_id:
        await save_profile_field(int(user_id), "company", "")
    await state.set_state(SimulateFlow.precise_contact_website)
    await callback.message.answer(
        "Введите сайт вашей компании:",
        reply_markup=simulate_contact_field_keyboard("simulate:contacts:website:skip"),
    )
    await callback.answer()


@router.message(SimulateFlow.precise_contact_website, F.text)
async def simulate_contact_website(message: Message, state: FSMContext):
    website_raw = message.text.strip()
    if not URL_RE.match(website_raw):
        await message.answer("Ссылка выглядит некорректно. Пример: www.company.com или https://company.com")
        return

    await state.update_data(contact_website=website_raw)
    user_id = (await state.get_data()).get("db_user_id")
    if user_id:
        await save_profile_field(int(user_id), "company_website", website_raw)

    data = await state.get_data()
    await state.update_data(
        precise_contacts=(
            f"name={data.get('contact_name', '')}|email={data.get('contact_email', '')}|"
            f"phone={data.get('contact_phone', '')}|company={data.get('contact_company', '')}|"
            f"website={website_raw}"
        ),
    )
    await state.set_state(SimulateFlow.precise_standardization)
    await ask_precise_standardization_question(message)


@router.callback_query(SimulateFlow.precise_contact_website, F.data == "simulate:contacts:website:skip")
async def simulate_contact_website_skip(callback: CallbackQuery, state: FSMContext):
    await state.update_data(contact_website="")
    user_id = (await state.get_data()).get("db_user_id")
    if user_id:
        await save_profile_field(int(user_id), "company_website", "")
    data = await state.get_data()
    await state.update_data(
        precise_contacts=(
            f"name={data.get('contact_name', '')}|email={data.get('contact_email', '')}|"
            f"phone={data.get('contact_phone', '')}|company={data.get('contact_company', '')}|website="
        ),
    )
    await state.set_state(SimulateFlow.precise_standardization)
    await ask_precise_standardization_question(callback.message)
    await callback.answer()


@router.message(SimulateFlow.precise_margin, F.text.casefold() == "пропустить")
async def simulate_precise_margin_skip(message: Message, state: FSMContext):
    await state.update_data(precise_margin=0)
    user_id = (await state.get_data()).get("db_user_id")
    if user_id:
        await save_funnel_fields(int(user_id), margin_percent=0)
    await finalize_precise_assessment(message, state)


@router.callback_query(SimulateFlow.precise_margin, F.data == "simulate:precise:margin:skip")
async def simulate_precise_margin_skip_callback(callback: CallbackQuery, state: FSMContext):
    await state.update_data(precise_margin=0)
    user_id = (await state.get_data()).get("db_user_id")
    if user_id:
        await save_funnel_fields(int(user_id), margin_percent=0)
    await finalize_precise_assessment(callback.message, state)
    await callback.answer()


async def finalize_precise_assessment(target: Message | CallbackQuery, state: FSMContext):
    data = await state.get_data()
    express_result = calculate_express_operation_savings(
        int(data["precise_accountants"]),
        int(data["precise_salary"]),
    )
    precise_result = calculate_precise_savings_from_express(
        express_result=express_result,
        standardization_band=str(data.get("plus3_standardization", "medium")),
        automation_band=str(data.get("plus3_automation", "partial")),
        advisory_band=str(data.get("plus3_advisory", "10_20")),
    )

    k = precise_result["k"]
    released_6 = int(round(express_result["released_6"] * k))
    released_12 = int(round(express_result["released_12"] * k))
    payroll_saved_6 = express_result["payroll_saved_6"] * k
    payroll_saved_12 = express_result["payroll_saved_12"] * k
    ai_cost_6 = express_result["ai_cost_6"] * k
    ai_cost_12 = express_result["ai_cost_12"] * k
    net_6 = express_result["net_6"] * k
    net_12 = express_result["net_12"] * k

    precise_range = f"{format_rub(min(net_6, net_12))} – {format_rub(max(net_6, net_12))} ₽/мес"
    text = (
        "🎯 <b>Ваши результаты с Aivel:</b>\n\n"
        "Спасибо — на основе ваших ответов мы уточнили базовую оценку и рассчитали более точный потенциал "
        "экономии с учётом специфики именно вашей фирмы.\n"
        "Шаги расчёта через 6 месяцев и через 12 месяцев\n\n"
        "1. <b>Число высвобождаемых бухгалтеров</b>\n"
        f"• через 6 месяцев: <b>{released_6}</b>\n"
        f"• через 12 месяцев: <b>{released_12}</b>\n\n"
        "2. <b>Сохраняемая месячная зарплатная масса</b>\n"
        f"• через 6 месяцев: <b>{format_rub(payroll_saved_6)} ₽ в месяц</b>\n"
        f"• через 12 месяцев: <b>{format_rub(payroll_saved_12)} ₽ в месяц</b>\n\n"
        "3. <b>Новая стоимость операций на базе искусственного интеллекта</b>\n"
        f"• через 6 месяцев: <b>{format_rub(ai_cost_6)} ₽ в месяц</b>\n"
        f"• через 12 месяцев: <b>{format_rub(ai_cost_12)} ₽ в месяц</b>\n\n"
        "4. <b>Чистая экономия в месяц</b>\n"
        f"• через 6 месяцев: <b>{format_rub(net_6)} ₽ в месяц</b>\n"
        f"• через 12 месяцев: <b>{format_rub(net_12)} ₽ в месяц</b>\n\n"
        f"<i>Итоговый K: {k:.2f}</i>\n"
        f"<i>Диапазон точной экономии: {precise_range}</i>"
    )

    user_id = await get_db_user_id(target)
    await save_funnel_fields(
        user_id,
        precise_assessment=precise_range,
        express_saving_6=int(round(net_6)),
        express_saving_12=int(round(net_12)),
    )
    await add_event(
        user_id,
        "simulate_precise_completed",
        (
            f"accountants={data.get('precise_accountants', 0)};salary={data.get('precise_salary', 0)};"
            f"clients={data.get('precise_clients', 0)};contacts={data.get('precise_contacts', '')};"
            f"margin={data.get('precise_margin', 0)};std={data.get('plus3_standardization', 'medium')};"
            f"auto={data.get('plus3_automation', 'partial')};advisory={data.get('plus3_advisory', '10_20')};"
            f"k={k:.4f};range={precise_range};net6={format_rub(net_6)};net12={format_rub(net_12)}"
        ),
    )

    await state.set_state(SimulateFlow.precise_growth)
    if isinstance(target, CallbackQuery):
        await target.message.answer(text, parse_mode="HTML")
        await target.message.answer(
            "Планируете ли вы рост в ближайшие 12-24 месяца?",
            reply_markup=simulate_growth_keyboard(),
        )
    else:
        await target.answer(text, parse_mode="HTML")
        await target.answer(
            "Планируете ли вы рост в ближайшие 12-24 месяца?",
            reply_markup=simulate_growth_keyboard(),
        )


@router.callback_query(SimulateFlow.precise_growth, F.data.startswith("simulate:post:growth:"))
async def simulate_post_growth(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[-1]
    if value not in {"none", "normal", "fast"}:
        await callback.answer("Некорректный вариант", show_alert=True)
        return

    await state.update_data(post_growth=value)
    user_id = (await state.get_data()).get("db_user_id")
    if user_id:
        await save_funnel_fields(int(user_id), growth_band=value)
    await state.set_state(SimulateFlow.precise_mna)
    await callback.message.answer(
        "Рассматриваете ли вы M&A / привлечение инвестиций?",
        reply_markup=simulate_mna_keyboard(),
    )
    await callback.answer()


@router.callback_query(SimulateFlow.precise_mna, F.data.startswith("simulate:post:mna:"))
async def simulate_post_mna(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[-1]
    if value not in {"yes", "no"}:
        await callback.answer("Некорректный вариант", show_alert=True)
        return

    await state.update_data(post_mna=value)
    user_id = (await state.get_data()).get("db_user_id")
    if user_id:
        await save_funnel_fields(int(user_id), mna_interest=value)
    await state.set_state(SimulateFlow.precise_wait_excel)
    await callback.message.answer(
        "🎯 Серьёзно рассматриваете внедрение? Загрузите Excel — получите полный бизнес-кейс от нашей команды.",
        reply_markup=simulate_deep_assessment_keyboard(),
    )
    await callback.answer()


@router.callback_query(SimulateFlow.precise_wait_excel, F.data == "simulate:deep:download")
async def simulate_deep_download(callback: CallbackQuery, state: FSMContext):
    await send_excel_and_wait_for_user(callback, state)


@router.callback_query(SimulateFlow.precise_wait_excel, F.data == "simulate:deep:sent_email")
async def simulate_deep_sent_email(callback: CallbackQuery, state: FSMContext):
    user_id = await get_db_user_id(callback)
    await save_funnel_fields(user_id, uploaded_file_link="sent_to_success@aivel.ai")
    await add_event(user_id, "simulate_deep_sent_email")
    await return_to_base_state(callback.message, state, THANKS_DEEP_TEXT)
    await callback.answer()


@router.callback_query(SimulateFlow.precise_wait_excel, F.data == "simulate:deep:back")
async def simulate_deep_back(callback: CallbackQuery, state: FSMContext):
    await return_to_base_state(callback.message, state, THANKS_TOOL_TEXT)
    await callback.answer()


@router.callback_query(SimulateFlow.precise_wait_excel, F.data == "simulate:deep:back_wait")
async def simulate_deep_back_wait(callback: CallbackQuery, state: FSMContext):
    await return_to_base_state(callback.message, state, THANKS_TOOL_TEXT)
    await callback.answer()


@router.message(SimulateFlow.precise_wait_excel, F.document)
async def simulate_wait_excel_upload(message: Message, state: FSMContext):
    document = message.document
    if not is_excel_filename(document.file_name):
        await message.answer("Похоже, это не Excel-файл. Пожалуйста, отправьте файл в формате .xlsx/.xls/.xlsm.")
        return

    user_id = await get_db_user_id(message)
    await save_funnel_fields(
        user_id,
        file_downloaded=True,
        uploaded_file_link=f"telegram_file_id:{document.file_id}",
    )
    await add_event(user_id, "simulate_deep_excel_uploaded", document.file_name)
    await return_to_base_state(message, state, THANKS_DEEP_TEXT)


@router.message(SimulateFlow.precise_wait_excel)
async def simulate_wait_excel_invalid(message: Message):
    await message.answer(
        "Пожалуйста, отправьте Excel-файл (.xlsx/.xls/.xlsm) или используйте кнопки ниже.",
        reply_markup=simulate_deep_wait_keyboard(),
    )
