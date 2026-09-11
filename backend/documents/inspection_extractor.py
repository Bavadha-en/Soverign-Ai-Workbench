"""
Read the fields an approval note needs out of an inspection report's text.

Works line by line on text from a PDF text layer or from OCR, and keeps the
line each value came from, so every figure in the approval note can be traced
back to the report. Handles two layouts seen in practice: narrative lines
("Bearing Temperature: 88.0 deg C (HIGH: ...)") and tables that a PDF text
layer emits one cell per line. The parsing is deterministic: no language model
touches the numbers.
"""
import re
from typing import Any, Dict, List, Optional, Set, Tuple

UNIT_PATTERN = (
    r"mm/s|in/s|deg\s*C|degC|°\s*C|º\s*C|℃|deg\s*F|°\s*F|drops\s*/\s*min(?:ute)?s?|ml\s*/\s*h|"
    r"MPa|kPa|bar|psi|m3\s*/\s*h|m³\s*/\s*h|meters|metres|kW|rpm|mm(?![/a-z])|m(?![a-z/²³])|%"
)

_UNITS = {
    "degc": "°C", "°c": "°C", "degf": "°F", "°f": "°F", "m3/h": "m³/h", "m³/h": "m³/h",
    "meters": "m", "metres": "m", "m": "m", "mpa": "MPa", "kpa": "kPa", "kw": "kW",
    "rpm": "rpm", "ml/h": "ml/h", "mm/s": "mm/s", "in/s": "in/s", "bar": "bar",
    "psi": "psi", "mm": "mm", "%": "%",
}


def canonical_unit(raw: str) -> str:
    u = re.sub(r"\s+", "", raw or "").lower().replace("º", "°").replace("℃", "°c")
    if u.startswith("drops/min"):
        return "drops/min"
    return _UNITS.get(u, (raw or "").strip())


_HEAD = r"^[\s\-•*]*(?P<label>[A-Za-z][A-Za-z /&\-]*?)\s*(?:\((?P<loc>[^():]*)\)?\s*)?"
_TAIL = rf"(?P<value>[-+]?\d+(?:[.,]\d+)?)\s*(?P<unit>{UNIT_PATTERN})(?P<rest>.*)$"
# "- Vibration (Outboard Bearing RMS): 7.4 mm/s (CRITICAL: ... > 7.1 mm/s)".
# OCR can drop the closing bracket or the spaces, so both are optional.
MEASUREMENT_RE = re.compile(_HEAD + r"[:;]\s*" + _TAIL, re.I)
# Inside a measurements section OCR also drops the colon ("Discharge Pressure 1.85MPa").
MEASUREMENT_LOOSE_RE = re.compile(_HEAD + r"(?:[:;]\s*)?" + _TAIL, re.I)

VALUE_CELL_RE = re.compile(rf"^\s*(?P<value>[-+]?\d+(?:[.,]\d+)?)\s*(?P<unit>{UNIT_PATTERN})\s*$", re.I)
TABLE_HEADER_RE = re.compile(r"^\s*parameters?\s*$", re.I)
COLUMN_ROLES = [
    ("value", ("measured", "value", "reading")),
    ("limit", ("threshold", "limit", "design", "allowable", "range")),
    ("status", ("status", "condition", "result", "remark")),
]

def _loose(phrase: str) -> str:
    """A label pattern that tolerates OCR spaces inside words ("INSPEC TION") and missing ones between them."""
    return r"\s*".join(r"\s?".join(re.escape(c) for c in word) for word in phrase.split())


FIELD_PATTERNS = {
    "report_no": re.compile(_loose("REPORT NO") + r"\.?\s*[:.]?\s*([A-Z0-9][A-Z0-9\-/]{3,})", re.I),
    "inspection_date": re.compile(
        _loose("DATE OF INSPECTION") + r"\s*[:.]?\s*(\d{4}-\d{2}-\d{2}|\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4})", re.I
    ),
    "equipment_tag": re.compile(_loose("Equipment Tag") + r"\s*[:.]?\s*([A-Z]{1,4}\s?-\s?\d{2,5}[A-Z]?)", re.I),
    "equipment_name": re.compile(_loose("Equipment Description") + r"\s*[:.]?\s*(.+)", re.I),
    "governing_specs": re.compile(_loose("Governing Specification") + r"s?\s*[:.]?\s*(.+)", re.I),
    "stated_severity": re.compile(
        r"(?:" + _loose("Overall") + r"\s*)?" + _loose("Risk Severity")
        + r"(?:\s*" + _loose("Assessment") + r")?\s*[:.]?\s*([A-Za-z]+)", re.I
    ),
}
INSPECTOR_RE = re.compile(r"^\s*" + _loose("Lead Inspector") + r"\s*[:.]?\s*(.+)", re.I)
SIGNOFF_RE = re.compile(
    r"^\s*(?:" + _loose("Lead Inspector") + r"|" + _loose("Inspector") + r"\s*[:.]|" + _loose("Signature") + r")", re.I
)
SOP_RE = re.compile(r"SOP\s*[-.\s]?\s*([A-Z]{1,4})\s*[-.\s]?\s*(\d{2,4})", re.I)
FALLBACK_TAG_RE = re.compile(r"\b([A-Z]{1,3})-(\d{2,4})\b")

SECTIONS = [
    ("measurements", ("MEASUREMENT", "TELEMETRY", "READINGS")),
    ("findings", ("FINDING", "EXAMINATION", "OBSERVATION")),
    ("risk", ("RISKSEVERITY", "RISKCLASS", "SEVERITY")),
    ("recommendations", ("RECOMMENDATION", "CORRECTIVE")),
    ("equipment", ("IDENTIFICATION",)),
]
NUMBERED_HEADING_RE = re.compile(r"^\s*\d{1,2}\s*[.,)]?\s*[A-Z]")

SEVERITIES = {"CRITICAL": "CRITICAL", "HIGH": "HIGH", "MEDIUM": "MEDIUM", "MODERATE": "MEDIUM", "LOW": "LOW", "NORMAL": "LOW"}


def _clean(text: str) -> str:
    t = re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", " ", text or "")
    t = t.replace("·", "-").replace("：", ":").replace("–", "-").replace("—", "-")
    return re.sub(r"\s+", " ", t).strip()


def _tidy(text: str) -> str:
    """Put back spaces OCR removed between words ("DifferentialHead")."""
    return re.sub(r"\s+", " ", re.sub(r"(?<=[a-z])(?=[A-Z])", " ", text or "")).strip()


def _section_of(text: str) -> Optional[str]:
    """Numbered upper-case headings ("2. OPERATIONAL MEASUREMENTS") or short titles ending in a colon."""
    letters = [c for c in text if c.isalpha()]
    numbered = bool(
        NUMBERED_HEADING_RE.match(text) and letters and sum(c.isupper() for c in letters) / len(letters) >= 0.8
    )
    titled = text.endswith(":") and len(text) <= 60
    if not (numbered or titled):
        return None
    squashed = re.sub(r"[^A-Z]", "", text.upper())
    for name, keys in SECTIONS:
        if any(k in squashed for k in keys):
            return name
    return "other" if numbered else None


def _status_word(text: str) -> Optional[str]:
    s = (text or "").lower()
    if "critical" in s or "trip" in s:
        return "CRITICAL"
    if "exceed" in s or re.match(r"\s*high\b", s) or "over limit" in s:
        return "EXCEEDED"
    if "warning" in s or "alert" in s:
        return "WARNING"
    if re.search(r"\b(below|under|above|over)\b|\breduc|\bslight|\bdrop(?!s?\s*/)", s):
        return "DEVIATION"
    if any(w in s for w in ("normal", "acceptable", "within", "good")):
        return "OK"
    return None


def _kind(label: str, location: Optional[str]) -> str:
    s = f"{label} {location or ''}".lower().replace(" ", "")
    if "vibration" in s:
        return "vibration"
    if "temp" in s:
        return "bearing_temperature" if "bearing" in s else "temperature"
    if any(w in s for w in ("leak", "weep", "seep")):
        return "seal_leakage"
    if "pressure" in s:
        if "suction" in s:
            return "suction_pressure"
        if "discharge" in s:
            return "discharge_pressure"
        return "pressure"
    if "flow" in s:
        return "flow_rate"
    if "head" in s:
        return "differential_head"
    return re.sub(r"[^a-z]+", "_", label.lower()).strip("_") or "value"


def _parse_note(rest: str, unit: str) -> Tuple[Optional[str], List[float], Optional[Tuple[float, float]], Optional[Tuple[str, float]]]:
    """
    Read the inspector's note on a reading, e.g. "(HIGH: SOP-M-104 max allowable
    is 75.0 deg C)" or "(Design normal 80 - 85 m3/h)". Returns the stated status,
    limit values quoted in the reading's unit, a stated range, and a reference
    point ("below 50.0", or a design point such as a BEP flow).
    """
    text = (rest or "").strip().lstrip("(").rstrip(")").strip()
    head = re.match(r"([A-Za-z][A-Za-z ]*?)\s*[:.]", text)
    stated = (_status_word(head.group(1)) if head else None) or _status_word(text)

    limits: List[float] = []
    rng = None
    for lo, hi, u in re.findall(rf"(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*({UNIT_PATTERN})", text, re.I):
        if canonical_unit(u) == unit:
            rng = (float(lo), float(hi))
            limits += [float(lo), float(hi)]
    for v, u in re.findall(rf"(?<![\d.\-])(\d+(?:\.\d+)?)\s*({UNIT_PATTERN})", text, re.I):
        if canonical_unit(u) == unit:
            limits.append(float(v))
    limits = sorted(set(limits))

    ref = None
    r = re.search(r"\b(below|under|above|over)\s*(\d+(?:\.\d+)?)", text, re.I)
    if r:
        ref = ("below" if r.group(1).lower() in ("below", "under") else "above", float(r.group(2)))
    elif len(limits) == 1 and not rng and re.search(r"\b(bep|best\s*efficiency|design\s*point|rated|nominal)\b", text, re.I):
        ref = ("design", limits[0])
    return stated, limits, rng, ref


def _rows(text: str, lines: Optional[List[Dict[str, Any]]], pages_data: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if lines:
        counters: Dict[int, int] = {}
        for l in lines:
            t = _clean(l.get("text", ""))
            if not t:
                continue
            page = l.get("page", 1)
            counters[page] = counters.get(page, 0) + 1
            rows.append({"no": counters[page], "page": page, "text": t, "confidence": l.get("confidence")})
        return rows
    for p in pages_data or [{"page": 1, "text": text or ""}]:
        n = 0
        for raw in (p.get("text") or "").split("\n"):
            t = _clean(raw)
            if not t:
                continue
            n += 1
            rows.append({"no": n, "page": p.get("page", 1), "text": t, "confidence": None})
    return rows


def _field(value: str, row: Dict[str, Any], method: str = "field") -> Dict[str, Any]:
    return {
        "value": value,
        "line": row["no"],
        "page": row["page"],
        "text": row["text"],
        "confidence": row["confidence"],
        "method": method,
    }


def _normalise_field(key: str, value: str) -> str:
    value = value.strip()
    if key == "equipment_tag":
        return re.sub(r"\s+", "", value).upper()
    if key == "stated_severity":
        return SEVERITIES.get(value.upper(), value.upper())
    return _tidy(value)


def _add_item(items: List[Dict[str, Any]], row: Dict[str, Any], text_source: str) -> None:
    text = row["text"].lstrip("-•* ").strip()
    if not text:
        return
    # A text layer wraps long sentences; a line starting in lower case continues the previous item.
    if items and text_source != "ocr" and text[0].islower():
        items[-1]["text"] = f"{items[-1]['text']} {text}"
        return
    items.append({"text": text, "line": row["no"], "page": row["page"], "confidence": row["confidence"]})


def _measurement(label: str, location: Optional[str], value_text: str, unit_raw: str, note: str,
                 row: Dict[str, Any], source_text: str, confidence: Optional[float]) -> Dict[str, Any]:
    unit = canonical_unit(unit_raw)
    value_text = value_text.replace(",", ".")
    label = _tidy(label)
    location = _tidy(location or "") or None
    stated, limits, rng, ref = _parse_note(note, unit)
    return {
        "kind": _kind(label, location),
        "label": label,
        "location": location,
        "label_full": f"{label} ({location})" if location else label,
        "value": float(value_text),
        "value_text": value_text,
        "unit": unit,
        "stated_status": stated,
        "stated_limit_values": limits,
        "stated_range": list(rng) if rng else None,
        "stated_reference": list(ref) if ref else None,
        "line": row["no"],
        "page": row["page"],
        "confidence": confidence,
        "source_text": source_text,
    }


def _parse_tables(rows: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Set[int]]:
    """
    Tables a PDF text layer emits one cell per line: a "Parameter" header, the
    other header cells, then one line per cell for each reading.
    """
    measurements: List[Dict[str, Any]] = []
    consumed: Set[int] = set()
    i = 0
    while i < len(rows):
        if not TABLE_HEADER_RE.match(rows[i]["text"]):
            i += 1
            continue
        header = [rows[i]["text"]]
        j = i + 1
        # Header cells run until the first cell that is followed by a value cell.
        while j + 1 < len(rows) and not VALUE_CELL_RE.match(rows[j + 1]["text"]) and len(header) < 8:
            header.append(rows[j]["text"])
            j += 1
        roles = {"label": 0}
        for col, name in enumerate(header[1:], start=1):
            low = name.lower()
            for role, words in COLUMN_ROLES:
                if role not in roles and any(w in low for w in words):
                    roles[role] = col
                    break
        ncols = len(header)
        if "value" not in roles or ncols < 2:
            i += 1
            continue

        k = j
        while k + ncols <= len(rows):
            cells = rows[k:k + ncols]
            vm = VALUE_CELL_RE.match(cells[roles["value"]]["text"])
            if not vm:
                break
            name = cells[0]["text"]
            nm = re.match(r"^(?P<label>[^()]+?)\s*(?:\((?P<loc>[^)]*)\))?\s*$", name)
            status_text = cells[roles["status"]]["text"] if "status" in roles else ""
            limit_text = cells[roles["limit"]]["text"] if "limit" in roles else ""
            note = f"({status_text}: {limit_text})" if status_text else f"({limit_text})"
            confidences = [c["confidence"] for c in cells if c["confidence"] is not None]
            measurements.append(_measurement(
                nm.group("label") if nm else name,
                nm.group("loc") if nm else None,
                vm.group("value"), vm.group("unit"), note,
                cells[roles["value"]],
                " | ".join(c["text"] for c in cells),
                min(confidences) if confidences else None,
            ))
            consumed.update(range(k, k + ncols))
            k += ncols
        consumed.update(range(i, j))
        i = max(k, i + 1)
    return measurements, consumed


def extract_inspection_record(
    text: str,
    lines: Optional[List[Dict[str, Any]]] = None,
    text_source: str = "text_layer",
    pages_data: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    rows = _rows(text, lines, pages_data)
    record: Dict[str, Any] = {key: None for key in FIELD_PATTERNS}
    record.update({
        "inspector": None,
        "text_source": text_source,
        "sop_refs": [],
        "measurements": [],
        "findings": [],
        "recommendations": [],
        "unparsed_measurement_lines": [],
        "sections_found": [],
    })

    for row in rows:
        for m in SOP_RE.finditer(row["text"]):
            ref = f"SOP-{m.group(1).upper()}-{m.group(2)}"
            if ref not in record["sop_refs"]:
                record["sop_refs"].append(ref)

    table_measurements, consumed = _parse_tables(rows)
    record["measurements"].extend(table_measurements)

    candidates = []
    section = None
    for idx, row in enumerate(rows):
        if idx in consumed:
            continue
        t = row["text"]

        sec = _section_of(t)
        if sec:
            section = sec
            record["sections_found"].append(sec)
            continue

        if SIGNOFF_RE.match(t):
            insp = INSPECTOR_RE.match(t)
            if insp and record["inspector"] is None:
                record["inspector"] = _field(_tidy(insp.group(1)), row)
            section = "signoff"
            continue

        matched_field = False
        for key, pat in FIELD_PATTERNS.items():
            if record[key] is None:
                m = pat.search(t)
                if m:
                    record[key] = _field(_normalise_field(key, m.group(1)), row)
                    matched_field = True
        if matched_field:
            continue

        if section == "findings":
            _add_item(record["findings"], row, text_source)
        elif section == "recommendations":
            _add_item(record["recommendations"], row, text_source)
        elif section != "signoff":
            candidates.append((section, row))

    in_section = "measurements" in record["sections_found"]
    for section, row in candidates:
        if in_section and section != "measurements":
            continue
        pattern = MEASUREMENT_LOOSE_RE if section == "measurements" else MEASUREMENT_RE
        m = pattern.match(row["text"])
        if not m:
            if in_section and re.search(r"\d", row["text"]) and re.search(UNIT_PATTERN, row["text"], re.I):
                record["unparsed_measurement_lines"].append({"line": row["no"], "page": row["page"], "text": row["text"]})
            continue
        record["measurements"].append(_measurement(
            m.group("label"), m.group("loc"), m.group("value"), m.group("unit"), m.group("rest"),
            row, row["text"], row["confidence"],
        ))

    if record["equipment_tag"] is None:
        for row in rows[:20]:
            for m in FALLBACK_TAG_RE.finditer(row["text"]):
                if m.group(1) not in ("IR", "SOP", "ISO", "API"):
                    record["equipment_tag"] = _field(f"{m.group(1)}-{m.group(2)}", row, "pattern")
                    break
            if record["equipment_tag"]:
                break

    return record
