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
    "SPG", "SPN", "SPA", "SPD", "AT", "AI", "ZT", "ZI", "PDT", "PDI", "PDIC"
}

EQUIPMENT_PREFIXES = {
    "P", "PU", "PUMP",
    "V", "TK", "T", "VESSEL", "TANK",
    "E", "HE", "EX", "HEX",
    "C", "COMP", "K",
    "R", "REACTOR",
    "F", "FL", "FILTER",
    "S", "STR", "STRAINER",
    "M", "MOT", "MOTOR",
    "BL", "BLOWER",
    "NOTE", "CBJ",
    "L", "PL"
}

KNOWN_TAG_PREFIXES = ISA_INSTRUMENT_PREFIXES | EQUIPMENT_PREFIXES


def _deskew(img: np.ndarray, max_angle: float = 5.0, step: float = 0.2, min_angle: float = 1.0) -> Tuple[np.ndarray, float]:
    """
    Straighten a scanned page. Tries small rotations and keeps the one whose
    rows of ink line up best (highest variance of the horizontal projection).
    Pages skewed by less than `min_angle` degrees are returned unchanged.
    """
    import cv2

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img
    scale = min(1.0, 800.0 / max(gray.shape))
    small = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA) if scale < 1.0 else gray
    ink = 255 - cv2.threshold(small, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    h, w = ink.shape
    best_score, best_angle = -1.0, 0.0
    for angle in np.arange(-max_angle, max_angle + 1e-9, step):
        m = cv2.getRotationMatrix2D((w / 2, h / 2), float(angle), 1.0)
        rotated = cv2.warpAffine(ink, m, (w, h), flags=cv2.INTER_NEAREST, borderValue=0)
        score = float(np.var(rotated.sum(axis=1)))
        if score > best_score:
            best_score, best_angle = score, float(angle)
    if abs(best_angle) < min_angle:
        return img, best_angle
    height, width = img.shape[:2]
    m = cv2.getRotationMatrix2D((width / 2, height / 2), best_angle, 1.0)
    border = (255, 255, 255) if img.ndim == 3 else 255
    return cv2.warpAffine(img, m, (width, height), flags=cv2.INTER_CUBIC, borderValue=border), best_angle


def normalize_engineering_tag(raw_text: str) -> Optional[str]:
    """
    Tolerantly normalize OCR strings into standard ISA-5.1 / engineering equipment tags.
    Handles delimiters (spaces, underscores, hyphens, colons) and unseparated prefixes:
      'P101', 'P 101', 'P_101' -> 'P-101'
      'T101', 'T 101', 'T_101' -> 'T-101'
      'V101', 'V 101', 'V_101' -> 'V-101'
      'E101', 'E 101', 'E_101' -> 'E-101'
      'FIC101', 'FIC 101', 'FIC_101' -> 'FIC-101'
      'LIC101', 'LIC 101', 'LIC_101' -> 'LIC-101'
      'PIC101', 'PIC 101', 'PIC_101' -> 'PIC-101'
      'XV101', 'XV 101', 'XV_101' -> 'XV-101'
      'FO 1035' -> 'FO-1035'
      'PI-1027' -> 'PI-1027'
      'SPG 4002' -> 'SPG-4002'
    Does NOT blindly normalize arbitrary non-engineering text (e.g. 'PUMP', 'INLET', 'SHEET 1').
    """
    if not raw_text:
        return None
    s = raw_text.strip().upper()

    # Clean leading/trailing non-alphanumeric punctuation (except quote marks for pipe sizes)
    s = re.sub(r"^[^A-Z0-9\"]+|[^A-Z0-9]+$", "", s)

    # 1. Check piping line notation: e.g. '2"-PL-101', '3"-L-102', 'L-101'
    m_pipe = re.match(r'^(?:(\d+["\']?)-)?([A-Z]{1,3})[\s_\-]?([0-9]{2,5}[A-Z]?)$', s)
    if m_pipe:
        size, prefix, num = m_pipe.group(1), m_pipe.group(2), m_pipe.group(3)
        if prefix in {"L", "PL", "CW", "IA", "PW", "RW", "ST", "SL", "FG", "DG"}:
            size_prefix = f"{size}-" if size else ""
            return f"{size_prefix}{prefix}-{num}"

    # 2. Match with explicit separator (spaces, underscores, hyphens, slashes, colons)
    # E.g. P 101, P_101, P-101, FIC 101, FIC_101, XV-101, T 101, E_101
    m_sep = re.match(r"^([A-Z]{1,5})[\s_\-\.:/]+([0-9]{1,5}[A-Z]?)$", s)
    if m_sep:
        prefix, num = m_sep.group(1), m_sep.group(2)
        if prefix in KNOWN_TAG_PREFIXES or len(prefix) <= 3:
            # Clean single letter pump / tank / valve / exchanger
            if prefix in {"PU", "PUMP"}:
                return f"P-{num}"
            if prefix in {"TK", "TANK"}:
                return f"T-{num}"
            if prefix in {"HEX", "EX"}:
                return f"E-{num}"
            if prefix in {"COMP"}:
                return f"C-{num}"
            return f"{prefix}-{num}"

    # 3. Match contiguous token without separator: e.g. P101, T101, V101, E101, FIC101, LIC101, PIC101, XV101
    # We match against known prefixes first (longest prefix match)
    for pfx in sorted(KNOWN_TAG_PREFIXES, key=lambda x: -len(x)):
        if s.startswith(pfx):
            rem = s[len(pfx):].strip(" _-")
            if re.match(r"^[0-9]{2,5}[A-Z]?$", rem):
                norm_pfx = pfx
                if norm_pfx in {"PU", "PUMP"}:
                    norm_pfx = "P"
                elif norm_pfx in {"TK", "TANK"}:
                    norm_pfx = "T"
                elif norm_pfx in {"HEX", "EX"}:
                    norm_pfx = "E"
                elif norm_pfx in {"COMP"}:
                    norm_pfx = "C"
                return f"{norm_pfx}-{rem}"

    # 4. Specific known multi-word patterns like NOTE-15, CBJ-01
    m_note = re.match(r"^(NOTE|CBJ|DWG|SOP)[\s_\-]?([0-9]{1,4})$", s)
    if m_note:
        return f"{m_note.group(1)}-{m_note.group(2)}"

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
        min_confidence: float = 0.50,
        source_tile: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract normalized engineering equipment and instrumentation tags from diagram.
        Includes tolerant regex normalization and 2-line instrument bubble merging (e.g. PT over 1027).
        Preserves raw OCR text, normalized tag, calibrated confidence, bounding box, and source tile.
        """
        raw_items = self.perform_ocr_detailed(source)
        if not raw_items:
            return []

        def _conf_level(c: float) -> str:
            if c >= 0.85:
                return "HIGH"
            if c >= 0.65:
                return "MEDIUM"
            if c >= 0.45:
                return "LOW"
            return "UNKNOWN"

        tags: List[Dict[str, Any]] = []
        consumed_indices = set()

        # Step 1: Check single-line tags
        for i, item in enumerate(raw_items):
            if item["confidence"] < min_confidence:
                continue
            normalized = normalize_engineering_tag(item["text"])
            if normalized:
                c_val = item["confidence"]
                tags.append({
                    "text": normalized,
                    "normalized_tag": normalized,
                    "raw_text": item["text"],
                    "confidence": c_val,
                    "confidence_level": _conf_level(c_val),
                    "bbox": item["bbox"],
                    "source_tile": source_tile,
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
                                "normalized_tag": merged_tag,
                                "raw_text": f"{top['text']} / {bot['text']}",
                                "confidence": combined_conf,
                                "confidence_level": _conf_level(combined_conf),
                                "bbox": combined_bbox,
                                "source_tile": source_tile,
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


    def perform_ocr_document(self, source: Union[str, np.ndarray], deskew: bool = True) -> List[Dict[str, Any]]:
        """
        OCR a scanned report page and return its text lines from top to bottom.

        Report pages are upright, so the text-direction classifier is switched
        off: on the demo scans it turned a whole line upside down and dropped the
        seal-leakage reading entirely. Boxes on the same row are joined into one
        line, and each line keeps its lowest recognition confidence so doubtful
        reads can be flagged for review instead of trusted.
        """
        if not self._has_rapidocr:
            return []
        import cv2

        img = cv2.imread(source) if isinstance(source, str) else source
        if img is None:
            return []
        angle = 0.0
        if deskew:
            img, angle = _deskew(img)
        try:
            results, _ = self._rapidocr_engine(img, use_cls=False)
        except Exception:
            return []

        items = []
        for poly, text, conf in results or []:
            text = str(text).strip()
            if not text:
                continue
            xs = [p[0] for p in poly]
            ys = [p[1] for p in poly]
            items.append({
                "text": text,
                "confidence": round(float(conf), 3),
                "x": min(xs), "y": min(ys),
                "w": max(xs) - min(xs), "h": max(ys) - min(ys),
            })
        items.sort(key=lambda it: it["y"] + it["h"] / 2)

        rows: List[Dict[str, Any]] = []
        for it in items:
            cy = it["y"] + it["h"] / 2
            if rows and abs(cy - rows[-1]["cy"]) < 0.5 * min(it["h"], rows[-1]["h"]):
                rows[-1]["items"].append(it)
                continue
            rows.append({"cy": cy, "h": it["h"], "items": [it]})

        lines = []
        for row in rows:
            parts = sorted(row["items"], key=lambda it: it["x"])
            x0 = min(p["x"] for p in parts)
            y0 = min(p["y"] for p in parts)
            x1 = max(p["x"] + p["w"] for p in parts)
            y1 = max(p["y"] + p["h"] for p in parts)
            lines.append({
                "text": " ".join(p["text"] for p in parts),
                "confidence": min(p["confidence"] for p in parts),
                "bbox": [int(x0), int(y0), int(x1 - x0), int(y1 - y0)],
                "deskew_angle": round(angle, 1),
            })
        return lines

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
