import base64
import io
import os
from typing import Any, Dict, Optional, Tuple, Union
from PIL import Image, ImageEnhance


class ImageProcessor:
    """
    Local Image Processing & Preprocessing Engine for Industrial Inspection Photos & Scanned Diagrams.
    Operates completely offline using Pillow.
    """

    SUPPORTED_FORMATS = {".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"}

    def load_image(self, source: Union[str, bytes]) -> Image.Image:
        """Load PIL Image from file path or raw bytes."""
        if isinstance(source, bytes):
            return Image.open(io.BytesIO(source))
        elif isinstance(source, str):
            if not os.path.exists(source):
                raise FileNotFoundError(f"Image not found at path: {source}")
            return Image.open(source)
        else:
            raise ValueError("Unsupported source type for image loading.")

    def process_image(self, source: Union[str, bytes]) -> Dict[str, Any]:
        """
        Extract image metadata, format, and dimension statistics for inspection logging.
        """
        img = self.load_image(source)
        return {
            "width": img.width,
            "height": img.height,
            "format": img.format or "UNKNOWN",
            "mode": img.mode,
            "is_animated": getattr(img, "is_animated", False),
            "aspect_ratio": round(img.width / img.height, 3) if img.height > 0 else 1.0
        }

    def image_to_base64(self, source: Union[str, bytes], format: str = "PNG") -> str:
        """
        Convert image to Base64 encoded string for local Multimodal VLM inference (Ollama / LLaVA / Moondream).
        """
        if isinstance(source, bytes):
            return base64.b64encode(source).decode("utf-8")

        img = self.load_image(source)
        # Convert RGBA to RGB if saving as JPEG
        if format.upper() in ("JPG", "JPEG") and img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        buffered = io.BytesIO()
        img.save(buffered, format=format)
        return base64.b64encode(buffered.getvalue()).decode("utf-8")

    def enhance_for_inspection(
        self,
        source: Union[str, bytes],
        contrast_factor: float = 1.5,
        sharpness_factor: float = 1.3
    ) -> bytes:
        """
        Enhance scanned document or industrial inspection photo to improve OCR and defect detection.
        """
        img = self.load_image(source)
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")

        # Enhance contrast
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(contrast_factor)

        # Enhance sharpness
        sharpener = ImageEnhance.Sharpness(img)
        img = sharpener.enhance(sharpness_factor)

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()


image_processor = ImageProcessor()
