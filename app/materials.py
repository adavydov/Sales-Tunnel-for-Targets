from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MATERIALS_DIR = BASE_DIR / "materials"

COMPARE_FILES = [
    {
        "local_name": "full_sale_track.txt",
        "display_name": "Подробнее про трек полной продажи.txt",
        "content": "текст про Подробнее про трек полной продажи",
    },
    {
        "local_name": "cooperation_track.txt",
        "display_name": "Подробнее про трек сотрудничества.txt",
        "content": "текст про Подробнее про трек сотрудничества",
    },
    {
        "local_name": "how_to_choose.txt",
        "display_name": "Как выбрать из этих вариантов.txt",
        "content": "текст про Как выбрать из этих вариантов",
    },
]


def ensure_material_files():
    MATERIALS_DIR.mkdir(parents=True, exist_ok=True)

    for item in COMPARE_FILES:
        file_path = MATERIALS_DIR / item["local_name"]
        if not file_path.exists():
            file_path.write_text(item["content"], encoding="utf-8")