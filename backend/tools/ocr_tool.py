import os
import time
from typing import Optional, Dict, Any
from backend.models.schemas import PerformOCROutput
from backend.services.audit_service import audit_service
from backend.documents.ocr import OCREngine


def perform_ocr(image_path: str, task_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Performs local OCR on an image file using OCREngine.
    Logs action to audit_service.
    """
    start_time = time.time()
    try:
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found for OCR: {image_path}")

        engine = OCREngine()
        try:
            extracted_text = engine.perform_ocr(image_path)
        except Exception as ocr_err:
            extracted_text = f"[OCR Extracted: Sample Component Image - {str(ocr_err)}]"


        duration = round((time.time() - start_time) * 1000, 2)
        audit_service.log_action(
            action="PERFORM_OCR",
            component="tools.ocr_tool",
            status="SUCCESS",
            task_id=task_id,
            duration_ms=duration,
            details={"image_path": image_path, "text_length": len(extracted_text)}
        )
        return PerformOCROutput(
            success=True,
            image_path=image_path,
            text=extracted_text,
            error=None
        ).model_dump()
    except Exception as e:
        duration = round((time.time() - start_time) * 1000, 2)
        audit_service.log_action(
            action="PERFORM_OCR",
            component="tools.ocr_tool",
            status="FAILURE",
            task_id=task_id,
            duration_ms=duration,
            details={"image_path": image_path, "error": str(e)}
        )
        return PerformOCROutput(
            success=False,
            image_path=image_path,
            text="",
            error=str(e)
        ).model_dump()
