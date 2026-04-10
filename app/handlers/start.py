import logging
import re
from pathlib import Path

from aiogram import F, Router
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message, ReplyKeyboardRemove

from app.db import add_event, get_tool_consent, save_profile_field, upsert_user
from app.keyboards import (
    menu_keyboard,
    persistent_main_keyboard,
    simulate_deep_assessment_keyboard,
    simulate_mode_keyboard,
    simulate_plus3_advisory_keyboard,
    simulate_plus3_automation_keyboard,
    simulate_plus3_standardization_keyboard,
    simulate_precise_complex_keyboard,
    simulate_precise_ops_keyboard,
    simulate_precise_results_keyboard,
    simulate_results_keyboard,
    tool_consent_keyboard,
    website_optional_keyboard,
)
from app.scoring import (
    calculate_express_savings,
    calculate_precise_savings,
    refine_precise_savings_with_plus3,
)
from app.states import OnboardingFlow, SimulateFlow, ToolConsentFlow

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
BOOK_MEETING_TEXT = (
    "Для организации созвона напишите нам:\n\n"
    "• Email: hello@aivel.ru\n"
    "• Telegram: @aivel_ai\n"
    "• Website: https://aivel.ru"
)
SIMULATE_MODE_TEXT = (
    "💰 <b>Калькулятор экономии с Aivel</b>\n\n"
    "Выберите уровень детализации расчёта:\n\n"
    "⚡ <b>Экспресс-оценка (1 минута)</b>\n"
    "3 вопроса → мгновенный результат\n"
    "Для первого знакомства и быстрой оценки порядка цифр\n\n"
    "✅ <b>Точная оценка (5–7 минут)</b>\n"
    "7 вопросов → персонализированный расчёт с диапазонами\n\n"
    "📊 <b>Профессиональная оценка (60–90 минут)</b>\n"
    "Excel-опросник: ~45 полей данных → максимальная точность\n"
    "Полный финансовый анализ с моделированием ROI, NPV, и планом внедрения"
)
SIMULATE_PRO_TEXT = (
    "🎯 Серьёзно рассматриваете внедрение? Загрузите Excel — получите полный бизнес-кейс от нашей команды.\n\n"
    "📥 Скачать Excel-файл\n"
    "📤 Заполнили? Загрузить обратно или отправьте это на: success@aivel.ai\n"
    "После загрузки мы подготовим детальный бизнес-кейс и свяжемся с вами в течение 2 рабочих дней."
)
SIMULATE_PRO_MISSING_TEXT = (
    "Не удалось найти Excel-файл в проекте.\n"
    "Пожалуйста, добавьте .xlsx в репозиторий (например, в app/assets/) и попробуйте снова."
)
OPS_SHARE_LABELS = {
    "40_50": "40-50%",
    "50_70": "50-70%",
    "70_plus": "70%+",
}
COMPLEX_CASES_LABELS = {
    "many": "Да, много (>30%)",
    "some": "Некоторые (10–30%)",
    "few": "Мало (<10%)",
}
STANDARDIZATION_LABELS = {
    "high": "Высокая",
    "medium": "Средняя",
    "low": "Низкая",
}
AUTOMATION_LABELS = {
    "none": "Нет, всё вручную",
    "partial": "Частично",
    "crm": "Есть CRM/системы",
    "rpa": "Продвинутая (RPA/боты)",
}
ADVISORY_LABELS = {
    "lt5": "Менее 5%",
    "5_15": "5-15%",
    "15_25": "15-25%",
    "gt25": "Более 25%",
}
WAIT_FILE_TEXT = (
    "Ожидаем ваш файл.\n\n"
    "Вы можете загрузить Excel сюда или нажать «Отправил по почте», если уже отправили на success@aivel.ai."
)
THANKS_DEEP_TEXT = "Спасибо! С вами свяжутся в течение 2 рабочих дней."


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
        "Прикрепите www-ссылку на сайт компании.",
        reply_markup=website_optional_keyboard(),
    )


@router.message(OnboardingFlow.company)
async def onboarding_company_invalid(message: Message):
    await message.answer("Пожалуйста, введите название компании текстом.")


@router.message(OnboardingFlow.website, F.text)
async def onboarding_website(message: Message, state: FSMContext):
    website_raw = message.text.strip()
    website_value = website_raw

    if not URL_RE.match(website_raw):
        await message.answer("Ссылка выглядит некорректно. Пример: www.company.com или https://company.com")
        return

    data = await state.get_data()
    user_id = data["db_user_id"]

    await save_profile_field(user_id, "company_website", website_value)
    await add_event(user_id, "onboarding_website_saved", website_value)

    await state.clear()
    await send_onboarding_complete(message)


@router.message(OnboardingFlow.website)
async def onboarding_website_invalid(message: Message):
    await message.answer("Пожалуйста, отправьте ссылку текстом или нажмите кнопку «Нет сайта».")


@router.callback_query(OnboardingFlow.website, F.data == "onboarding:no_site")
async def onboarding_no_site(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = data["db_user_id"]

    await save_profile_field(user_id, "company_website", "")
    await add_event(user_id, "onboarding_website_saved", "")

    await state.clear()
    await callback.message.delete()
    await send_onboarding_complete(callback.message)
    await callback.answer()


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
async def book_meeting(callback: CallbackQuery):
    await callback.message.answer(BOOK_MEETING_TEXT, disable_web_page_preview=True)
    await callback.answer()


@router.callback_query(F.data.startswith("stub:"))
async def menu_stub(callback: CallbackQuery):
    await callback.answer("Раздел в разработке. Скоро добавим функционал.", show_alert=True)


@router.callback_query(SimulateFlow.mode_select, F.data == "simulate:mode:menu")
async def simulate_mode_menu(callback: CallbackQuery, state: FSMContext):
    await send_simulate_mode_menu(callback, state)


@router.callback_query(SimulateFlow.mode_select, F.data == "simulate:mode:express")
async def simulate_mode_express(callback: CallbackQuery, state: FSMContext):
    user_id = await get_db_user_id(callback)
    await add_event(user_id, "simulate_mode_selected", "express")

    await state.set_state(SimulateFlow.express_revenue)
    await callback.message.answer(
        "⚡ <b>Экспресс-оценка</b>\n\nОтветьте на 3 простых вопроса.\n\n"
        "1️⃣ Ваша годовая выручка (₽)?\n<i>Например: 50000000</i>",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove(),
    )
    await callback.answer()


@router.callback_query(SimulateFlow.mode_select, F.data == "simulate:mode:precise")
async def simulate_mode_precise(callback: CallbackQuery, state: FSMContext):
    user_id = await get_db_user_id(callback)
    await add_event(user_id, "simulate_mode_selected", "precise")

    await state.set_state(SimulateFlow.precise_revenue)
    await callback.message.answer(
        "✅ <b>Точная оценка</b>\n\n"
        "Ответьте на 7 вопросов.\n\n"
        "1️⃣ Годовая выручка (₽)?\n<i>Например: 50000000</i>",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove(),
    )
    await callback.answer()


@router.callback_query(SimulateFlow.mode_select, F.data == "simulate:mode:pro")
async def simulate_mode_pro(callback: CallbackQuery):
    user_id = await get_db_user_id(callback)
    await add_event(user_id, "simulate_mode_selected", "pro")

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
    await add_event(user_id, "simulate_pro_excel_sent", excel_path.name)
    await callback.answer()


@router.message(SimulateFlow.express_revenue, F.text)
async def simulate_express_revenue(message: Message, state: FSMContext):
    revenue = parse_positive_int(message.text.strip())
    if revenue is None:
        await message.answer("Введите годовую выручку числом в ₽. Пример: 50000000")
        return

    await state.update_data(express_revenue=revenue)
    await state.set_state(SimulateFlow.express_accountants)
    await message.answer(
        "2️⃣ Сколько у вас бухгалтеров (чел.)?\n<i>Например: 15</i>",
        parse_mode="HTML",
    )


@router.message(SimulateFlow.express_accountants, F.text)
async def simulate_express_accountants(message: Message, state: FSMContext):
    accountants = parse_positive_int(message.text.strip())
    if accountants is None:
        await message.answer("Введите количество бухгалтеров целым числом. Пример: 15")
        return

    await state.update_data(express_accountants=accountants)
    await state.set_state(SimulateFlow.express_salary)
    await message.answer(
        "3️⃣ Средняя зарплата бухгалтера (₽/мес)?\n<i>Например: 80000</i>",
        parse_mode="HTML",
    )


@router.message(SimulateFlow.express_salary, F.text)
async def simulate_express_salary(message: Message, state: FSMContext):
    salary = parse_positive_int(message.text.strip())
    if salary is None:
        await message.answer("Введите среднюю зарплату бухгалтера числом в ₽. Пример: 80000")
        return

    data = await state.get_data()
    revenue = int(data["express_revenue"])
    accountants = int(data["express_accountants"])
    result = calculate_express_savings(revenue, accountants, salary)

    savings_range = format_mln_range(result["min_savings_rub"], result["max_savings_rub"])
    result_text = (
        "🎯 <b>Ваши результаты с Aivel:</b>\n"
        f"Ориентировочная экономия: <b>{savings_range}</b>\n"
        f"Рост маржи: <b>+{result['min_margin_growth_pct']}-{result['max_margin_growth_pct']}%</b>\n\n"
        "⚠️ Это грубая оценка. Для точного расчёта пройдите детальную оценку."
    )

    user_id = await get_db_user_id(message)
    await add_event(
        user_id,
        "simulate_express_completed",
        f"revenue={revenue};accountants={accountants};salary={salary};range={savings_range}",
    )

    await state.set_state(SimulateFlow.mode_select)
    await message.answer(result_text, parse_mode="HTML", reply_markup=simulate_results_keyboard())


@router.message(SimulateFlow.precise_revenue, F.text)
async def simulate_precise_revenue(message: Message, state: FSMContext):
    revenue = parse_positive_int(message.text.strip())
    if revenue is None:
        await message.answer("Введите годовую выручку числом в ₽. Пример: 50000000")
        return

    await state.update_data(precise_revenue=revenue)
    await state.set_state(SimulateFlow.precise_accountants)
    await message.answer("2️⃣ Количество бухгалтеров (чел.)?\n<i>Например: 15</i>", parse_mode="HTML")


@router.message(SimulateFlow.precise_accountants, F.text)
async def simulate_precise_accountants(message: Message, state: FSMContext):
    accountants = parse_positive_int(message.text.strip())
    if accountants is None:
        await message.answer("Введите количество бухгалтеров целым числом. Пример: 15")
        return

    await state.update_data(precise_accountants=accountants)
    await state.set_state(SimulateFlow.precise_salary)
    await message.answer("3️⃣ Средняя зарплата бухгалтера (₽/мес)?\n<i>Например: 80000</i>", parse_mode="HTML")


@router.message(SimulateFlow.precise_salary, F.text)
async def simulate_precise_salary(message: Message, state: FSMContext):
    salary = parse_positive_int(message.text.strip())
    if salary is None:
        await message.answer("Введите среднюю зарплату бухгалтера числом в ₽. Пример: 80000")
        return

    await state.update_data(precise_salary=salary)
    await state.set_state(SimulateFlow.precise_clients)
    await message.answer("4️⃣ Количество активных клиентов?\n<i>Например: 120</i>", parse_mode="HTML")


@router.message(SimulateFlow.precise_clients, F.text)
async def simulate_precise_clients(message: Message, state: FSMContext):
    clients = parse_positive_int(message.text.strip())
    if clients is None:
        await message.answer("Введите количество активных клиентов целым числом. Пример: 120")
        return

    await state.update_data(precise_clients=clients)
    await state.set_state(SimulateFlow.precise_margin)
    await message.answer("5️⃣ Текущая валовая маржа (%)?\n<i>Например: 35</i>", parse_mode="HTML")


@router.message(SimulateFlow.precise_margin, F.text)
async def simulate_precise_margin(message: Message, state: FSMContext):
    margin = parse_positive_int(message.text.strip())
    if margin is None or margin > 100:
        await message.answer("Введите валовую маржу числом от 1 до 100. Пример: 35")
        return

    await state.update_data(precise_margin=margin)
    await state.set_state(SimulateFlow.precise_ops_share)
    await message.answer(
        "6️⃣ Какой % работы занимают операции:\n"
        "• Обработка входящих запросов и документов\n"
        "• Первичные документы\n"
        "• Акты сверки\n"
        "• Работа с банк-клиентом\n\n"
        "Выберите вариант:",
        reply_markup=simulate_precise_ops_keyboard(),
    )


@router.callback_query(SimulateFlow.precise_ops_share, F.data.startswith("simulate:precise:ops:"))
async def simulate_precise_ops_share(callback: CallbackQuery, state: FSMContext):
    ops_share = callback.data.split(":")[-1]
    if ops_share not in OPS_SHARE_LABELS:
        await callback.answer("Некорректный вариант", show_alert=True)
        return

    await state.update_data(precise_ops_share=ops_share)
    await state.set_state(SimulateFlow.precise_complex_cases)
    await callback.message.answer(
        "7️⃣ Есть ли у вас клиенты со сложными кейсами?\n"
        "<i>Это снижает процент автоматизации для сложных задач.</i>\n\n"
        "Выберите вариант:",
        parse_mode="HTML",
        reply_markup=simulate_precise_complex_keyboard(),
    )
    await callback.answer()


@router.callback_query(SimulateFlow.precise_complex_cases, F.data.startswith("simulate:precise:complex:"))
async def simulate_precise_complex_cases(callback: CallbackQuery, state: FSMContext):
    complex_cases = callback.data.split(":")[-1]
    if complex_cases not in COMPLEX_CASES_LABELS:
        await callback.answer("Некорректный вариант", show_alert=True)
        return

    await state.update_data(precise_complex_cases=complex_cases)
    data = await state.get_data()
    result = calculate_precise_savings(
        revenue_rub=int(data["precise_revenue"]),
        accountants_count=int(data["precise_accountants"]),
        monthly_salary_rub=int(data["precise_salary"]),
        clients_count=int(data["precise_clients"]),
        gross_margin_pct=int(data["precise_margin"]),
        ops_share_band=str(data["precise_ops_share"]),
        complex_cases_band=complex_cases,
    )

    phase1 = format_mln_range(result["phase1_min_rub"], result["phase1_max_rub"]).replace("/год", "")
    phase2 = format_mln_range(result["phase2_min_rub"], result["phase2_max_rub"]).replace("/год", "")
    future = format_mln_range(result["future_min_rub"], result["future_max_rub"]).replace("/год", "")

    result_text = (
        "🎯 <b>Ваши результаты с Aivel:</b>\n"
        f"Фаза 1 (6 мес): <b>{phase1} экономии</b>\n"
        f"Фаза 2 (18 мес): <b>{phase2} экономии</b>\n"
        f"Будущий потенциал: <b>{future}</b>\n\n"
        "Это быстрая прикидка экономики на основе ваших процессов."
    )

    user_id = await get_db_user_id(callback)
    await add_event(
        user_id,
        "simulate_precise_completed",
        (
            f"revenue={data['precise_revenue']};accountants={data['precise_accountants']};"
            f"salary={data['precise_salary']};clients={data['precise_clients']};"
            f"margin={data['precise_margin']};ops={data['precise_ops_share']};complex={complex_cases}"
        ),
    )

    await state.set_state(SimulateFlow.mode_select)
    await callback.message.answer(result_text, parse_mode="HTML", reply_markup=simulate_precise_results_keyboard())
    await callback.answer()


@router.callback_query(SimulateFlow.mode_select, F.data == "simulate:precise:more")
async def simulate_precise_more(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SimulateFlow.precise_standardization)
    await callback.message.answer(
        "8️⃣ Насколько стандартизированы ваши процессы?\n"
        "<i>При высокой стандартизации вы достигнете результатов на 30% быстрее.</i>\n\n"
        "Выберите вариант:",
        parse_mode="HTML",
        reply_markup=simulate_plus3_standardization_keyboard(),
    )
    await callback.answer()


@router.callback_query(SimulateFlow.precise_standardization, F.data.startswith("simulate:plus3:std:"))
async def simulate_plus3_standardization(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[-1]
    if value not in STANDARDIZATION_LABELS:
        await callback.answer("Некорректный вариант", show_alert=True)
        return

    await state.update_data(plus3_standardization=value)
    await state.set_state(SimulateFlow.precise_automation)
    await callback.message.answer(
        "9️⃣ Используете ли вы сейчас какие-то инструменты автоматизации?\n"
        "<i>У вас уже есть CRM — интеграция займёт 3 месяца вместо 5.</i>\n\n"
        "Выберите вариант:",
        parse_mode="HTML",
        reply_markup=simulate_plus3_automation_keyboard(),
    )
    await callback.answer()


@router.callback_query(SimulateFlow.precise_automation, F.data.startswith("simulate:plus3:auto:"))
async def simulate_plus3_automation(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[-1]
    if value not in AUTOMATION_LABELS:
        await callback.answer("Некорректный вариант", show_alert=True)
        return

    await state.update_data(plus3_automation=value)
    await state.set_state(SimulateFlow.precise_advisory)
    await callback.message.answer(
        "🔟 Какой % клиентов требует нестандартных консультаций / advisory работы?\n"
        "Выберите вариант:",
        reply_markup=simulate_plus3_advisory_keyboard(),
    )
    await callback.answer()


@router.callback_query(SimulateFlow.precise_advisory, F.data.startswith("simulate:plus3:advisory:"))
async def simulate_plus3_advisory(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[-1]
    if value not in ADVISORY_LABELS:
        await callback.answer("Некорректный вариант", show_alert=True)
        return

    data = await state.get_data()
    base_result = calculate_precise_savings(
        revenue_rub=int(data["precise_revenue"]),
        accountants_count=int(data["precise_accountants"]),
        monthly_salary_rub=int(data["precise_salary"]),
        clients_count=int(data["precise_clients"]),
        gross_margin_pct=int(data["precise_margin"]),
        ops_share_band=str(data["precise_ops_share"]),
        complex_cases_band=str(data["precise_complex_cases"]) if "precise_complex_cases" in data else "some",
    )
    refined = refine_precise_savings_with_plus3(
        base_result,
        standardization_band=str(data["plus3_standardization"]),
        automation_band=str(data["plus3_automation"]),
        advisory_band=value,
    )

    phase1 = format_mln_range(refined["phase1_min_rub"], refined["phase1_max_rub"]).replace("/год", "")
    phase2 = format_mln_range(refined["phase2_min_rub"], refined["phase2_max_rub"]).replace("/год", "")
    future = format_mln_range(refined["future_min_rub"], refined["future_max_rub"]).replace("/год", "")

    await state.update_data(plus3_advisory=value)
    await state.set_state(SimulateFlow.precise_wait_excel)

    await callback.message.answer(
        "🎯 <b>Ваши результаты с Aivel:</b>\n"
        f"Фаза 1 (6 мес): <b>{phase1} экономии</b>\n"
        f"Фаза 2 (18 мес): <b>{phase2} экономии</b>\n"
        f"Будущий потенциал: <b>{future}</b>\n\n"
        "🎯 Серьёзно рассматриваете внедрение? Загрузите Excel — получите полный бизнес-кейс от нашей команды.",
        parse_mode="HTML",
        reply_markup=simulate_deep_assessment_keyboard(),
    )
    await callback.answer()


@router.callback_query(SimulateFlow.precise_wait_excel, F.data == "simulate:deep:download")
async def simulate_deep_download(callback: CallbackQuery):
    excel_path = find_excel_template()
    if excel_path is None:
        await callback.message.answer(SIMULATE_PRO_MISSING_TEXT)
        await callback.answer("Excel-файл пока не найден", show_alert=True)
        return

    await callback.message.answer_document(
        document=FSInputFile(excel_path),
        caption="📥 Excel-опросник для профессиональной оценки",
    )
    await callback.message.answer(WAIT_FILE_TEXT, reply_markup=simulate_deep_assessment_keyboard())
    await callback.answer()


@router.callback_query(SimulateFlow.precise_wait_excel, F.data == "simulate:deep:sent_email")
async def simulate_deep_sent_email(callback: CallbackQuery, state: FSMContext):
    user_id = await get_db_user_id(callback)
    await add_event(user_id, "simulate_deep_sent_email")
    await state.set_state(SimulateFlow.mode_select)
    await callback.message.answer(THANKS_DEEP_TEXT)
    await callback.answer()


@router.callback_query(SimulateFlow.precise_wait_excel, F.data == "simulate:deep:back")
async def simulate_deep_back(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SimulateFlow.mode_select)
    await callback.message.answer("Ну хорошо, ждём вас позже.")
    await callback.answer()


@router.message(SimulateFlow.precise_wait_excel, F.document)
async def simulate_wait_excel_upload(message: Message, state: FSMContext):
    document = message.document
    if not is_excel_filename(document.file_name):
        await message.answer("Похоже, это не Excel-файл. Пожалуйста, отправьте файл в формате .xlsx/.xls/.xlsm.")
        return

    user_id = await get_db_user_id(message)
    await add_event(user_id, "simulate_deep_excel_uploaded", document.file_name)
    await state.set_state(SimulateFlow.mode_select)
    await message.answer(THANKS_DEEP_TEXT)


@router.message(SimulateFlow.precise_wait_excel)
async def simulate_wait_excel_invalid(message: Message):
    await message.answer(
        "Пожалуйста, отправьте Excel-файл (.xlsx/.xls/.xlsm) или используйте кнопки ниже.",
        reply_markup=simulate_deep_assessment_keyboard(),
    )
