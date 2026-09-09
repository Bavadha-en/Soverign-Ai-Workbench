import os
import time
from typing import Optional, Dict, Any
from backend.models.schemas import ExtractPDFOutput
from backend.services.audit_service import audit_service


def extract_pdf(file_path: str, task_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Extracts text and metadata from a PDF file using PyMuPDF (fitz) or PDFProcessor.
    Logs action to audit_service.
    """
    start_time = time.time()
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        try:
            import fitz
            doc = fitz.open(file_path)
            pages_count = len(doc)
            extracted_text_list = []
            ocr_pages = []

            for i, page in enumerate(doc):
                text = page.get_text()
                if text.strip():
                    extracted_text_list.append(f"--- Page {i+1} ---\n{text}")
                else:
                    ocr_pages.append(i + 1)

            full_text = "\n\n".join(extracted_text_list)
            text_extracted = len(full_text.strip()) > 0
            doc.close()
        except Exception:
            from backend.documents.pdf_processor import PDFProcessor
            processor = PDFProcessor()
            res = processor.process_pdf(file_path)
            pages_count = res.get("pages", 1)
            full_text = res.get("text", "Extracted PDF content")
            text_extracted = res.get("text_extracted", True)
            ocr_pages = res.get("ocr_pages", [])

        duration = round((time.time() - start_time) * 1000, 2)
        audit_service.log_action(
            action="EXTRACT_PDF",
            component="tools.pdf_tool",
            status="SUCCESS",
            task_id=task_id,
            duration_ms=duration,
            details={"file_path": file_path, "pages": pages_count, "ocr_pages": ocr_pages}
        )
        return ExtractPDFOutput(
            success=True,
            file_path=file_path,
            pages=pages_count,
            text=full_text,
            text_extracted=text_extracted,
            ocr_pages=ocr_pages,
            error=None
        ).model_dump()
    except Exception as e:
        duration = round((time.time() - start_time) * 1000, 2)
        audit_service.log_action(
            action="EXTRACT_PDF",
            component="tools.pdf_tool",
            status="FAILURE",
            task_id=task_id,
            duration_ms=duration,
            details={"file_path": file_path, "error": str(e)}
        )
        return ExtractPDFOutput(
            success=False,
            file_path=file_path,
            pages=0,
            text="",
            text_extracted=False,
            ocr_pages=[],
            error=str(e)
        ).model_dump()
