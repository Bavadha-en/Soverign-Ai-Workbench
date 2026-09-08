from typing import Any, Dict, Union
from backend.documents.pdf_processor import pdf_processor


def process_pdf_document(source: Union[str, bytes]) -> Dict[str, Any]:
    """Extract metadata, pages, and text from a PDF file."""
    return pdf_processor.process_pdf(source)


def extract_pdf_text(source: Union[str, bytes]) -> str:
    """Extract concatenated text from all PDF pages."""
    return pdf_processor.extract_full_text(source)
