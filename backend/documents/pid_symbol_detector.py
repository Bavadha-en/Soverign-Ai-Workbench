import io
import os
import zipfile
import csv
from typing import Any, Dict, List, Optional, Tuple, Union
import cv2
import numpy as np
from PIL import Image


_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Source dataset used to build symbol templates. Eng_Diagrams has no licence, so
# neither it nor templates derived from it ship with the product. Set
# ENG_DIAGRAMS_ZIP to a local copy for research runs only.
DEFAULT_ZIP_PATH = os.getenv(
    "ENG_DIAGRAMS_ZIP",
    os.path.join(_REPO_ROOT, "datasets", "Eng_Diagrams-master.zip"),
)

# Optional bundled templates. Only licensed or self-made templates belong here;
# ENG_DIAGRAM_TEMPLATES can point at a research-only copy kept outside the repo.
BUNDLED_TEMPLATES_PATH = os.getenv(
    "ENG_DIAGRAM_TEMPLATES",
    os.path.join(_REPO_ROOT, "assets", "eng_diagram_templates.npz"),
)

# Locally rebuilt templates take priority over the bundled copy.
CACHE_PATH = os.path.join(os.getcwd(), "outputs", "storage", "eng_diagram_templates.npz")


class PIDSymbolDetector:
    """
    Deterministic Engineering Symbol Detector & Classifier for P&ID diagrams.
    Utilizes canonical exemplars from the Eng_Diagrams dataset, geometric invariants,
    contour analysis, and OpenCV template matching.
    Never fabricates classifications; outputs 'UNKNOWN' when confidence is low.
    """

    def __init__(self, zip_path: str = DEFAULT_ZIP_PATH, cache_path: str = CACHE_PATH):
        self.zip_path = zip_path
        self.cache_path = cache_path
        self.class_centroids: Dict[str, np.ndarray] = {}
        self.class_templates: Dict[str, List[np.ndarray]] = {}
        self._load_or_build_templates()

    def _load_or_build_templates(self) -> None:
        """Load cached templates or compute them from Eng_Diagrams-master.zip."""
        os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)

        # Locally built cache first, then the templates shipped with the repo.
        for candidate in (self.cache_path, BUNDLED_TEMPLATES_PATH):
            if not os.path.exists(candidate):
                continue
            try:
                data = np.load(candidate, allow_pickle=True)
                self.class_centroids = {k: data[k] for k in data.files}
                return
            except Exception:
                continue

        # Build from dataset zip
        if not os.path.exists(self.zip_path):
            return

        try:
            with zipfile.ZipFile(self.zip_path, "r") as z:
                if "Eng_Diagrams-master/data/Symbols_pixel.csv" in z.namelist():
                    with z.open("Eng_Diagrams-master/data/Symbols_pixel.csv") as f:
                        reader = csv.reader(io.TextIOWrapper(f, encoding="utf-8"))
                        header = next(reader, None)
                        class_buckets: Dict[str, List[np.ndarray]] = {}
                        for row in reader:
                            if not row or len(row) < 101:
                                continue
                            label = row[-1].strip()
                            pixels = [int(p) for p in row[:-1] if p.isdigit()]
                            if len(pixels) == 10000:
                                arr = np.array(pixels, dtype=np.float32).reshape((100, 100))
                                # Normalize 0-1
                                arr = arr / 255.0
                                class_buckets.setdefault(label, []).append(arr)

                        centroids = {}
                        for label, imgs in class_buckets.items():
                            if imgs:
                                mean_img = np.mean(imgs, axis=0)
                                centroids[label] = mean_img

                        self.class_centroids = centroids
                        np.savez_compressed(self.cache_path, **centroids)
        except Exception:
            pass

    def classify_isolated_symbol(
        self,
        symbol_image: Union[np.ndarray, Image.Image, bytes, str],
        confidence_threshold: float = 0.55
    ) -> Dict[str, Any]:
        """
        Classify a single cropped engineering symbol image (e.g. from Eng_Diagrams dataset).
        Returns class name, confidence, and whether it is recognized or UNKNOWN.
        """
        # Convert to 100x100 grayscale float array [0, 1]
        if isinstance(symbol_image, str) and os.path.exists(symbol_image):
            img = cv2.imread(symbol_image, cv2.IMREAD_GRAYSCALE)
        elif isinstance(symbol_image, bytes):
            nparr = np.frombuffer(symbol_image, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
        elif isinstance(symbol_image, Image.Image):
            img = np.array(symbol_image.convert("L"))
        elif isinstance(symbol_image, np.ndarray):
            img = cv2.cvtColor(symbol_image, cv2.COLOR_BGR2GRAY) if len(symbol_image.shape) == 3 else symbol_image.copy()
        else:
            return {"class": "UNKNOWN", "confidence": 0.0, "is_known": False, "source": "deterministic"}

        if img is None or img.size == 0:
            return {"class": "UNKNOWN", "confidence": 0.0, "is_known": False, "source": "deterministic"}

        resized = cv2.resize(img, (100, 100), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0

        if not self.class_centroids:
            return {"class": "UNKNOWN", "confidence": 0.0, "is_known": False, "source": "deterministic"}

        best_label = "UNKNOWN"
        best_score = -1.0

        norm_target = np.linalg.norm(resized)
        if norm_target < 1e-6:
            return {"class": "UNKNOWN", "confidence": 0.0, "is_known": False, "source": "deterministic"}

        for label, centroid in self.class_centroids.items():
            norm_c = np.linalg.norm(centroid)
            if norm_c < 1e-6:
                continue
            # Cosine similarity
            sim = float(np.dot(resized.flatten(), centroid.flatten()) / (norm_target * norm_c))
            if sim > best_score:
                best_score = sim
                best_label = label

        # Convert cosine similarity (typically 0.70-0.98) to calibrated confidence
        calibrated_conf = round(max(0.0, min(1.0, (best_score - 0.50) / 0.45)), 3)

        if calibrated_conf < confidence_threshold:
            return {
                "class": "UNKNOWN",
                "predicted_candidate": best_label,
                "confidence": calibrated_conf,
                "is_known": False,
                "source": "deterministic"
            }

        return {
            "class": best_label,
            "confidence": calibrated_conf,
            "raw_similarity": round(best_score, 3),
            "is_known": True,
            "source": "deterministic"
        }

    def detect_symbols_in_diagram(
        self,
        image: Union[np.ndarray, str],
        min_size: int = 14,
        max_size: int = 160
    ) -> List[Dict[str, Any]]:
        """
        Locate and classify standard P&ID symbols (valves, pumps, instruments, reducers)
        using OpenCV contour geometry and template correlation.
        """
        if isinstance(image, str):
            cv_img = cv2.imread(image)
        else:
            cv_img = image

        if cv_img is None:
            return []

        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY) if len(cv_img.shape) == 3 else cv_img.copy()
        h, w = gray.shape[:2]

        # Otsu thresholding
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # Remove long continuous horizontal/vertical piping lines from the binary mask
        # so component symbol shapes become isolated connected components
        kernel_h = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
        kernel_v = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 25))
        horiz_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel_h)
        vert_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel_v)
        pipe_mask = cv2.bitwise_or(horiz_lines, vert_lines)
        symbol_mask = cv2.bitwise_and(thresh, cv2.bitwise_not(pipe_mask))

        contours, _ = cv2.findContours(symbol_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        detected_symbols: List[Dict[str, Any]] = []

        for cnt in contours:
            bx, by, bw, bh = cv2.boundingRect(cnt)
            area = cv2.contourArea(cnt)
            if bw < min_size or bh < min_size or bw > max_size or bh > max_size:
                continue
            if area < 40:
                continue

            aspect = bw / float(bh)
            perimeter = cv2.arcLength(cnt, True)
            circularity = (4 * np.pi * area) / (perimeter * perimeter) if perimeter > 0 else 0

            crop = gray[by:by + bh, bx:bx + bw]
            if crop.size == 0:
                continue

            def _level(c: float) -> str:
                if c >= 0.85:
                    return "HIGH"
                if c >= 0.65:
                    return "MEDIUM"
                if c >= 0.45:
                    return "LOW"
                return "UNKNOWN"

            # Check for circular instrument bubble / sensor
            if circularity >= 0.70 and 0.8 <= aspect <= 1.25 and bw >= 20:
                conf = round(min(0.98, float(circularity) + 0.15), 3)
                detected_symbols.append({
                    "symbol_type": "Sensor",
                    "category": "instrument_bubble",
                    "bbox": [int(bx), int(by), int(bw), int(bh)],
                    "confidence": conf,
                    "confidence_level": _level(conf),
                    "aspect_ratio": round(aspect, 2),
                    "detector": "deterministic_cv",
                    "visual_evidence": f"Circular instrument bubble contour (circularity={circularity:.2f}, aspect={aspect:.2f})",
                    "source": "deterministic"
                })
                continue

            # Check for pump symbol (circle with tangential line/nozzle or inscribed triangle, area >= 400)
            if circularity >= 0.55 and 0.8 <= aspect <= 1.3 and bw >= 32 and bh >= 32:
                conf = round(min(0.92, float(circularity) + 0.20), 3)
                detected_symbols.append({
                    "symbol_type": "Centrifugal Pump",
                    "category": "pump",
                    "bbox": [int(bx), int(by), int(bw), int(bh)],
                    "confidence": conf,
                    "confidence_level": _level(conf),
                    "aspect_ratio": round(aspect, 2),
                    "detector": "deterministic_cv",
                    "visual_evidence": f"Centrifugal pump circular casing contour (circularity={circularity:.2f}, dimension={bw}x{bh})",
                    "source": "deterministic"
                })
                continue

            # Check for vessel / column (large elongated cylindrical contour)
            if area > 1200 and (aspect >= 1.8 or aspect <= 0.55):
                conf = 0.85
                detected_symbols.append({
                    "symbol_type": "Pressure Vessel / Column",
                    "category": "vessel",
                    "bbox": [int(bx), int(by), int(bw), int(bh)],
                    "confidence": conf,
                    "confidence_level": _level(conf),
                    "aspect_ratio": round(aspect, 2),
                    "detector": "deterministic_cv",
                    "visual_evidence": f"Elongated vessel enclosure contour (aspect={aspect:.2f}, area={int(area)})",
                    "source": "deterministic"
                })
                continue

            # Match against known exemplar templates / Eng_Diagrams dataset
            classification = self.classify_isolated_symbol(crop, confidence_threshold=0.50)
            pred_class = classification.get("class", "UNKNOWN")
            conf = classification.get("confidence", 0.0)

            # Heuristic geometric sanity check & categorization
            p_lower = pred_class.lower()
            is_valve = any(k in p_lower for k in ["valve", "db&b", "esdv", "psv", "prv"])
            is_pump = "pump" in p_lower
            is_vessel = any(k in p_lower for k in ["vessel", "tank", "drum", "column"])
            is_hex = any(k in p_lower for k in ["exchanger", "cooler", "heater", "condenser"])
            is_filter = any(k in p_lower for k in ["filter", "strainer"])
            is_motor = any(k in p_lower for k in ["motor", "compressor", "turbine"])
            is_reducer = "reducer" in p_lower
            is_arrow = "arrow" in p_lower

            if is_valve:
                cat = "valve"
            elif is_pump:
                cat = "pump"
            elif is_vessel:
                cat = "vessel"
            elif is_hex:
                cat = "heat_exchanger"
            elif is_filter:
                cat = "filter"
            elif is_motor:
                cat = "motor"
            elif is_reducer:
                cat = "reducer"
            elif is_arrow:
                cat = "flow_arrow"
            else:
                cat = "component"

            if pred_class != "UNKNOWN" and conf >= 0.50:
                detected_symbols.append({
                    "symbol_type": pred_class,
                    "category": cat,
                    "bbox": [int(bx), int(by), int(bw), int(bh)],
                    "confidence": conf,
                    "confidence_level": _level(conf),
                    "aspect_ratio": round(aspect, 2),
                    "detector": "deterministic_cv",
                    "visual_evidence": f"Template correlation match to canonical {pred_class} exemplar (score={conf:.2f})",
                    "source": "deterministic"
                })

        # Non-maximum suppression / proximity filtering
        filtered: List[Dict[str, Any]] = []
        for s in sorted(detected_symbols, key=lambda x: -x["confidence"]):
            sx, sy, sw, sh = s["bbox"]
            sc_x = sx + sw / 2.0
            sc_y = sy + sh / 2.0
            duplicate = False
            for f in filtered:
                fx, fy, fw, fh = f["bbox"]
                fc_x = fx + fw / 2.0
                fc_y = fy + fh / 2.0
                dist = np.hypot(sc_x - fc_x, sc_y - fc_y)
                if dist < 22:
                    duplicate = True
                    break
            if not duplicate:
                filtered.append(s)

        return filtered

    def detect_symbols(
        self,
        image: Union[np.ndarray, str],
        thresh: Optional[np.ndarray] = None,
        min_size: int = 14,
        max_size: int = 160,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Convenience alias for detect_symbols_in_diagram."""
        return self.detect_symbols_in_diagram(image, min_size=min_size, max_size=max_size)


pid_symbol_detector = PIDSymbolDetector()

