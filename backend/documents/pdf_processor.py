import hashlib
import io
import os
from typing import Any, Dict, List, Optional, Union
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

    def extract_page_images(self, source: Union[str, bytes], output_dir: Optional[str] = None) -> List[Dict[str, Any]]:
        """Extract embedded images from all PDF pages."""
        reader = self._get_reader(source)
        target_dir = output_dir or os.path.join(os.getcwd(), "outputs", "extracted_images")
        os.makedirs(target_dir, exist_ok=True)
        extracted_images: List[Dict[str, Any]] = []

        # Name images after their source so two PDFs never overwrite each other's pages.
        if isinstance(source, str):
            stem = os.path.splitext(os.path.basename(source))[0]
            digest = hashlib.sha1(os.path.abspath(source).encode("utf-8")).hexdigest()[:8]
        else:
            stem, digest = "pdf", hashlib.sha1(source[:65536]).hexdigest()[:8]

        for i, page in enumerate(reader.pages):
            try:
                for img_idx, img in enumerate(page.images):
                    img_filename = f"{stem}_{digest}_p{i+1}_img{img_idx}_{img.name}"
                    img_path = os.path.join(target_dir, img_filename)
                    with open(img_path, "wb") as f:
                        f.write(img.data)
                    extracted_images.append({
                        "page": i + 1,
                        "image_index": img_idx,
                        "name": img.name,
                        "file_path": img_path
                    })
            except Exception:
                pass
        return extracted_images

    def process_pdf(self, source: Union[str, bytes]) -> Dict[str, Any]:
        """
        Extract complete metadata, page count, full text, and embedded images from PDF.
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
        extracted_images = self.extract_page_images(source)

        return {
            "pages": num_pages,
            "total_chars": total_chars,
            "is_scanned": is_scanned,
            "text_extracted": not is_scanned,
            "metadata": metadata,
            "pages_data": pages_text,
            "images": extracted_images
        }

    def extract_full_text(self, source: Union[str, bytes]) -> str:
        """Extract concatenated text from all PDF pages."""
        result = self.process_pdf(source)
        return "\n\n".join(p["text"] for p in result["pages_data"] if p["text"])


pdf_processor = PDFProcessor()
