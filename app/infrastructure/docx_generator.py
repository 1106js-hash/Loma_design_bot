from docxtpl import DocxTemplate
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent  # это папка app
RESOURCES_DIR = BASE_DIR / "resources"

TEMPLATE_PATH = RESOURCES_DIR / "templates" / "kp_template.docx"
OUTPUT_DIR = RESOURCES_DIR / "output"


def generate_docx(data: dict, user_id: int) -> str:
    doc = DocxTemplate(TEMPLATE_PATH)

    context = {
        "name": data.get("name", ""),
        "phone": data.get("phone", ""),
        "email": data.get("email", "")
    }

    doc.render(context)

    OUTPUT_DIR.mkdir(exist_ok=True)
    file_path = OUTPUT_DIR / f"form_{user_id}.docx"
    doc.save(file_path)

    return str(file_path)
