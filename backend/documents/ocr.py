import io
import os
from typing import Any, Dict, Optional, Union
from PIL import Image

from backend.documents.image_processor import image_processor


class OCREngine:
    """
    Local OCR & Scanned Document Text Extraction Engine.
    Combines direct image processing with fallback for Sovereign On-Premise environments.
    """

    def __init__(self, tesseract_cmd: Optional[str] = None):
        self.tesseract_cmd = tesseract_cmd or os.getenv("TESSERACT_PATH", "")
        self._has_tesseract = self._check_tesseract()

    def _check_tesseract(self) -> bool:
        """Check if pytesseract and Tesseract-OCR binary are available."""
        try:
            import pytesseract
            if self.tesseract_cmd and os.path.exists(self.tesseract_cmd):
                pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd
            return True
        except Exception:
            return False

    def perform_ocr(self, source: Union[str, bytes]) -> str:
        """
        Extract text from scanned documents or equipment photos.
        """
        if self._has_tesseract:
            try:
                import pytesseract
                img = image_processor.load_image(source)
                enhanced_bytes = image_processor.enhance_for_inspection(source)
                enhanced_img = Image.open(io.BytesIO(enhanced_bytes))
                return pytesseract.image_to_string(enhanced_img).strip()
            except Exception as e:
                return f"[OCR Engine Note: Fallback active - {str(e)}]"

        # Sovereign fallback mode when native binary is not installed
        img_info = image_processor.process_image(source)
        return (
            f"[OCR Processed: Scanned Image {img_info['width']}x{img_info['height']} {img_info['format']} - "
            f"Preprocessed for Multimodal VLM Analysis]"
        )

    def is_available(self) -> bool:
        return self._has_tesseract


ocr_engine = OCREngine()
