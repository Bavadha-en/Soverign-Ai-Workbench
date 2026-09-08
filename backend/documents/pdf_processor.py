import io
import os
from typing import Any, Dict, List, Union
import pypdf


class PDFProcessor:
    """
    Local PDF Processor for Industrial SOPs, Manuals, and Technical Reports.
    Operates 100% offline using pypdf.
    """

    def _get_reader(self, source: Union[str, bytes]) -> pypdf.PdfReader:
        """Create pypdf PdfReader from filepath or bytes."""
        if isinstance(source, bytes):
            return pypdf.PdfReader(io.BytesIO(source))
        elif isinstance(source, str):
            if not os.path.exists(source):
                raise FileNotFoundError(f"PDF file not found at: {source}")
            return pypdf.PdfReader(source)
        else:
            raise ValueError("Unsupported source type for PDF processing.")

    def process_pdf(self, source: Union[str, bytes]) -> Dict[str, Any]:
        """
        Extract complete metadata, page count, and full text from PDF.
        """
        reader = self._get_reader(source)
        num_pages = len(reader.pages)
        pages_text: List[Dict[str, Any]] = []
        total_chars = 0

        for i, page in enumerate(reader.pages):
            try:
                extracted = page.extract_text() or ""
            except Exception:
                extracted = ""
            pages_text.append({
                "page": i + 1,
                "text": extracted,
                "char_count": len(extracted)
            })
            total_chars += len(extracted)

        metadata = {}
        if reader.metadata:
            for k, v in reader.metadata.items():
                clean_k = str(k).lstrip("/")
                metadata[clean_k] = str(v)

        is_scanned = total_chars < 50 and num_pages > 0

        return {
            "pages": num_pages,
            "total_chars": total_chars,
            "is_scanned": is_scanned,
            "text_extracted": not is_scanned,
            "metadata": metadata,
            "pages_data": pages_text
        }

    def extract_full_text(self, source: Union[str, bytes]) -> str:
        """Extract concatenated text from all PDF pages."""
        result = self.process_pdf(source)
        return "\n\n".join(p["text"] for p in result["pages_data"] if p["text"])


pdf_processor = PDFProcessor()
