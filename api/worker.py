
from api.ocr import ResidencePermitProcessor

from celery import Celery

app = Celery(
    "ocr_tasks",
    broker="redis://redis/0",
    backend="redis://redis/0",
)

@app.task
def process_ocr(image_bytes: bytes):
    """OCR + translation task."""

    text = ResidencePermitProcessor().process_document(image_bytes, "output.txt")

    return {"text": text['translated_text']}

