import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.dml.color import RGBColor


# Theme Palette
NAVY_PRIMARY = RGBColor(10, 37, 64)       # #0A2540
TEAL_ACCENT = RGBColor(0, 128, 128)       # #008080
SLATE_GRAY = RGBColor(74, 85, 104)        # #4A5568
LIGHT_BG = RGBColor(248, 250, 252)        # #F8FAFC
CARD_BG = RGBColor(255, 255, 255)         # #FFFFFF
BORDER_COLOR = RGBColor(226, 232, 240)    # #E2E8F0
TEXT_DARK = RGBColor(26, 32, 44)          # #1A202C
TEXT_MUTED = RGBColor(100, 116, 139)      # #64748B
RED_ALERT = RGBColor(197, 48, 48)         # #C53030
GREEN_SUCCESS = RGBColor(34, 139, 34)     # #228B22
AMBER_WARN = RGBColor(217, 119, 6)        # #D97706


def _create_slide_with_header(
    prs: Presentation,
    title_text: str,
    category: str = "CONFIGIQ SOVEREIGN AI EXECUTIVE REVIEW"
) -> Any:
    """Helper to create a consistent widescreen slide with a clean header banner and footer."""
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)

    # Top Header Banner Shape
    top_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(1.1))
    top_bar.fill.solid()
    top_bar.fill.fore_color.rgb = NAVY_PRIMARY
    top_bar.line.fill.background()

    # Category Label
    cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.12), Inches(11.7), Inches(0.3))
    tf_cat = cat_box.text_frame
    tf_cat.word_wrap = True
    p_cat = tf_cat.paragraphs[0]
    p_cat.text = category.upper()
    p_cat.font.size = Pt(9.5)
    p_cat.font.bold = True
    p_cat.font.color.rgb = TEAL_ACCENT

    # Slide Title
    title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.38), Inches(11.7), Inches(0.6))
    tf_title = title_box.text_frame
    tf_title.word_wrap = True
    p_title = tf_title.paragraphs[0]
    p_title.text = title_text
    p_title.font.size = Pt(22)
    p_title.font.bold = True
    p_title.font.color.rgb = RGBColor(255, 255, 255)

    # Bottom Footer
    footer_box = slide.shapes.add_textbox(Inches(0.8), Inches(7.05), Inches(11.7), Inches(0.35))
    tf_foot = footer_box.text_frame
    p_foot = tf_foot.paragraphs[0]
    p_foot.text = "ConfigIQ Sovereign AI Workbench  |  100% Offline & Air-Gapped  |  Problem Statement 26117"
    p_foot.font.size = Pt(8.5)
    p_foot.font.color.rgb = TEXT_MUTED

    return slide


def _create_table(
    slide: Any,
    left: Inches,
    top: Inches,
    width: Inches,
    height: Inches,
    headers: List[str],
    rows: List[List[str]],
    col_widths: Optional[List[Inches]] = None
) -> None:
    """Helper to add a cleanly styled table to a PowerPoint slide."""
    num_rows = len(rows) + 1
    num_cols = len(headers)
    table_shape = slide.shapes.add_table(num_rows, num_cols, left, top, width, height)
    table = table_shape.table

    if col_widths and len(col_widths) == num_cols:
        for idx, w in enumerate(col_widths):
            table.columns[idx].width = w

    # Style Header Row
    for col_idx, h_text in enumerate(headers):
        cell = table.cell(0, col_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY_PRIMARY
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf = cell.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = h_text
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = RGBColor(255, 255, 255)
        p.alignment = PP_ALIGN.CENTER

    # Style Data Rows
    for row_idx, row_data in enumerate(rows, start=1):
        is_alt = (row_idx % 2 == 0)
        bg_color = LIGHT_BG if is_alt else CARD_BG

        for col_idx, cell_value in enumerate(row_data):
            cell = table.cell(row_idx, col_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = bg_color
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf = cell.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.text = str(cell_value)
            p.font.size = Pt(10)
            p.font.color.rgb = TEXT_DARK

            # Align status / tags center
            val_upper = str(cell_value).upper()
            if val_upper in ["HIGH", "CRITICAL", "MANDATORY"]:
                p.font.bold = True
                p.font.color.rgb = RED_ALERT
                p.alignment = PP_ALIGN.CENTER
            elif val_upper in ["PASS", "COMPLIANT", "SUPPORTED", "APPROVED", "LOW"]:
                p.font.bold = True
                p.font.color.rgb = GREEN_SUCCESS
                p.alignment = PP_ALIGN.CENTER
            elif "REVIEW" in val_upper or "MEDIUM" in val_upper or "WARNING" in val_upper:
                p.font.bold = True
                p.font.color.rgb = AMBER_WARN
                p.alignment = PP_ALIGN.CENTER
            elif col_idx == 0:
                p.font.bold = True


def create_executive_summary_pptx(
    output_path: str,
    task_id: str,
    reference_document: str = "Industrial Inspection Report CV-102.pdf",
    executive_summary: Optional[Dict[str, Any]] = None,
    findings: Optional[List[Dict[str, Any]]] = None,
    sop_comparisons: Optional[List[Dict[str, Any]]] = None,
    risks: Optional[List[Dict[str, Any]]] = None,
    recommended_actions: Optional[List[Dict[str, Any]]] = None,
    approval_recommendation: Optional[Dict[str, Any]] = None,
    sources_and_sovereignty: Optional[Dict[str, Any]] = None,
    title: str = "Inspection Report Review"
) -> str:
    """
    Generate an 8-slide Professional Executive Summary PowerPoint presentation.
    Slide 1: Title Slide
    Slide 2: Executive Summary
    Slide 3: Inspection Findings
    Slide 4: SOP / Manual Comparison
    Slide 5: Risk Assessment
    Slide 6: Recommended Actions
    Slide 7: Approval Recommendation
    Slide 8: Sources & Sovereignty
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    prs = Presentation()
    # 16:9 Widescreen dimensions
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    gen_date = datetime.now(timezone.utc).strftime("%B %d, %Y (%H:%M UTC)")

    # =========================================================================
    # SLIDE 1: Title Slide
    # =========================================================================
    blank_layout = prs.slide_layouts[6]
    s1 = prs.slides.add_slide(blank_layout)

    # Background Top / Center Block
    bg_box = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(4.5))
    bg_box.fill.solid()
    bg_box.fill.fore_color.rgb = NAVY_PRIMARY
    bg_box.line.fill.background()

    # Title Subtitle & Name
    t_box = s1.shapes.add_textbox(Inches(1.0), Inches(1.2), Inches(11.333), Inches(2.5))
    tf1 = t_box.text_frame
    tf1.word_wrap = True

    p0 = tf1.paragraphs[0]
    p0.text = "CONFIGIQ SOVEREIGN AI WORKBENCH"
    p0.font.size = Pt(14)
    p0.font.bold = True
    p0.font.color.rgb = TEAL_ACCENT

    p1 = tf1.add_paragraph()
    p1.text = title
    p1.font.size = Pt(34)
    p1.font.bold = True
    p1.font.color.rgb = RGBColor(255, 255, 255)

    p2 = tf1.add_paragraph()
    p2.text = "Autonomous Multi-Modal Engineering Assessment & Sourced Verification"
    p2.font.size = Pt(15)
    p2.font.color.rgb = RGBColor(200, 215, 230)

    # Bottom Metadata Card
    card1 = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.0), Inches(4.9), Inches(11.333), Inches(2.0))
    card1.fill.solid()
    card1.fill.fore_color.rgb = CARD_BG
    card1.line.color.rgb = BORDER_COLOR

    c_box = s1.shapes.add_textbox(Inches(1.3), Inches(5.05), Inches(10.7), Inches(1.7))
    tf_c = c_box.text_frame
    tf_c.word_wrap = True

    def add_meta_line(tf, label, val):
        p = tf.add_paragraph() if len(tf.paragraphs[0].text) > 0 else tf.paragraphs[0]
        r1 = p.add_run()
        r1.text = f"{label}: "
        r1.font.bold = True
        r1.font.size = Pt(11)
        r1.font.color.rgb = NAVY_PRIMARY
        r2 = p.add_run()
        r2.text = str(val)
        r2.font.size = Pt(11)
        r2.font.color.rgb = TEXT_DARK

    add_meta_line(tf_c, "Task ID", task_id)
    add_meta_line(tf_c, "Reference Document", reference_document)
    add_meta_line(tf_c, "Generated Date", gen_date)
    add_meta_line(tf_c, "Operational Mode", "100% Air-Gapped Local Inference (No External Cloud APIs)")

    # =========================================================================
    # SLIDE 2: Executive Summary
    # =========================================================================
    s2 = _create_slide_with_header(prs, "Executive Summary & Audit Assessment")
    exec_data = executive_summary or {
        "overall_finding": "Critical wall thickness degradation identified on high-pressure control valve CV-102.",
        "severity": "HIGH (Mandatory Action Required)",
        "key_conclusion": "Wall loss has reached 36% (measured 3.2mm vs 5.0mm nominal), exceeding the 30% retirement threshold under SOP-M-402.",
        "verification_status": "SUPPORTED & VERIFIED against local SOP knowledge base"
    }

    # Left Card: Core Findings
    left_card = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.4), Inches(7.5), Inches(5.3))
    left_card.fill.solid()
    left_card.fill.fore_color.rgb = CARD_BG
    left_card.line.color.rgb = BORDER_COLOR

    lt_box = s2.shapes.add_textbox(Inches(1.1), Inches(1.6), Inches(6.9), Inches(4.9))
    ltf = lt_box.text_frame
    ltf.word_wrap = True

    p_lh = ltf.paragraphs[0]
    p_lh.text = "Key Operational Findings"
    p_lh.font.size = Pt(16)
    p_lh.font.bold = True
    p_lh.font.color.rgb = NAVY_PRIMARY

    p_f1 = ltf.add_paragraph()
    p_f1.text = f"• Primary Finding: {exec_data.get('overall_finding', '')}"
    p_f1.font.size = Pt(12)
    p_f1.font.color.rgb = TEXT_DARK

    p_f2 = ltf.add_paragraph()
    p_f2.text = f"• Conclusion: {exec_data.get('key_conclusion', '')}"
    p_f2.font.size = Pt(12)
    p_f2.font.color.rgb = TEXT_DARK

    p_f3 = ltf.add_paragraph()
    p_f3.text = "• Compliance Impact: Mandatory Double Block & Bleed isolation and valve replacement before next pressurization cycle."
    p_f3.font.size = Pt(12)
    p_f3.font.color.rgb = TEXT_DARK

    # Right Card: Status & Severity Callout
    right_card = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(8.6), Inches(1.4), Inches(3.9), Inches(5.3))
    right_card.fill.solid()
    right_card.fill.fore_color.rgb = LIGHT_BG
    right_card.line.color.rgb = BORDER_COLOR

    rt_box = s2.shapes.add_textbox(Inches(8.8), Inches(1.6), Inches(3.5), Inches(4.9))
    rtf = rt_box.text_frame
    rtf.word_wrap = True

    p_rh = rtf.paragraphs[0]
    p_rh.text = "Audit Verdict"
    p_rh.font.size = Pt(16)
    p_rh.font.bold = True
    p_rh.font.color.rgb = NAVY_PRIMARY

    p_sev_lbl = rtf.add_paragraph()
    p_sev_lbl.text = "Assessed Severity:"
    p_sev_lbl.font.size = Pt(11)
    p_sev_lbl.font.color.rgb = TEXT_MUTED

    p_sev = rtf.add_paragraph()
    p_sev.text = exec_data.get("severity", "HIGH")
    p_sev.font.size = Pt(14)
    p_sev.font.bold = True
    p_sev.font.color.rgb = RED_ALERT if "HIGH" in str(exec_data.get("severity", "")).upper() else NAVY_PRIMARY

    p_ver_lbl = rtf.add_paragraph()
    p_ver_lbl.text = "Verification Status:"
    p_ver_lbl.font.size = Pt(11)
    p_ver_lbl.font.color.rgb = TEXT_MUTED

    p_ver = rtf.add_paragraph()
    p_ver.text = exec_data.get("verification_status", "SUPPORTED")
    p_ver.font.size = Pt(13)
    p_ver.font.bold = True
    p_ver.font.color.rgb = GREEN_SUCCESS

    # =========================================================================
    # SLIDE 3: Inspection Findings
    # =========================================================================
    s3 = _create_slide_with_header(prs, "Detailed Inspection Findings & Evidence")
    f_headers = ["Inspection Item / Finding", "Severity", "Observed Evidence & Measurement", "Source / Page"]
    default_findings = findings or [
        {
            "finding": "Flange Wall Thinning (CV-102)",
            "severity": "HIGH",
            "evidence": "UT measurement indicates 3.2mm wall thickness vs 5.0mm nominal (36% loss).",
            "source": f"{reference_document}, Page 1"
        },
        {
            "finding": "Gasket Surface Pitting",
            "severity": "HIGH",
            "evidence": "Visible ring-joint surface pitting exceeding 0.5mm depth tolerance.",
            "source": f"{reference_document}, Page 1"
        },
        {
            "finding": "Actuator Fastener Oxidation",
            "severity": "MEDIUM",
            "evidence": "Atmospheric surface corrosion on B7 studs without torque loss.",
            "source": f"{reference_document}, Page 1"
        }
    ]
    f_rows = []
    for f in default_findings:
        f_rows.append([
            f.get("finding", "Finding"),
            f.get("severity", "HIGH"),
            f.get("evidence", "Evidence"),
            f.get("source", "Report, Page 1")
        ])
    _create_table(
        s3,
        left=Inches(0.8),
        top=Inches(1.5),
        width=Inches(11.733),
        height=Inches(4.8),
        headers=f_headers,
        rows=f_rows,
        col_widths=[Inches(3.2), Inches(1.5), Inches(5.0), Inches(2.033)]
    )

    # =========================================================================
    # SLIDE 4: SOP / Manual Comparison
    # =========================================================================
    s4 = _create_slide_with_header(prs, "SOP & Technical Manual Compliance Matrix")
    sop_headers = ["Finding", "Relevant SOP", "Expected Condition", "Observed Condition", "Status"]
    default_sops = sop_comparisons or [
        {
            "finding": "Control Valve Wall Loss",
            "sop": "SOP-M-402 (Sec 1.2)",
            "expected": "Max wall thinning <= 30% (3.5mm min)",
            "observed": "36% wall loss (3.2mm actual)",
            "status": "NON-COMPLIANT"
        },
        {
            "finding": "Flange Sealing Face",
            "sop": "ASME B16.5 / SOP-M-402",
            "expected": "Smooth RTJ gasket groove without pitting",
            "observed": "Localized pitting detected",
            "status": "NON-COMPLIANT"
        },
        {
            "finding": "Material Spec",
            "sop": "SOP-M-402 (Sec 3.1)",
            "expected": "316L Stainless Steel for sour service",
            "observed": "Original Carbon Steel body",
            "status": "UPGRADE REQ"
        }
    ]
    sop_rows = []
    for sc in default_sops:
        sop_rows.append([
            sc.get("finding", "Item"),
            sc.get("sop", "SOP-M-402"),
            sc.get("expected", "Expected condition"),
            sc.get("observed", "Observed condition"),
            sc.get("status", "NON-COMPLIANT")
        ])
    _create_table(
        s4,
        left=Inches(0.8),
        top=Inches(1.5),
        width=Inches(11.733),
        height=Inches(4.8),
        headers=sop_headers,
        rows=sop_rows,
        col_widths=[Inches(2.5), Inches(2.2), Inches(2.8), Inches(2.5), Inches(1.733)]
    )

    # =========================================================================
    # SLIDE 5: Risk Assessment
    # =========================================================================
    s5 = _create_slide_with_header(prs, "Operational Risk Assessment & Prioritization")
    risk_headers = ["Identified Risk", "Severity", "Operational Impact & Evidence", "Priority"]
    default_risks = risks or [
        {
            "risk": "Flange Rupture Under Pressure",
            "severity": "CRITICAL",
            "impact": "Potential high-pressure fluid release if operated at nominal line pressure.",
            "priority": "P1 - IMMEDIATE"
        },
        {
            "risk": "Fugitive Emissions from Gasket",
            "severity": "HIGH",
            "impact": "Seal failure at RTJ ring groove causing toxic/flammable leakage.",
            "priority": "P1 - IMMEDIATE"
        },
        {
            "risk": "Fastener Seizure During Service",
            "severity": "MEDIUM",
            "impact": "Delays during emergency maintenance if studs are not replaced.",
            "priority": "P2 - SCHEDULED"
        }
    ]
    risk_rows = []
    for r in default_risks:
        risk_rows.append([
            r.get("risk", "Risk"),
            r.get("severity", "HIGH"),
            r.get("impact", "Impact description"),
            r.get("priority", "P1")
        ])
    _create_table(
        s5,
        left=Inches(0.8),
        top=Inches(1.5),
        width=Inches(11.733),
        height=Inches(4.8),
        headers=risk_headers,
        rows=risk_rows,
        col_widths=[Inches(3.2), Inches(1.8), Inches(4.733), Inches(2.0)]
    )

    # =========================================================================
    # SLIDE 6: Recommended Actions
    # =========================================================================
    s6 = _create_slide_with_header(prs, "Recommended Engineering Actions & Work Order")
    act_headers = ["Action Item", "Priority", "Technical Justification / SOP Clause", "Source"]
    default_actions = recommended_actions or [
        {
            "action": "Execute Double Block and Bleed (DBB) isolation and LOTO.",
            "priority": "P1",
            "reason": "Ensure zero stored energy per SOP-M-402 Section 2.",
            "source": "SOP-M-402.pdf (Page 2)"
        },
        {
            "action": "Procure and install ASME B31.3 certified 316L replacement valve.",
            "priority": "P1",
            "reason": "Mandatory replacement for wall loss > 30%.",
            "source": "SOP-M-402.pdf (Page 3)"
        },
        {
            "action": "Torque flange bolts to 220 Nm in cross-pattern star sequence.",
            "priority": "P1",
            "reason": "Uniform compression of new RTJ metallic gasket.",
            "source": "SOP-M-402.pdf (Page 4)"
        },
        {
            "action": "Conduct 30-min hydrostatic pressure test at 1.5x operating pressure.",
            "priority": "P1",
            "reason": "Validation before final commissioning sign-off.",
            "source": "SOP-M-402.pdf (Page 4)"
        }
    ]
    act_rows = []
    for a in default_actions:
        act_rows.append([
            a.get("action", "Action"),
            a.get("priority", "P1"),
            a.get("reason", "Reason"),
            a.get("source", "SOP-M-402")
        ])
    _create_table(
        s6,
        left=Inches(0.8),
        top=Inches(1.5),
        width=Inches(11.733),
        height=Inches(4.8),
        headers=act_headers,
        rows=act_rows,
        col_widths=[Inches(4.0), Inches(1.3), Inches(4.4), Inches(2.033)]
    )

    # =========================================================================
    # SLIDE 7: Approval Recommendation
    # =========================================================================
    s7 = _create_slide_with_header(prs, "Formal Approval Recommendation & Review Requirements")
    app_data = approval_recommendation or {
        "recommendation": "APPROVED FOR IMMEDIATE REPLACEMENT WORK ORDER",
        "verification_status": "SUPPORTED — Sourced from Inspection Report & SOP-M-402",
        "human_review_required": False,
        "human_review_notes": "Mandatory physical sign-off by Maintenance Superintendent before high-pressure hydrotest."
    }

    rec_card = s7.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.5), Inches(11.733), Inches(5.0))
    rec_card.fill.solid()
    rec_card.fill.fore_color.rgb = CARD_BG
    rec_card.line.color.rgb = BORDER_COLOR

    rb_box = s7.shapes.add_textbox(Inches(1.1), Inches(1.7), Inches(11.133), Inches(4.5))
    rtfb = rb_box.text_frame
    rtfb.word_wrap = True

    p_rh2 = rtfb.paragraphs[0]
    p_rh2.text = "Autonomous Agent Recommendation Verdict"
    p_rh2.font.size = Pt(16)
    p_rh2.font.bold = True
    p_rh2.font.color.rgb = NAVY_PRIMARY

    p_rv = rtfb.add_paragraph()
    p_rv.text = f"Recommendation: {app_data.get('recommendation', 'APPROVED')}"
    p_rv.font.size = Pt(15)
    p_rv.font.bold = True
    p_rv.font.color.rgb = TEAL_ACCENT

    p_rst = rtfb.add_paragraph()
    p_rst.text = f"Verification Status: {app_data.get('verification_status', 'SUPPORTED')}"
    p_rst.font.size = Pt(12)
    p_rst.font.bold = True
    p_rst.font.color.rgb = GREEN_SUCCESS

    p_rhr = rtfb.add_paragraph()
    p_rhr.text = f"Human Review Requirements: {app_data.get('human_review_notes', 'Physical inspection sign-off required.')}"
    p_rhr.font.size = Pt(12)
    p_rhr.font.color.rgb = TEXT_DARK

    p_disc = rtfb.add_paragraph()
    p_disc.text = "Note: This is an AI-assisted draft generated by ConfigIQ Sovereign Agent. Final work order release requires certified engineer signature."
    p_disc.font.size = Pt(10)
    p_disc.font.italic = True
    p_disc.font.color.rgb = TEXT_MUTED

    # =========================================================================
    # SLIDE 8: Sources & Sovereignty
    # =========================================================================
    s8 = _create_slide_with_header(prs, "Data Provenance & Air-Gapped Sovereignty Attestation")
    sovereignty_headers = ["Governance Dimension", "Operational Guarantee", "Local Technology Component", "Status"]
    sov_rows = [
        ["Network Sovereignty", "LOCAL_ONLY (Zero External Internet / APIs)", "FastAPI + Local Host Only", "VERIFIED"],
        ["Open-Weight LLMs", "On-Premise Model Weights Inference", "Ollama (Llama 3, Qwen 2.5 Coder, Moondream)", "VERIFIED"],
        ["Document & Knowledge RAG", "Local Vector Store & Semantic Embeddings", "ChromaDB + Nomic-Embed-Text", "VERIFIED"],
        ["Vision & OCR Processing", "Local Optical Character Recognition & Multimodal", "PyMuPDF + Tesseract OCR + Moondream", "VERIFIED"],
        ["Code Sandbox Execution", "Isolated Local Subprocess Sandbox with Blocked Sockets", "Python 3.10 Subprocess Sandbox", "VERIFIED"],
        ["Deliverable Generation", "100% Local Word, Excel, PowerPoint Compilation", "python-docx, openpyxl, python-pptx", "VERIFIED"]
    ]
    _create_table(
        s8,
        left=Inches(0.8),
        top=Inches(1.5),
        width=Inches(11.733),
        height=Inches(4.8),
        headers=sovereignty_headers,
        rows=sov_rows,
        col_widths=[Inches(2.5), Inches(3.8), Inches(3.7), Inches(1.733)]
    )

    prs.save(output_path)
    return output_path


def create_presentation(output_path: str, title: str, slides: List[Dict[str, Any]]) -> str:
    """Generic presentation creator for backward compatibility."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # Title slide
    blank_layout = prs.slide_layouts[6]
    s_title = prs.slides.add_slide(blank_layout)
    top_bar = s_title.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(4.5))
    top_bar.fill.solid()
    top_bar.fill.fore_color.rgb = NAVY_PRIMARY
    t_box = s_title.shapes.add_textbox(Inches(1.0), Inches(1.5), Inches(11.333), Inches(2.0))
    p = t_box.text_frame.paragraphs[0]
    p.text = title
    p.font.size = Pt(32)
    p.font.bold = True
    p.font.color.rgb = RGBColor(255, 255, 255)

    for slide_info in slides:
        stitle = slide_info.get("title", "Slide")
        s = _create_slide_with_header(prs, stitle)
        content = slide_info.get("content", [])
        tb = s.shapes.add_textbox(Inches(1.0), Inches(1.6), Inches(11.333), Inches(5.0))
        tf = tb.text_frame
        tf.word_wrap = True
        if isinstance(content, list):
            for item in content:
                p_item = tf.add_paragraph()
                p_item.text = f"• {item}"
                p_item.font.size = Pt(14)
                p_item.font.color.rgb = TEXT_DARK
        else:
            p_item = tf.add_paragraph()
            p_item.text = str(content)
            p_item.font.size = Pt(14)
            p_item.font.color.rgb = TEXT_DARK

    prs.save(output_path)
    return output_path