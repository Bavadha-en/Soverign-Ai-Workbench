"""
Check each reading from an inspection report against the limits in the SOP the
report cites, work out the severity from those checks, and list everything an
engineer has to look at before signing.

The limits are copied from the SOPs in the knowledge base together with the
clause each one comes from, so every verdict in the approval note points to a
numbered clause instead of to a model's judgement.
"""
import re
from typing import Any, Dict, List, Optional, Tuple

from backend.documents.inspection_extractor import UNIT_PATTERN, canonical_unit, extract_inspection_record

# Source: demo_data/knowledge_base/SOP-M-104_centrifugal_pump_maintenance.md
SOP_LIMITS: Dict[str, Dict[str, Any]] = {
    "SOP-M-104": {
        "vibration": {
            "unit": "mm/s",
            # (zone, upper bound, bound belongs to this zone, status, what the SOP says to do)
            "zones": [
                ("A", 1.8, False, "OK", "good"),
                ("B", 4.5, True, "OK", "acceptable for continuous operation"),
                ("C", 7.1, True, "WARNING", "schedule a planned overhaul within 14 days"),
                ("D", None, False, "CRITICAL", "immediate emergency shutdown and isolation"),
            ],
            "clause": "SOP-M-104 §3",
        },
        "bearing_temperature": {
            "unit": "°C",
            "max": 75.0,
            "over": "EXCEEDED",
            "meaning": "bearing temperature must not exceed 75 °C",
            "clause": "SOP-M-104 §4",
        },
        "seal_leakage": {
            "unit": "drops/min",
            "max": 5.0,
            "over": "EXCEEDED",
            "meaning": "more than 5 drops/min requires immediate seal replacement",
            "clause": "SOP-M-104 §4",
        },
        "_required": ["vibration", "bearing_temperature", "seal_leakage"],
    },
}

CONVERSIONS = {
    ("°F", "°C"): lambda v: (v - 32.0) * 5.0 / 9.0,
    ("in/s", "mm/s"): lambda v: v * 25.4,
}

STATUS_SEVERITY = {"CRITICAL": "CRITICAL", "EXCEEDED": "HIGH", "WARNING": "HIGH", "DEVIATION": "MEDIUM", "OK": "LOW"}
SEVERITY_RANK = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
STATUS_TEXT = {
    "CRITICAL": "Critical",
    "EXCEEDED": "Exceeded",
    "WARNING": "Warning",
    "DEVIATION": "Deviation",
    "OK": "Within limit",
    "NO_LIMIT": "No limit given",
    "UNKNOWN": "Cannot check",
}
RECOMMENDATION = {
    "CRITICAL": "APPROVED FOR IMMEDIATE EMERGENCY REPAIR / REPLACEMENT",
    "HIGH": "APPROVED FOR SCHEDULED COMPONENT OVERHAUL UNDER APPLICABLE SOP",
    "MEDIUM": "APPROVED WITH ROUTINE MAINTENANCE MONITORING",
    "LOW": "NO CORRECTIVE WORK REQUIRED - CONTINUE ROUTINE MONITORING",
}
KIND_LABEL = {"vibration": "vibration", "bearing_temperature": "bearing temperature", "seal_leakage": "seal leakage"}
# Units whose values are cross-checked between the findings and the measurement table
CROSS_CHECK_UNITS = {"mm/s": ("vibration",), "°C": ("bearing_temperature", "temperature"), "drops/min": ("seal_leakage",)}
LIMIT_WORDS = (
    "limit", "max", "min", "allowable", "threshold", "required", "zone", "band", "trip", "toward",
    "range", "ceiling", "exceed", "than", "beyond", "vs",
)
LOW_CONFIDENCE = 0.85


def _convert(value: float, unit: str, target: str) -> Optional[float]:
    if unit == target:
        return value
    fn = CONVERSIONS.get((unit, target))
    return fn(value) if fn else None


def _zone(value: float, zones: list) -> Tuple[str, str, str]:
    lower = None
    for zone, upper, inclusive, status, meaning in zones:
        if upper is None or value < upper or (inclusive and value == upper):
            if upper is None:
                band = f"above {lower:g}"
            elif lower is None:
                band = f"below {upper:g}"
            else:
                band = f"{lower:g}-{upper:g}"
            return zone, band, status
        lower = upper
    raise ValueError("zone table has no open upper bound")


def _zone_meaning(zone: str, zones: list) -> str:
    return next(z[4] for z in zones if z[0] == zone)


def _rule_numbers(rule: Dict[str, Any]) -> List[float]:
    if "zones" in rule:
        return [z[1] for z in rule["zones"] if z[1] is not None]
    return [rule["max"]]


def _fmt(m: Dict[str, Any]) -> str:
    return f"{m['value_text']} {m['unit']}"


def _check_measurement(m: Dict[str, Any], rules: List[Tuple[str, Dict[str, Any]]], review: List[str]) -> None:
    kind, value, unit = m["kind"], m["value"], m["unit"]
    stated = m.get("stated_status")
    found = next(((sop, r[kind]) for sop, r in rules if kind in r), None)

    if found:
        sop, rule = found
        v = _convert(value, unit, rule["unit"])
        if v is None:
            m.update(status="UNKNOWN", basis="sop", limit=f"limit is in {rule['unit']}", limit_source=rule["clause"], meaning="")
            review.append(f"{m['label_full']} is reported in {unit}, which cannot be compared with the {rule['unit']} limit in {rule['clause']}.")
        elif "zones" in rule:
            zone, band, status = _zone(v, rule["zones"])
            m.update(
                status=status, zone=zone, basis="sop", limit_source=rule["clause"],
                limit=f"Zone {zone}: {band} {rule['unit']}",
                meaning=_zone_meaning(zone, rule["zones"]),
            )
        else:
            over = v > rule["max"]
            m.update(
                status=rule["over"] if over else "OK", basis="sop", limit_source=rule["clause"],
                limit=f"max {rule['max']:g} {rule['unit']}",
                meaning=rule["meaning"] if over else "",
            )
        sop_numbers = _rule_numbers(rule)
        quoted = [q for q in m.get("stated_limit_values") or [] if not any(abs(q - s) < 1e-6 for s in sop_numbers)]
        if quoted and v is not None:
            review.append(
                f"Report line {m['line']} quotes a {m['label'].lower()} limit of "
                f"{', '.join(f'{q:g}' for q in quoted)} {unit}, but {rule['clause']} gives "
                f"{', '.join(f'{s:g}' for s in sop_numbers)} {rule['unit']}."
            )
    elif m.get("stated_range"):
        lo, hi = m["stated_range"]
        m.update(
            status="OK" if lo <= value <= hi else "DEVIATION", basis="report_range", limit_source="report",
            limit=f"{lo:g}-{hi:g} {unit} design range", meaning="",
        )
    elif m.get("stated_reference"):
        direction, ref = m["stated_reference"]
        if direction == "design":
            # A design point (e.g. BEP flow): any departure from it is a deviation.
            off = abs(value - ref) > 1e-9
            direction = "below" if value < ref else "above"
        else:
            off = value < ref if direction == "below" else value > ref
        m.update(
            status="DEVIATION" if off else "OK", basis="report_reference", limit_source="report",
            limit=f"{ref:g} {unit} design point", meaning=f"{direction} the design point" if off else "",
        )
    elif stated in STATUS_SEVERITY:
        m.update(status=stated, basis="report_statement", limit_source="report", limit="no numeric limit given", meaning="")
    else:
        m.update(status="NO_LIMIT", basis="none", limit_source=None, limit="no limit given", meaning="")

    if m["basis"] == "report_statement":
        m["agreement"] = "STATED_ONLY"
    elif not stated or m["status"] in ("UNKNOWN", "NO_LIMIT"):
        m["agreement"] = "NOT_STATED"
    elif stated == m["status"]:
        m["agreement"] = "AGREES"
    else:
        m["agreement"] = "DIFFERS"
        review.append(
            f"{m['label_full']} {_fmt(m)}: the report says {STATUS_TEXT[stated].lower()}, "
            f"but the check against {m['limit_source']} gives {STATUS_TEXT[m['status']].lower()}."
        )

    if m.get("confidence") is not None and m["confidence"] < LOW_CONFIDENCE:
        review.append(
            f"{m['label_full']} was read from the scan with low confidence ({m['confidence']:.2f}): "
            f"\"{m['source_text']}\". Check the value against the page."
        )


def _cross_check_findings(record: Dict[str, Any], review: List[str]) -> None:
    """Flag a value in the findings that disagrees with the measurement table (often an OCR misread)."""
    table: Dict[str, List[float]] = {}
    for m in record["measurements"]:
        table.setdefault(m["kind"], []).append(m["value"])
    value_re = re.compile(rf"(?<![\d.])(\d+(?:\.\d+)?)\s*({UNIT_PATTERN})", re.I)
    for item in record["findings"]:
        text = item["text"]
        for match in value_re.finditer(text):
            unit = canonical_unit(match.group(2))
            kinds = CROSS_CHECK_UNITS.get(unit)
            if not kinds:
                continue
            before = text[max(0, match.start() - 25):match.start()].lower()
            if re.search(r"(<=|>=|<|>|≤|≥|-)\s*$", before) or any(w in before for w in LIMIT_WORDS):
                continue
            known = [v for k in kinds for v in table.get(k, [])]
            value = float(match.group(1))
            if known and not any(abs(value - k) < 0.05 for k in known):
                review.append(
                    f"Findings line {item['line']} gives {match.group(1)} {unit}, but the measurement table has "
                    f"{', '.join(f'{k:g}' for k in known)} {unit}. Check the report."
                )


def _severity(measurements: List[Dict[str, Any]]) -> Tuple[Optional[str], str, List[Dict[str, Any]]]:
    ranked = [(SEVERITY_RANK[STATUS_SEVERITY[m["status"]]], m) for m in measurements if m["status"] in STATUS_SEVERITY]
    if not ranked:
        return None, "No reading could be checked against a limit.", []
    top = max(r for r, _ in ranked)
    severity = next(k for k, v in SEVERITY_RANK.items() if v == top)
    if severity == "LOW":
        return severity, "All checked readings are within their limits.", []
    drivers = [m for r, m in ranked if r == top]
    reasons = []
    for m in drivers:
        why = f"{m['label_full']} {_fmt(m)} is {STATUS_TEXT[m['status']].lower()} ({m['limit']}, {m['limit_source']})"
        if m.get("meaning"):
            why += f": {m['meaning']}"
        reasons.append(why)
    return severity, "; ".join(reasons) + ".", drivers


def _summary(a: Dict[str, Any]) -> str:
    tag = (a.get("equipment_tag") or {}).get("value") or "The equipment"
    name = (a.get("equipment_name") or {}).get("value")
    date = (a.get("inspection_date") or {}).get("value")
    report_no = (a.get("report_no") or {}).get("value")
    head = tag + (f" ({name})" if name else "")
    head += f" was inspected on {date}" if date else " was inspected"
    head += f" (report {report_no})." if report_no else "."
    parts = [head]

    ms = a["measurements"]
    breaches = [m for m in ms if m["status"] in ("CRITICAL", "EXCEEDED", "WARNING", "DEVIATION")]
    if breaches:
        listed = "; ".join(f"{m['label_full']} {_fmt(m)} ({STATUS_TEXT[m['status']].lower()}, {m['limit']})" for m in breaches)
        parts.append(f"{len(breaches)} of {len(ms)} readings are outside their limits: {listed}.")
    elif ms:
        parts.append(f"All {len(ms)} readings are within their limits.")
    sev = a["severity"]
    if sev["value"]:
        parts.append(f"Severity {sev['value']}, set by the checks: {sev['basis']}")
    if a["review_items"]:
        n = len(a["review_items"])
        parts.append(f"{n} item{'s' if n != 1 else ''} need{'s' if n == 1 else ''} an engineer's check before sign-off.")
    return " ".join(parts)


def assess_record(record: Dict[str, Any]) -> Dict[str, Any]:
    a = dict(record)
    a["measurements"] = [dict(m) for m in record["measurements"]]
    review: List[str] = []
    ocr = record.get("text_source") == "ocr"
    a["applicable"] = bool(a["measurements"]) or ((a.get("equipment_tag") or {}).get("method") == "field")

    if record.get("text_source") == "none":
        review.append("No text could be read from the document. Check the scan quality and upload it again.")
    if a["applicable"] and not record.get("inspection_date"):
        review.append("The report does not state an inspection date.")

    rules = [(sop, SOP_LIMITS[sop]) for sop in record.get("sop_refs", []) if sop in SOP_LIMITS]
    a["limits_applied"] = [sop for sop, _ in rules]
    if a["applicable"] and not rules:
        review.append("The report cites no SOP with configured limits, so readings were checked only against limits quoted in the report.")

    for m in a["measurements"]:
        _check_measurement(m, rules, review)

    for sop, r in rules:
        for kind in r.get("_required", []):
            if not any(m["kind"] == kind for m in a["measurements"]):
                where = " The scan may be hard to read here; check it by eye." if ocr else ""
                review.append(f"{sop} calls for a {KIND_LABEL.get(kind, kind)} reading, but none was found in the report.{where}")

    for line in record.get("unparsed_measurement_lines", []):
        review.append(f"Could not read a value from measurement line {line['line']}: \"{line['text']}\".")

    _cross_check_findings(a, review)

    for rec in a.get("recommendations", []):
        if rec.get("confidence") is not None and rec["confidence"] < LOW_CONFIDENCE:
            review.append(f"Recommendation on line {rec['line']} was read with low confidence ({rec['confidence']:.2f}): \"{rec['text']}\".")

    severity, basis, drivers = _severity(a["measurements"])
    stated = (record.get("stated_severity") or {}).get("value")
    a["severity"] = {
        "value": severity,
        "basis": basis,
        "drivers": [m["label_full"] for m in drivers],
        "stated": stated,
        "agrees": (stated == severity) if (stated and severity) else None,
    }
    if stated and severity and stated != severity:
        review.append(f"The report rates severity {stated}; the checks give {severity}. An engineer must decide which applies.")
    if a["applicable"] and severity is None:
        review.append("Severity could not be set because no reading could be checked against a limit.")

    a["review_items"] = list(dict.fromkeys(review))
    a["recommendation"] = RECOMMENDATION.get(severity) if severity else "NO RECOMMENDATION - ENGINEER TO ASSESS"
    a["summary"] = _summary(a) if a["applicable"] else ""
    return a


def assess_text(
    text: str,
    lines: Optional[List[Dict[str, Any]]] = None,
    text_source: str = "text_layer",
    pages_data: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    record = extract_inspection_record(text, lines=lines, text_source=text_source, pages_data=pages_data)
    return assess_record(record)


def assess_document(path: str) -> Dict[str, Any]:
    from backend.documents.reader import read_document

    doc = read_document(path)
    a = assess_text(doc["text"], lines=doc.get("lines"), text_source=doc["text_source"], pages_data=doc.get("pages_data"))
    a["file"] = path
    a["text"] = doc["text"]
    return a
