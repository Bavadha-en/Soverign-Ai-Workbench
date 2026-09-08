from typing import Union
from backend.documents.ocr import ocr_engine


def extract_ocr_text(source: Union[str, bytes]) -> str:
    """Extract text from scanned document pages or images using local OCR."""
    return ocr_engine.perform_ocr(source)
