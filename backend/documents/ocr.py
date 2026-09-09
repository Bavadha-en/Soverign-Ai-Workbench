import io
import os
import re
from typing import Any, Dict, List, Optional, Tuple, Union
from PIL import Image
import numpy as np

from backend.documents.image_processor import image_processor


# Standard ISA-5.1 Instrument & Equipment Letter Codes
ISA_INSTRUMENT_PREFIXES = {
    "PT", "PI", "PIC", "PIT",
    "FT", "FI", "FIC", "FIT",
    "LT", "LI", "LIC", "LIT",
    "TT", "TI", "TIC", "TIT",
    "CV", "PV", "FV", "LV", "TV", "XV", "SV", "PSV", "PRV", "SDV", "BDV", "ESDV",
    "FO", "RO", "FE", "TE", "LE", "PE",
    "SPG", "AT", "AI", "ZT", "ZI", "PDT", "PDI", "PDIC"
}

EQUIPMENT_PREFIXES = {
    "P", "PU", "PUMP",
    "V", "TK", "T", "VESSEL", "TANK",
    "E", "HE", "EX",
    "C", "COMP", "K",
    "R", "REACTOR",
    "F", "FL", "FILTER",
    "S", "STR", "STRAINER"
}


def normalize_engineering_tag(raw_text: str) -> Optional[str]:
    """
    Tolerantly normalize OCR strings into standard ISA-5.1 / engineering equipment tags.
    Examples:
      'P101' -> 'P-101'
      'CV101' -> 'CV-101'
      'PT 1027' -> 'PT-1027'
      'PI-1027' -> 'PI-1027'
      'FO 1035' -> 'FO-1035'
      'SPG 4002' -> 'SPG-4002'
      'V-101' -> 'V-101'
    """
    if not raw_text:
        return None
    s = raw_text.strip().upper()

    # Clean punctuation around the tag
    s = re.sub(r"^[^\w]+|[^\w]+$", "", s)

    # Direct match: LETTERS followed by optional separator followed by NUMBERS
    # E.g., PT-1027, P-101, CV101, FO 1035, SPG-4002
    m = re.match(r"^([A-Z]{1,5})[\s_\-\.:/]*([0-9]{2,5}[A-Z]?)$", s)
    if m:
        prefix, num = m.group(1), m.group(2)
        if prefix in ISA_INSTRUMENT_PREFIXES or prefix in EQUIPMENT_PREFIXES or len(prefix) <= 4:
            return f"{prefix}-{num}"

    # Valve prefix match: V101 -> V-101, V-101 -> V-101
    m_valve = re.match(r"^(V|CV|PV|FV|LV|TV|XV|SV|PSV|ESDV)[\s_\-]?([0-9]{2,5}[A-Z]?)$", s)
    if m_valve:
        return f"{m_valve.group(1)}-{m_valve.group(2)}"

    # Pump prefix match: P101 -> P-101, P-101 -> P-101
    m_pump = re.match(r"^(P|PU)[\s_\-]?([0-9]{2,5}[A-Z]?)$", s)
    if m_pump:
        return f"P-{m_pump.group(2)}"

    return None


class OCREngine:
    """
    Local OCR & Scanned Document Text Extraction Engine.
    Powered by local RapidOCR (ONNX Runtime) with tolerant ISA-5.1 engineering tag detection
    and fallback for air-gapped / sovereign on-premise environments.
    """

    def __init__(self, tesseract_cmd: Optional[str] = None):
        self.tesseract_cmd = tesseract_cmd or os.getenv("TESSERACT_PATH", "")
        self._has_rapidocr = False
        self._rapidocr_engine = None
        self._init_rapidocr()

    def _init_rapidocr(self) -> None:
        """Initialize local RapidOCR ONNX engine."""
        try:
            from rapidocr_onnxruntime import RapidOCR
            self._rapidocr_engine = RapidOCR()
            self._has_rapidocr = True
        except Exception:
            self._has_rapidocr = False

    def is_available(self) -> bool:
        return self._has_rapidocr

    def _source_to_numpy_or_path(self, source: Union[str, bytes]) -> Union[str, np.ndarray]:
        """Convert input source to format expected by RapidOCR."""
        if isinstance(source, str) and os.path.exists(source):
            return source
        elif isinstance(source, bytes):
            nparr = np.frombuffer(source, np.uint8)
            import cv2
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            return img if img is not None else source
        return source

    def perform_ocr_detailed(self, source: Union[str, bytes, np.ndarray]) -> List[Dict[str, Any]]:
        """
        Run OCR and return list of detected items with text, confidence, and [x, y, w, h] bbox.
        """
        if not self._has_rapidocr:
            return []

        try:
            target = source
            if isinstance(source, bytes):
                nparr = np.frombuffer(source, np.uint8)
                import cv2
                target = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            results, _ = self._rapidocr_engine(target)
            if not results:
                return []

            parsed = []
            for item in results:
                poly = item[0]  # 4 points: [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
                text = str(item[1]).strip()
                conf = round(float(item[2]), 3)

                # Compute axis-aligned bounding box [x, y, width, height]
                xs = [p[0] for p in poly]
                ys = [p[1] for p in poly]
                x_min = int(min(xs))
                y_min = int(min(ys))
                x_max = int(max(xs))
                y_max = int(max(ys))
                w = max(1, x_max - x_min)
                h = max(1, y_max - y_min)

                parsed.append({
                    "text": text,
                    "confidence": conf,
                    "bbox": [x_min, y_min, w, h],
                    "poly": poly,
                    "source": "ocr"
                })
            return parsed
        except Exception:
            return []

    def extract_engineering_tags(
        self,
        source: Union[str, bytes, np.ndarray],
        min_confidence: float = 0.50
    ) -> List[Dict[str, Any]]:
        """
        Extract normalized engineering equipment and instrumentation tags from diagram.
        Includes tolerant regex normalization and 2-line instrument bubble merging (e.g. PT over 1027).
        """
        raw_items = self.perform_ocr_detailed(source)
        if not raw_items:
            return []

        tags: List[Dict[str, Any]] = []
        consumed_indices = set()

        # Step 1: Check single-line tags
        for i, item in enumerate(raw_items):
            if item["confidence"] < min_confidence:
                continue
            normalized = normalize_engineering_tag(item["text"])
            if normalized:
                tags.append({
                    "text": normalized,
                    "raw_text": item["text"],
                    "confidence": item["confidence"],
                    "bbox": item["bbox"],
                    "source": "ocr"
                })
                consumed_indices.add(i)

        # Step 2: Bubble stacking merger: Top text is letters (e.g. 'PT', 'PI', 'FO', 'SPG'),
        # bottom text is digits (e.g. '1027', '1035', '4002') in close vertical proximity
        for i, top in enumerate(raw_items):
            if i in consumed_indices or top["confidence"] < min_confidence:
                continue
            top_text = top["text"].strip().upper()
            if top_text in ISA_INSTRUMENT_PREFIXES or top_text in EQUIPMENT_PREFIXES or (top_text.isalpha() and 2 <= len(top_text) <= 4):
                top_bx, top_by, top_bw, top_bh = top["bbox"]
                top_center_x = top_bx + top_bw / 2.0
                top_bottom_y = top_by + top_bh

                # Look for a numeric token just below top
                for j, bot in enumerate(raw_items):
                    if j in consumed_indices or i == j or bot["confidence"] < min_confidence:
                        continue
                    bot_text = bot["text"].strip()
                    if bot_text.isdigit() and 2 <= len(bot_text) <= 5:
                        bot_bx, bot_by, bot_bw, bot_bh = bot["bbox"]
                        bot_center_x = bot_bx + bot_bw / 2.0
                        bot_top_y = bot_by

                        # Check proximity: horizontal alignment within 30px, vertical gap within 45px
                        dx = abs(top_center_x - bot_center_x)
                        dy = bot_top_y - top_bottom_y
                        if dx <= max(35, top_bw) and -10 <= dy <= 50:
                            merged_tag = f"{top_text}-{bot_text}"
                            combined_bbox = [
                                min(top_bx, bot_bx),
                                min(top_by, bot_by),
                                max(top_bx + top_bw, bot_bx + bot_bw) - min(top_bx, bot_bx),
                                max(top_by + top_bh, bot_by + bot_bh) - min(top_by, bot_by)
                            ]
                            combined_conf = round((top["confidence"] + bot["confidence"]) / 2.0, 3)
                            tags.append({
                                "text": merged_tag,
                                "raw_text": f"{top['text']} / {bot['text']}",
                                "confidence": combined_conf,
                                "bbox": combined_bbox,
                                "source": "ocr"
                            })
                            consumed_indices.add(i)
                            consumed_indices.add(j)
                            break

        # Deduplicate tags by text and proximity
        unique_tags = []
        seen = set()
        for t in sorted(tags, key=lambda x: -x["confidence"]):
            key = (t["text"], t["bbox"][0] // 20, t["bbox"][1] // 20)
            if key not in seen:
                seen.add(key)
                unique_tags.append(t)

        return unique_tags

    def perform_ocr(self, source: Union[str, bytes]) -> str:
        """
        Extract text from scanned documents or equipment photos.
        Backwards-compatible method returning clean consolidated string.
        """
        detailed = self.perform_ocr_detailed(source)
        if detailed:
            return "\n".join(item["text"] for item in detailed if item["text"].strip())

        # Fallback mode when no text detected
        try:
            img_info = image_processor.process_image(source)
            return (
                f"[OCR Processed: Scanned Image {img_info['width']}x{img_info['height']} {img_info['format']} - "
                f"Preprocessed for Multimodal VLM Analysis]"
            )
        except Exception:
            return "[OCR Processed: Scanned Image Preprocessed for Multimodal VLM Analysis]"


ocr_engine = OCREngine()
