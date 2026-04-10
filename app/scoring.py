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


def calculate_precise_savings(
    revenue_rub: int,
    accountants_count: int,
    monthly_salary_rub: int,
    clients_count: int,
    gross_margin_pct: int,
    ops_share_band: str,
    complex_cases_band: str,
) -> dict[str, int]:
    annual_payroll = accountants_count * monthly_salary_rub * 12

    ops_multiplier = {
        "40_50": 0.90,
        "50_70": 1.00,
        "70_plus": 1.15,
    }.get(ops_share_band, 1.00)

    complexity_multiplier = {
        "many": 0.85,
        "some": 1.00,
        "few": 1.08,
    }.get(complex_cases_band, 1.00)

    scale_multiplier = min(max(clients_count / 100, 0.85), 1.25)
    margin_multiplier = 1.05 if gross_margin_pct < 30 else 0.95

    combined = ops_multiplier * complexity_multiplier * scale_multiplier * margin_multiplier
    base_min = int(min(annual_payroll * 0.40 * combined, revenue_rub * 0.16))
    base_max = int(min(annual_payroll * 0.85 * combined, revenue_rub * 0.30))

    if base_max < base_min:
        base_max = base_min

    phase2_min = int(base_min * 1.7)
    phase2_max = int(base_max * 1.9)
    future_min = int(phase2_min * 1.45)
    future_max = int(phase2_max * 1.35)

    if future_max < future_min:
        future_max = future_min

    return {
        "phase1_min_rub": base_min,
        "phase1_max_rub": base_max,
        "phase2_min_rub": phase2_min,
        "phase2_max_rub": phase2_max,
        "future_min_rub": future_min,
        "future_max_rub": future_max,
    }


def refine_precise_savings_with_plus3(
    base_result: dict[str, int],
    standardization_band: str,
    automation_band: str,
    advisory_band: str,
) -> dict[str, int]:
    standardization_multiplier = {
        "high": 1.12,
        "medium": 1.00,
        "low": 0.90,
    }.get(standardization_band, 1.00)
    automation_multiplier = {
        "none": 0.90,
        "partial": 1.00,
        "crm": 1.08,
        "rpa": 1.15,
    }.get(automation_band, 1.00)
    advisory_multiplier = {
        "lt5": 1.08,
        "5_15": 1.00,
        "15_25": 0.94,
        "gt25": 0.88,
    }.get(advisory_band, 1.00)

    combined = standardization_multiplier * automation_multiplier * advisory_multiplier

    phase1_min = int(base_result["phase1_min_rub"] * combined * 1.02)
    phase1_max = int(base_result["phase1_max_rub"] * combined * 0.90)
    if phase1_max < phase1_min:
        phase1_max = phase1_min

    phase2_min = int(phase1_min * 1.6)
    phase2_max = int(phase1_max * 1.75)
    if phase2_max < phase2_min:
        phase2_max = phase2_min

    future_min = int(phase2_min * 1.45)
    future_max = int(phase2_max * 1.3)
    if future_max < future_min:
        future_max = future_min

    return {
        "phase1_min_rub": phase1_min,
        "phase1_max_rub": phase1_max,
        "phase2_min_rub": phase2_min,
        "phase2_max_rub": phase2_max,
        "future_min_rub": future_min,
        "future_max_rub": future_max,
    }
