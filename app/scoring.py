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