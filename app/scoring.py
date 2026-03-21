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


def build_result_text(track: str, fit_score: int, intent_score: int, status: str) -> str:
    status_map = {
        "ready_t1": "Ready T1",
        "ready_t2": "Ready T2",
        "nurture": "Nurture",
        "not_fit": "Not fit",
    }

    track_map = {
        "t1": "Продажа 100% бизнеса",
        "t2": "Продажа части бизнеса / сотрудничество",
    }

    return (
        f"Ваш трек: {track_map.get(track, track)}\n\n"
        f"fit_score: {fit_score}\n"
        f"intent_score: {intent_score}\n"
        f"Статус: {status_map.get(status, status)}"
    )