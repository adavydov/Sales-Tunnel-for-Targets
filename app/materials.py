from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MATERIALS_DIR = BASE_DIR / "materials"

MATERIAL_FILES = [
    "material_1.txt",
    "material_2.txt",
    "material_3.txt",
    "material_4.txt",
    "material_5.txt",
]

def ensure_material_files():
    MATERIALS_DIR.mkdir(parents=True, exist_ok=True)
    for f in MATERIAL_FILES:
        file_path = MATERIALS_DIR / f
        if not file_path.exists():
            file_path.write_text(f"Текст про {f}", encoding="utf-8")