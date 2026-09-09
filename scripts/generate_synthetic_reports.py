import os
import json
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random

insp_dir = "demo_data/inspection"
os.makedirs(insp_dir, exist_ok=True)

# ----------------- Ground Truth P-101 -----------------
gt_p101 = {
    "equipment": "P-101",
    "equipment_name": "Primary Hydrocarbon Feed Centrifugal Pump",
    "inspection_date": "2026-08-14",
    "inspector": "Lead Inspector K. Vance, Senior Rotating Equipment Specialist",
    "operating_condition": "Continuous Feed Service (1450 RPM, 415V Drive)",
    "measurements": [
        {"parameter": "Vibration RMS", "value": 7.4, "unit": "mm/s", "threshold": "<= 4.5 mm/s (Zone D > 7.1 mm/s)", "status": "EXCEEDED"},
        {"parameter": "Bearing Temperature", "value": 88.0, "unit": "deg C", "threshold": "<= 75.0 deg C", "status": "EXCEEDED"},
        {"parameter": "Mechanical Seal Leakage", "value": 14, "unit": "drops/min", "threshold": "<= 5 drops/min", "status": "EXCEEDED"},
        {"parameter": "Suction Pressure", "value": 0.32, "unit": "MPa", "threshold": "0.30 - 0.40 MPa", "status": "NORMAL"},
        {"parameter": "Discharge Pressure", "value": 1.85, "unit": "MPa", "threshold": "1.80 - 2.10 MPa", "status": "NORMAL"},
        {"parameter": "Flow Rate", "value": 48.5, "unit": "m3/h", "threshold": "50.0 m3/h BEP", "status": "SLIGHT DROP"}
    ],
    "findings": [
        "Excessive triaxial vibration of 7.4 mm/s RMS on outboard bearing housing exceeding ISO 10816-3 Zone D critical trip limit (7.1 mm/s).",
        "Bearing operating temperature measured at 88 deg C exceeding maximum allowable threshold of 75 deg C per SOP-M-104.",
        "Dynamic mechanical cartridge seal weeping 14 drops/minute exceeding allowable leakage limit of 5 drops/minute.",
        "Localized pitting corrosion and cavitation erosion detected on impeller suction eye (depth: 1.2 mm)."
    ],
    "severity": "CRITICAL",
    "governing_sops": ["SOP-M-104", "SOP-SAF-001"],
    "recommendations": [
        "Immediate emergency shutdown and electrical Lockout/Tagout (LOTO) per SOP-SAF-001.",
        "Replace mechanical cartridge seal assembly.",
        "Replace drive-end and non-drive-end ball and thrust bearings.",
        "Laser align pump and motor shaft with angular offset <= 0.05 mm.",
        "Execute casing hydrostatic proof test at 1.5x MAWP for 15 minutes before recommissioning."
    ]
}

with open(os.path.join(insp_dir, "ground_truth.json"), "w", encoding="utf-8") as f:
    json.dump(gt_p101, f, indent=2)
with open(os.path.join(insp_dir, "ground_truth_P101.json"), "w", encoding="utf-8") as f:
    json.dump(gt_p101, f, indent=2)

# ----------------- Ground Truth P-202 -----------------
gt_p202 = {
    "equipment": "P-202",
    "equipment_name": "Boiler Feed Water Secondary Booster Pump",
    "inspection_date": "2026-08-22",
    "inspector": "Reliability Engineer M. S. Thorne",
    "operating_condition": "Intermittent Standby Service (2950 RPM, 3.3kV Drive)",
    "measurements": [
        {"parameter": "Vibration RMS", "value": 5.1, "unit": "mm/s", "threshold": "<= 4.5 mm/s (Zone C 4.5-7.1 mm/s)", "status": "WARNING"},
        {"parameter": "Bearing Temperature", "value": 71.0, "unit": "deg C", "threshold": "<= 75.0 deg C", "status": "NORMAL"},
        {"parameter": "Mechanical Seal Leakage", "value": 2, "unit": "drops/min", "threshold": "<= 5 drops/min", "status": "NORMAL"},
        {"parameter": "Suction Pressure", "value": 0.85, "unit": "MPa", "threshold": "0.80 - 0.90 MPa", "status": "NORMAL"},
        {"parameter": "Discharge Pressure", "value": 4.20, "unit": "MPa", "threshold": "4.10 - 4.30 MPa", "status": "NORMAL"},
        {"parameter": "Flow Rate", "value": 82.0, "unit": "m3/h", "threshold": "80.0 - 85.0 m3/h", "status": "NORMAL"}
    ],
    "findings": [
        "Elevated vibration of 5.1 mm/s RMS on drive-end bearing housing falling in ISO 10816-3 Zone C warning band (4.5 - 7.1 mm/s).",
        "Bearing temperature stable at 71 deg C within normal thermal operating window (< 75 deg C).",
        "Plan 53A dual mechanical seal leakage observed at 2 drops/minute within allowable limit (< 5 drops/minute).",
        "External casing exhibits superficial uniform atmospheric oxidation with zero internal wall thinning."
    ],
    "severity": "HIGH",
    "governing_sops": ["SOP-M-104"],
    "recommendations": [
        "Schedule planned overhaul within 14 days per SOP-M-104 Section 3.",
        "Inspect motor-pump flexible coupling elastomeric insert for torsional backlash.",
        "Replenish bearing grease with ISO VG 46 synthetic lubricant.",
        "Increase vibration condition monitoring to daily intervals until overhaul window."
    ]
}

with open(os.path.join(insp_dir, "ground_truth_P202.json"), "w", encoding="utf-8") as f:
    json.dump(gt_p202, f, indent=2)

# ----------------- Generate Clean Text Reports -----------------
txt_p101 = """SOVEREIGN INDUSTRIAL PLANT INTEGRITY MANAGEMENT
EQUIPMENT INSPECTION REPORT — ROTATING MACHINERY
REPORT NO: IR-2026-P101-0814
DATE OF INSPECTION: 2026-08-14
INSPECTION TYPE: Scheduled In-Service Reliability Audit

1. EQUIPMENT IDENTIFICATION
Equipment Tag: P-101
Equipment Description: Primary Hydrocarbon Feed Centrifugal Pump
Service: Hydrocarbon Liquid Transfer (Specific Gravity: 0.82)
Drive Unit: 415V 3-Phase Induction Motor (45 kW, 1450 RPM)
Governing Specifications: ISO 10816-3 Class II / API 610 / SOP-M-104

2. OPERATIONAL MEASUREMENTS & SENSOR TELEMETRY
- Vibration (Outboard Bearing RMS): 7.4 mm/s (CRITICAL: ISO 10816-3 Zone D trip limit is > 7.1 mm/s)
- Vibration (Drive End Bearing RMS): 4.8 mm/s (WARNING: Zone C range 4.5 - 7.1 mm/s)
- Bearing Temperature: 88.0 deg C (HIGH: SOP-M-104 max allowable is 75.0 deg C)
- Mechanical Seal Dynamic Leakage: 14 drops/minute (EXCEEDED: SOP-M-104 limit is <= 5 drops/min)
- Suction Pressure: 0.32 MPa (Normal operational baseline)
- Discharge Pressure: 1.85 MPa (Normal operational baseline)
- Flow Rate: 48.5 m3/h (Operating below 50.0 m3/h design Best Efficiency Point)
- Differential Head: 62.5 meters

3. PHYSICAL & NON-DESTRUCTIVE EXAMINATION FINDINGS
- Visual inspection of cartridge mechanical seal reveals significant carbon dusting and liquid droplet accumulation around gland plate.
- Dynamic weeping rate recorded at 14 drops/minute indicates failure of primary silicon carbide seal face.
- Outboard bearing exhibits audible high-pitched whining and bearing cap temperature of 88.0 deg C.
- Internal inspection via suction flange port indicates localized pitting corrosion and cavitation erosion on impeller eye with depth measuring 1.2 mm.
- Casing exterior shows moderate atmospheric oxidation; ultrasonic thickness scan of volute confirms adequate wall thickness (18.2 mm vs required 14.5 mm).

4. RISK SEVERITY & RISK CLASSIFICATION
Overall Risk Severity: CRITICAL
Risk Justification: Vibration level of 7.4 mm/s exceeds ISO 10816-3 Zone D shutdown limit (> 7.1 mm/s), combined with seal failure and bearing overheating at 88.0 deg C, presenting imminent risk of catastrophic shaft seizure or flammable product leakage.

5. INSPECTOR RECOMMENDATIONS & CORRECTIVE ACTIONS
- IMMEDIATELY initiate emergency operational shutdown and implement Lockout/Tagout (LOTO) per SOP-SAF-001.
- Decouple pump from motor; inspect flexible coupling elements for angular/radial misalignment.
- Remove and dismantle mechanical cartridge seal; replace with new API 682 certified Silicon Carbide seal cartridge.
- Replace drive-end and outboard non-drive-end ball and cylindrical roller bearings.
- Conduct precision dual-laser alignment achieving angular offset <= 0.05 mm and radial offset <= 0.05 mm.
- Perform hydrostatic pressure test at 1.5x MAWP for 15 minutes before unit recommissioning per SOP-M-104.

Lead Inspector: K. Vance, Senior Rotating Equipment Specialist
Signature: [Verified / Stamped: Plant Reliability Directorate]
"""

with open(os.path.join(insp_dir, "inspection_report_P101_clean.txt"), "w", encoding="utf-8") as f:
    f.write(txt_p101.strip() + "\n")

txt_p202 = """SOVEREIGN INDUSTRIAL PLANT INTEGRITY MANAGEMENT
EQUIPMENT INSPECTION REPORT — ROTATING MACHINERY
REPORT NO: IR-2026-P202-0822
DATE OF INSPECTION: 2026-08-22
INSPECTION TYPE: Routine In-Service Reliability Audit

1. EQUIPMENT IDENTIFICATION
Equipment Tag: P-202
Equipment Description: Boiler Feed Water Secondary Booster Pump
Service: Demineralized Boiler Feed Water (Density: 998 kg/m3)
Drive Unit: 3.3kV High-Voltage Induction Motor (110 kW, 2950 RPM)
Governing Specifications: ISO 10816-3 Class II / SOP-M-104

2. OPERATIONAL MEASUREMENTS & SENSOR TELEMETRY
- Vibration (Drive End Bearing RMS): 5.1 mm/s (WARNING: ISO 10816-3 Zone C band 4.5 - 7.1 mm/s)
- Vibration (Outboard Bearing RMS): 3.2 mm/s (NORMAL: Zone B band 1.8 - 4.5 mm/s)
- Bearing Temperature: 71.0 deg C (NORMAL: SOP-M-104 threshold <= 75.0 deg C)
- Mechanical Seal Dynamic Leakage: 2 drops/minute (NORMAL: SOP-M-104 threshold <= 5 drops/min)
- Suction Pressure: 0.85 MPa (Design normal)
- Discharge Pressure: 4.20 MPa (Design normal)
- Flow Rate: 82.0 m3/h (Design normal 80 - 85 m3/h)
- Differential Head: 115.0 meters

3. PHYSICAL & NON-DESTRUCTIVE EXAMINATION FINDINGS
- Plan 53A dual mechanical seal barrier fluid reservoir is pressurized and stable. Seepage rate is minor (2 drops/min).
- Drive-end bearing temperature is stable at 71.0 deg C. Vibration spectrum exhibits elevated 1X rotational unbalance peak at 5.1 mm/s.
- Pump volute and suction pipe show uniform external surface oxidation with zero localized pitting.
- Ultrasonic thickness survey confirms casing wall thickness of 26.4 mm (well above 19.8 mm required minimum).

4. RISK SEVERITY & RISK CLASSIFICATION
Overall Risk Severity: HIGH (PLANNED OVERHAUL REQUIRED)
Risk Justification: Vibration falls into Zone C (4.5 - 7.1 mm/s), indicating mechanical unbalance or coupling wear. Equipment does not require emergency trip but necessitates overhaul within 14 days per SOP-M-104.

5. INSPECTOR RECOMMENDATIONS & CORRECTIVE ACTIONS
- Schedule planned maintenance overhaul within 14 days per SOP-M-104 Section 3.
- Inspect motor-pump flexible coupling elastomeric insert for wear and backlash.
- Re-lubricate bearing cavities with ISO VG 46 synthetic grease.
- Monitor triaxial vibration daily to ensure levels do not escalate toward Zone D (> 7.1 mm/s).

Lead Inspector: M. S. Thorne, Plant Reliability Engineer
Signature: [Verified / Stamped: Plant Reliability Directorate]
"""

with open(os.path.join(insp_dir, "inspection_report_P202_clean.txt"), "w", encoding="utf-8") as f:
    f.write(txt_p202.strip() + "\n")

# ----------------- Generate Clean PDF Reports -----------------
def create_pdf(filename, title, data_rows, findings_text, recommendations_text, severity_badge):
    doc = SimpleDocTemplate(filename, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=15, leading=19, textColor=colors.HexColor('#1F4E78'))
    story.append(Paragraph(title, title_style))
    story.append(Paragraph('<b>ConfigIQ Sovereign AI Workbench — Equipment Integrity Inspection</b>', styles['Normal']))
    story.append(Spacer(1, 10))

    t_data = [['Parameter', 'Measured Value', 'Design / SOP Threshold', 'Condition Status']]
    t_data.extend(data_rows)
    t = Table(t_data, colWidths=[150, 100, 150, 120])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1F4E78')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9),
        ('BOTTOMPADDING', (0,0), (-1,0), 5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('ALIGN', (1,1), (-1,-1), 'CENTER'),
        ('FONTSIZE', (0,1), (-1,-1), 8),
    ]))
    story.append(t)
    story.append(Spacer(1, 12))

    story.append(Paragraph('<b>Key Technical Findings:</b>', styles['Heading3']))
    for f in findings_text:
        story.append(Paragraph(f'&bull; {f}', styles['Normal']))
    story.append(Spacer(1, 8))

    story.append(Paragraph(f'<b>Risk Severity Assessment: <font color=\"{severity_badge[1]}\">{severity_badge[0]}</font></b>', styles['Heading3']))
    story.append(Spacer(1, 8))

    story.append(Paragraph('<b>Inspector Corrective Recommendations:</b>', styles['Heading3']))
    for r in recommendations_text:
        story.append(Paragraph(f'&bull; {r}', styles['Normal']))

    doc.build(story)

create_pdf(
    os.path.join(insp_dir, "inspection_report_P101_clean.pdf"),
    "EQUIPMENT INSPECTION REPORT: CENTRIFUGAL PUMP P-101",
    [
        ["Vibration RMS (Outboard)", "7.4 mm/s", "<= 4.5 mm/s (Trip > 7.1)", "CRITICAL EXCEEDED"],
        ["Bearing Temperature", "88.0 deg C", "<= 75.0 deg C (SOP-M-104)", "EXCEEDED HIGH"],
        ["Mechanical Seal Leakage", "14 drops/min", "<= 5 drops/min", "EXCEEDED LEAK"],
        ["Suction Pressure", "0.32 MPa", "0.30 - 0.40 MPa", "NORMAL"],
        ["Discharge Pressure", "1.85 MPa", "1.80 - 2.10 MPa", "NORMAL"],
        ["Flow Rate (Q)", "48.5 m3/h", "50.0 m3/h BEP", "SLIGHT REDUCTION"],
    ],
    [
        "Outboard bearing vibration reached 7.4 mm/s RMS, exceeding ISO 10816-3 Zone D trip limit of 7.1 mm/s.",
        "Bearing running temperature elevated to 88.0 deg C, exceeding SOP-M-104 ceiling of 75.0 deg C.",
        "Silicon carbide mechanical cartridge seal dynamic leakage measured at 14 drops/minute (> 5 drops/min limit).",
        "Localized pitting and cavitation erosion detected on impeller suction eye (depth: 1.2 mm)."
    ],
    [
        "Immediately execute emergency shutdown and electrical LOTO isolation per SOP-SAF-001.",
        "Dismantle pump casing, replace mechanical cartridge seal assembly.",
        "Replace drive-end and non-drive-end bearing assemblies.",
        "Perform precision laser shaft alignment (angular offset <= 0.05 mm, radial <= 0.05 mm).",
        "Conduct hydrostatic pressure validation test at 1.5x MAWP for 15 minutes before recommissioning."
    ],
    ("CRITICAL — IMMEDIATE ACTION REQUIRED", "#D9534F")
)

create_pdf(
    os.path.join(insp_dir, "inspection_report_P202_clean.pdf"),
    "EQUIPMENT INSPECTION REPORT: BOOSTER PUMP P-202",
    [
        ["Vibration RMS (Drive End)", "5.1 mm/s", "<= 4.5 mm/s (Zone C 4.5-7.1)", "WARNING (ZONE C)"],
        ["Bearing Temperature", "71.0 deg C", "<= 75.0 deg C (SOP-M-104)", "NORMAL"],
        ["Mechanical Seal Leakage", "2 drops/min", "<= 5 drops/min", "NORMAL"],
        ["Suction Pressure", "0.85 MPa", "0.80 - 0.90 MPa", "NORMAL"],
        ["Discharge Pressure", "4.20 MPa", "4.10 - 4.30 MPa", "NORMAL"],
        ["Flow Rate (Q)", "82.0 m3/h", "80.0 - 85.0 m3/h", "NORMAL"],
    ],
    [
        "Drive-end bearing vibration recorded at 5.1 mm/s RMS, falling into ISO 10816-3 Zone C warning condition.",
        "Bearing temperature normal at 71.0 deg C; seal leakage normal at 2 drops/minute.",
        "External casing shows uniform atmospheric oxidation with zero localized pitting."
    ],
    [
        "Schedule planned maintenance overhaul within 14 days per SOP-M-104 Section 3.",
        "Inspect flexible motor-pump coupling elastomeric insert for backlash and wear.",
        "Replenish bearing grease with ISO VG 46 synthetic lubricant.",
        "Log triaxial vibration daily until overhaul."
    ],
    ("HIGH — PLANNED OVERHAUL WITHIN 14 DAYS", "#F0AD4E")
)

# ----------------- Generate Scanned / Degraded Images -----------------
def generate_scanned_image(text_report, out_png, out_pdf, stamp_text="SOVEREIGN AUDIT VERIFIED"):
    w, h = 1400, 1800
    img = Image.new("RGB", (w, h), color=(252, 251, 248))
    draw = ImageDraw.Draw(img)

    draw.rectangle([(50, 40), (w - 50, 100)], fill=(31, 78, 120))
    draw.text((70, 60), "SOVEREIGN INDUSTRIAL FACILITY — EQUIPMENT INSPECTION REPORT", fill=(255, 255, 255))
    
    y = 120
    for line in text_report.split("\n"):
        if not line.strip():
            y += 18
            continue
        if line.startswith(("1.", "2.", "3.", "4.", "5.")):
            y += 8
            draw.rectangle([(50, y), (w - 50, y + 26)], fill=(225, 232, 240))
            draw.text((60, y + 4), line, fill=(15, 15, 15))
            y += 32
        elif line.startswith("-"):
            draw.text((75, y), line, fill=(40, 40, 40))
            y += 22
        else:
            draw.text((60, y), line, fill=(25, 25, 25))
            y += 20

    # Stamp
    stamp_x, stamp_y = w - 420, h - 260
    draw.rectangle([(stamp_x, stamp_y), (stamp_x + 350, stamp_y + 90)], outline=(180, 30, 30), width=3)
    draw.text((stamp_x + 15, stamp_y + 12), "PLANT RELIABILITY DIVISION", fill=(180, 30, 30))
    draw.text((stamp_x + 20, stamp_y + 38), stamp_text, fill=(180, 30, 30))
    draw.text((stamp_x + 25, stamp_y + 62), "AIR-GAP FIELD VERIFIED", fill=(180, 30, 30))

    # Skew/degrade
    rotated = img.rotate(0.5, resample=Image.BICUBIC, expand=False, fillcolor=(252, 251, 248))
    blurred = rotated.filter(ImageFilter.GaussianBlur(radius=0.35))

    blurred.save(out_png, format="PNG")
    blurred.save(out_pdf, format="PDF", resolution=150.0)

generate_scanned_image(
    txt_p101,
    os.path.join(insp_dir, "inspection_report_P101_scanned.png"),
    os.path.join(insp_dir, "inspection_report_P101_scanned.pdf"),
    "CRITICAL: SHUTDOWN REQ."
)

generate_scanned_image(
    txt_p202,
    os.path.join(insp_dir, "inspection_report_P202_scanned.png"),
    os.path.join(insp_dir, "inspection_report_P202_scanned.pdf"),
    "OVERHAUL IN 14 DAYS"
)

print("All clean and scanned inspection reports successfully generated.")
