"""
Turn an uploaded report (PDF, image or text file) into text, and record how
the text was obtained.

A scanned PDF has no text layer, so its page images are read with OCR. Before
this, a scanned report reached the rest of the pipeline as an empty string and
the approval note was written from nothing.
"""
import os
from typing import Any, Dict, List

from backend.documents.image_processor import image_processor
from backend.documents.ocr import ocr_engine
from backend.documents.pdf_processor import pdf_processor


def _ocr_page(image_path: str, page: int) -> List[Dict[str, Any]]:
    lines = ocr_engine.perform_ocr_document(image_path)
    for line in lines:
        line["page"] = page
    return lines


def _from_lines(lines: List[Dict[str, Any]], pages: int) -> Dict[str, Any]:
    pages_data = []
    for page in range(1, pages + 1):
        page_text = "\n".join(l["text"] for l in lines if l["page"] == page)
        pages_data.append({"page": page, "text": page_text, "char_count": len(page_text)})
    return {
        "text": "\n".join(l["text"] for l in lines),
        "text_source": "ocr" if lines else "none",
        "pages_data": pages_data,
    }


def read_document(path: str) -> Dict[str, Any]:
    """
    Returns text, text_source ("text_layer", "ocr", "text_file" or "none"),
    page count, OCR lines with confidences, page images and pages_data.
    """
    ext = os.path.splitext(path)[1].lower()

    if ext == ".pdf":
        pdf = pdf_processor.process_pdf(path)
        images = pdf.get("images", [])
        if not pdf["is_scanned"]:
            return {
                "text": "\n\n".join(p["text"] for p in pdf["pages_data"] if p["text"]),
                "text_source": "text_layer",
                "pages": pdf["pages"],
                "pages_data": pdf["pages_data"],
                "lines": [],
                "images": images,
                "is_scanned": False,
            }
        lines: List[Dict[str, Any]] = []
        for img in images:
            lines.extend(_ocr_page(img["file_path"], img["page"]))
        return {
            **_from_lines(lines, pdf["pages"]),
            "pages": pdf["pages"],
            "lines": lines,
            "images": images,
            "is_scanned": True,
        }

    if ext in image_processor.SUPPORTED_FORMATS:
        lines = _ocr_page(path, 1)
        return {
            **_from_lines(lines, 1),
            "pages": 1,
            "lines": lines,
            "images": [{"page": 1, "file_path": path}],
            "is_scanned": True,
        }

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()
    return {
        "text": text,
        "text_source": "text_file",
        "pages": 1,
        "pages_data": [{"page": 1, "text": text, "char_count": len(text)}],
        "lines": [],
        "images": [],
        "is_scanned": False,
    }
