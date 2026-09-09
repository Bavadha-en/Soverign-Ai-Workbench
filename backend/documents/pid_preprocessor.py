import io
import os
import tempfile
from typing import Any, Dict, List, Optional, Tuple, Union
import cv2
import numpy as np
from PIL import Image, ImageEnhance


class PIDPreprocessor:
    """
    Robust P&ID Engineering Diagram Preprocessor and Tiling Engine.
    Operates offline using OpenCV and Pillow.
    Preserves original image integrity and generates multi-scale representations
    and coordinate-mapped overlapping tiles for localized high-precision inspection.
    """

    def __init__(self, temp_dir: Optional[str] = None):
        self.temp_dir = temp_dir or tempfile.gettempdir()

    def load_cv2_image(self, source: Union[str, bytes, np.ndarray, Image.Image]) -> np.ndarray:
        """Load image as BGR numpy array from various sources."""
        if isinstance(source, np.ndarray):
            if len(source.shape) == 2:
                return cv2.cvtColor(source, cv2.COLOR_GRAY2BGR)
            elif source.shape[2] == 4:
                return cv2.cvtColor(source, cv2.COLOR_RGBA2BGR)
            return source.copy()

        if isinstance(source, Image.Image):
            rgb = np.array(source.convert("RGB"))
            return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)

        if isinstance(source, bytes):
            nparr = np.frombuffer(source, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                raise ValueError("Failed to decode image bytes with OpenCV.")
            return img

        if isinstance(source, str):
            if not os.path.exists(source):
                raise FileNotFoundError(f"Image not found at path: {source}")
            img = cv2.imread(source, cv2.IMREAD_COLOR)
            if img is None:
                # Fallback to PIL for non-standard formats
                pil_img = Image.open(source).convert("RGB")
                img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            return img

        raise TypeError(f"Unsupported source type: {type(source)}")

    def preprocess(self, source: Union[str, bytes, np.ndarray, Image.Image]) -> Dict[str, Any]:
        """
        Generate full suite of preprocessed representations:
        1. original (BGR numpy array)
        2. resized (display normalized, max dim 1400)
        3. grayscale
        4. contrast_enhanced (CLAHE)
        5. thresholded (Otsu binarization)
        6. ocr_friendly (bilateral filter + adaptive threshold + morphological cleanup)
        7. metadata (dimensions, aspect ratio, channels)
        """
        original = self.load_cv2_image(source)
        h, w = original.shape[:2]

        # 2. Resized image (max dimension 1400 while preserving aspect ratio)
        scale = min(1.0, 1400.0 / max(h, w))
        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))
        resized = cv2.resize(original, (new_w, new_h), interpolation=cv2.INTER_AREA)

        # 3. Grayscale image
        grayscale = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)

        # 4. Contrast-enhanced image using CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        contrast_enhanced = clahe.apply(grayscale)

        # 5. Thresholded image (Otsu binarization, inverted so lines/text are white on black for morphology)
        # We also produce standard black-on-white threshold
        _, thresh_inv = cv2.threshold(grayscale, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        thresholded = cv2.bitwise_not(thresh_inv)

        # 6. OCR-friendly image (contrast boosted, light bilateral denoising to preserve crisp line edges)
        denoised = cv2.bilateralFilter(grayscale, d=5, sigmaColor=50, sigmaSpace=50)
        ocr_friendly = clahe.apply(denoised)

        metadata = {
            "width": w,
            "height": h,
            "channels": original.shape[2] if len(original.shape) > 2 else 1,
            "aspect_ratio": round(w / max(1, h), 3),
            "display_width": new_w,
            "display_height": new_h,
            "scale_factor": round(scale, 4)
        }

        return {
            "original": original,
            "resized": resized,
            "grayscale": grayscale,
            "contrast_enhanced": contrast_enhanced,
            "thresholded": thresholded,
            "thresholded_inv": thresh_inv,
            "ocr_friendly": ocr_friendly,
            "metadata": metadata
        }

    def generate_tiles(
        self,
        image: np.ndarray,
        tile_size: int = 512,
        overlap_ratio: float = 0.20
    ) -> List[Dict[str, Any]]:
        """
        Divide high-resolution P&ID into overlapping rectangular tiles.
        Each tile retains its exact coordinates (x, y, width, height) relative
        to the original diagram.

        Args:
            image: BGR or grayscale numpy array.
            tile_size: width and height of each square tile (default 512px).
            overlap_ratio: overlap fraction between adjacent tiles (default 20%).

        Returns:
            List of tile dicts:
            [{
                "tile_id": int,
                "x": int,
                "y": int,
                "width": int,
                "height": int,
                "image": np.ndarray (crop),
                "norm_bbox": [x_norm, y_norm, w_norm, h_norm]
            }]
        """
        h, w = image.shape[:2]
        step = max(64, int(tile_size * (1.0 - overlap_ratio)))

        tiles = []
        tile_id = 0

        y_starts = list(range(0, max(1, h - tile_size + 1), step))
        if not y_starts or y_starts[-1] + tile_size < h:
            y_starts.append(max(0, h - tile_size))

        x_starts = list(range(0, max(1, w - tile_size + 1), step))
        if not x_starts or x_starts[-1] + tile_size < w:
            x_starts.append(max(0, w - tile_size))

        # Ensure unique sorted starts
        y_starts = sorted(list(set(y_starts)))
        x_starts = sorted(list(set(x_starts)))

        for y in y_starts:
            for x in x_starts:
                tile_w = min(tile_size, w - x)
                tile_h = min(tile_size, h - y)
                crop = image[y:y + tile_h, x:x + tile_w].copy()

                tiles.append({
                    "tile_id": tile_id,
                    "x": x,
                    "y": y,
                    "width": tile_w,
                    "height": tile_h,
                    "image": crop,
                    "norm_bbox": [
                        round(x / w, 4),
                        round(y / h, 4),
                        round(tile_w / w, 4),
                        round(tile_h / h, 4)
                    ]
                })
                tile_id += 1

        return tiles

    def cv2_to_bytes(self, img: np.ndarray, ext: str = ".png") -> bytes:
        """Convert cv2 image to bytes without writing to disk."""
        success, encoded = cv2.imencode(ext, img)
        if not success:
            raise ValueError(f"Failed to encode image to {ext}")
        return encoded.tobytes()

    def cv2_to_base64(self, img: np.ndarray, ext: str = ".png") -> str:
        """Convert cv2 image to base64 string."""
        import base64
        return base64.b64encode(self.cv2_to_bytes(img, ext)).decode("utf-8")


pid_preprocessor = PIDPreprocessor()
