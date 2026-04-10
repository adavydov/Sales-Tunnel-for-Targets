from decimal import ROUND_HALF_UP, Decimal

ROLE_POINTS = {
    "owner": 25,
    "partner": 22,
    "ceo": 18,
    "ops": 10,
}

SIZE_POINTS = {
    "large": 25,
    "medium": 15,
    "small": 5,
}

TIMEFRAME_POINTS = {
    "now": 25,
    "3_6": 18,
    "6_12": 10,
    "later": 3,
}


def calculate_scores(track: str, role: str, business_size: str, timeframe: str, motivation: str):
    fit_score = (
        ROLE_POINTS.get(role, 0)
        + SIZE_POINTS.get(business_size, 0)
        + 20
        + (15 if motivation else 0)
    )

    intent_score = (
        TIMEFRAME_POINTS.get(timeframe, 0)
        + 20
        + (10 if motivation else 0)
    )

    fit_score = min(fit_score, 100)
    intent_score = min(intent_score, 100)

    if fit_score < 45:
        status = "not_fit"
    elif fit_score >= 60 and intent_score >= 55:
        status = "ready_t1" if track == "t1" else "ready_t2"
    else:
        status = "nurture"

    return fit_score, intent_score, status


def build_result_screen(track: str, status: str) -> str:
    texts = {
        "t1": {
            "ready_t1": (
                "Похоже, вам подходит сценарий полной продажи бизнеса.\n\n"
                "По вашим ответам уже есть основания переходить к предметному разговору "
                "и разбору ситуации."
            ),
            "nurture": (
                "Сценарий полной продажи бизнеса может быть вам релевантен, "
                "но по текущим ответам, вероятно, вам нужен ещё один шаг подготовки "
                "перед предметным обсуждением."
            ),
            "not_fit": (
                "По текущим ответам сценарий полной продажи бизнеса сейчас выглядит "
                "не самым очевидным. Но можно обсудить ситуацию точечно и понять, "
                "есть ли рабочий формат."
            ),
        },
        "t2": {
            "ready_t2": (
                "Похоже, вам подходит сценарий продажи части бизнеса / сотрудничества.\n\n"
                "По вашим ответам можно переходить к более предметному обсуждению модели."
            ),
            "nurture": (
                "Сценарий сотрудничества вам потенциально подходит, "
                "но по текущим ответам похоже, что решение еще требует доработки "
                "или дополнительного понимания."
            ),
            "not_fit": (
                "По текущим ответам сценарий сотрудничества сейчас выглядит "
                "не самым очевидным. Но можно обсудить ситуацию отдельно и понять, "
                "есть ли подходящий формат."
            ),
        }
    }

    common_cta = "\n\nЕсли хотите, оставьте свои контакты, и мы свяжемся с вами."
    return texts[track][status] + common_cta


def calculate_express_savings(revenue_rub: int, accountants_count: int, monthly_salary_rub: int) -> dict[str, int]:
    annual_payroll = accountants_count * monthly_salary_rub * 12

    min_savings = min(int(annual_payroll * 0.30), int(revenue_rub * 0.12))
    max_savings = min(int(annual_payroll * 0.90), int(revenue_rub * 0.24))

    if max_savings < min_savings:
        max_savings = min_savings

    return {
        "min_savings_rub": min_savings,
        "max_savings_rub": max_savings,
        "min_margin_growth_pct": 10,
        "max_margin_growth_pct": 20,
    }


def calculate_express_operation_savings(accountants_count: int, monthly_salary_rub: int) -> dict[str, int]:
    released_6 = int((Decimal(accountants_count) * Decimal("0.35")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    released_12 = int((Decimal(accountants_count) * Decimal("0.65")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

    payroll_saved_6 = int(released_6 * monthly_salary_rub)
    payroll_saved_12 = int(released_12 * monthly_salary_rub)

    ai_cost_6 = int((Decimal(payroll_saved_6) * Decimal("0.2")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    ai_cost_12 = int((Decimal(payroll_saved_12) * Decimal("0.2")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

    net_6 = int(payroll_saved_6 - ai_cost_6)
    net_12 = int(payroll_saved_12 - ai_cost_12)

    return {
        "released_6": released_6,         # всегда целое
        "released_12": released_12,       # всегда целое
        "payroll_saved_6": payroll_saved_6,
        "payroll_saved_12": payroll_saved_12,
        "ai_cost_6": ai_cost_6,
        "ai_cost_12": ai_cost_12,
        "net_6": net_6,
        "net_12": net_12,
    }

def calculate_precise_savings_from_express(
    express_result: dict[str, int],
    standardization_band: str,
    automation_band: str,
    advisory_band: str,
) -> dict[str, float]:
    advisory_multiplier = {
        "lt10": 1.00,
        "10_20": 0.95,
        "gt20": 0.85,
    }.get(advisory_band, 1.00)

    automation_multiplier = {
        "none": 1.00,
        "partial": 0.85,
        "systems": 0.65,
    }.get(automation_band, 1.00)

    standardization_multiplier = {
        "high": 1.00,
        "medium": 1.10,
        "low": 1.35,
    }.get(standardization_band, 1.00)

    weighted_k = (
        advisory_multiplier * 0.30
        + standardization_multiplier * 0.35
        + automation_multiplier * 0.35
    )

    express_min = min(express_result["net_6"], express_result["net_12"])
    express_max = max(express_result["net_6"], express_result["net_12"])
    precise_min = express_min * weighted_k
    precise_max = express_max * weighted_k

    return {
        "k": weighted_k,
        "k_advisory": advisory_multiplier,
        "k_standardization": standardization_multiplier,
        "k_automation": automation_multiplier,
        "precise_min_rub": precise_min,
        "precise_max_rub": precise_max,
    }


def refine_precise_savings_with_plus3(
    base_result: dict[str, int],
    standardization_band: str,
    automation_band: str,
    advisory_band: str,
) -> dict[str, float]:
    advisory_multiplier = {
        "lt10": 1.00,
        "10_20": 0.95,
        "gt20": 0.85,
    }.get(advisory_band, 1.00)
    automation_multiplier = {
        "none": 1.00,
        "partial": 0.85,
        "systems": 0.65,
    }.get(automation_band, 1.00)
    standardization_multiplier = {
        "high": 1.00,
        "medium": 1.10,
        "low": 1.35,
    }.get(standardization_band, 1.00)

    weighted_k = (
        advisory_multiplier * 0.30
        + standardization_multiplier * 0.35
        + automation_multiplier * 0.35
    )

    express_min = min(express_result["net_6"], express_result["net_12"])
    express_max = max(express_result["net_6"], express_result["net_12"])
    precise_min = express_min * weighted_k
    precise_max = express_max * weighted_k

    return {
        "k": weighted_k,
        "k_advisory": advisory_multiplier,
        "k_standardization": standardization_multiplier,
        "k_automation": automation_multiplier,
        "precise_min_rub": precise_min,
        "precise_max_rub": precise_max,
    }
