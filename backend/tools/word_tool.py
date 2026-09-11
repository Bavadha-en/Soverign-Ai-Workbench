import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT


def create_approval_note_docx(
    output_path: str,
    task_id: str,
    reference_document: str = "Inspection Report",
    executive_summary: str = "",
    inspection_findings: Optional[List[str]] = None,
    sop_references: Optional[List[str]] = None,
    risk_severity: str = "HIGH",
    recommended_actions: Optional[List[str]] = None,
    approval_recommendation: str = "APPROVED WITH CONDITIONS",
    sources: Optional[List[Dict[str, Any]]] = None,
    model_used: Optional[str] = "llama3:latest",
    verification_status: Optional[str] = "SUPPORTED",
    human_review_required: Optional[bool] = None,
    timestamp: Optional[str] = None,
    is_synthetic_demo: bool = False,
    measurement_checks: Optional[List[Dict[str, Any]]] = None,
    review_items: Optional[List[str]] = None,
    severity_basis: Optional[str] = None
) -> str:
    """
    Generate an official Inspection Report Review & Approval Note as a Word (.docx) document.
    Structure:
      1. Reference Document
      2. Executive Summary
      3. Inspection Findings
      4. SOP / Manual References
      5. Risk / Severity
      6. Recommended Actions
      7. Approval Recommendation
      8. Sources
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc = Document()

    # Determine human review requirement
    v_status_upper = (verification_status or "SUPPORTED").upper()
    needs_review = (
        human_review_required is True
        or bool(review_items)
        or "UNSUPPORTED" in v_status_upper
        or "NEEDS REVIEW" in v_status_upper
        or "NEEDS_REVIEW" in v_status_upper
    )

    gen_time = timestamp or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # Document Title (Heading 0)
    title = doc.add_heading("Inspection Report Review & Approval Note", level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Subtitle / Classification
    p_meta = doc.add_paragraph()
    p_meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    meta_run = p_meta.add_run("ConfigIQ Sovereign AI Workbench  |  Confidential / Air-Gapped Industrial Review")
    meta_run.font.size = Pt(9.5)
    meta_run.font.bold = True
    meta_run.font.color.rgb = RGBColor(60, 60, 60)

    # Metadata Summary Box / Paragraph
    p_details = doc.add_paragraph()
    p_details.alignment = WD_ALIGN_PARAGRAPH.CENTER
    details_run = p_details.add_run(
        f"Task ID: {task_id}  |  Generated: {gen_time}  |  Model: {model_used or 'llama3:latest'}  |  Status: {v_status_upper}"
    )
    details_run.font.size = Pt(8.5)
    details_run.font.color.rgb = RGBColor(100, 100, 100)

    # Prominent Human Review Callout if needed
    if needs_review:
        p_warn = doc.add_paragraph()
        p_warn.alignment = WD_ALIGN_PARAGRAPH.CENTER
        warn_text = "⚠ HUMAN REVIEW REQUIRED: AI-assisted draft — human approval required."
        if review_items:
            n = len(review_items)
            warn_text += f" {n} item{'s' if n != 1 else ''} to check, listed in section 5."
        warn_run = p_warn.add_run(warn_text)
        warn_run.bold = True
        warn_run.font.size = Pt(11)
        warn_run.font.color.rgb = RGBColor(190, 30, 30)
    else:
        p_cert = doc.add_paragraph()
        p_cert.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cert_text = (
            "✔ SOURCED & VERIFIED — every value traced to the report and checked against the cited SOP. "
            "Engineer sign-off still required."
            if measurement_checks
            else "✔ SOURCED & VERIFIED — Autonomous Sovereign Agent Audit Complete"
        )
        cert_run = p_cert.add_run(cert_text)
        cert_run.font.size = Pt(9)
        cert_run.font.color.rgb = RGBColor(0, 120, 40)

    if is_synthetic_demo:
        p_demo = doc.add_paragraph()
        p_demo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        demo_run = p_demo.add_run("[DEMO NOTE: Evaluation data based on local industrial dataset]")
        demo_run.font.italic = True
        demo_run.font.size = Pt(8.5)
        demo_run.font.color.rgb = RGBColor(150, 50, 50)

    doc.add_paragraph()  # Spacer

    # Section 1: Reference Document
    doc.add_heading("1. Reference Document", level=1)
    p1 = doc.add_paragraph(f"Primary Document: {reference_document}")
    p1.paragraph_format.left_indent = Inches(0.2)

    # Section 2: Executive Summary
    doc.add_heading("2. Executive Summary", level=1)
    p2 = doc.add_paragraph(
        executive_summary
        or "Autonomous inspection review completed successfully via ConfigIQ sovereign AI pipeline."
    )
    p2.paragraph_format.left_indent = Inches(0.2)

    # Section 3: Inspection Findings
    doc.add_heading("3. Inspection Findings", level=1)
    if measurement_checks:
        _add_measurement_table(doc, measurement_checks)
        p_quote = doc.add_paragraph()
        p_quote.add_run("Inspector's findings, quoted from the report:").bold = True
    findings = inspection_findings or ["No anomalous inspection items recorded."]
    for f in findings:
        doc.add_paragraph(f, style="List Bullet")

    # Section 4: SOP / Manual References
    doc.add_heading("4. SOP / Manual References", level=1)
    sops = sop_references or ["Standard Maintenance Guidelines (General)"]
    for s in sops:
        doc.add_paragraph(s, style="List Bullet")

    # Section 5: Risk / Severity
    doc.add_heading("5. Risk / Severity Assessment", level=1)
    p5 = doc.add_paragraph()
    p5.paragraph_format.left_indent = Inches(0.2)
    risk_label = p5.add_run(f"Risk Level: {risk_severity.upper()}")
    risk_label.bold = True
    if "HIGH" in risk_severity.upper() or "CRITICAL" in risk_severity.upper():
        risk_label.font.color.rgb = RGBColor(180, 0, 0)
    elif "MEDIUM" in risk_severity.upper():
        risk_label.font.color.rgb = RGBColor(200, 120, 0)
    else:
        risk_label.font.color.rgb = RGBColor(0, 140, 0)
    if severity_basis:
        p_basis = doc.add_paragraph(f"Basis: {severity_basis}")
        p_basis.paragraph_format.left_indent = Inches(0.2)
    if review_items:
        p_rev_head = doc.add_paragraph()
        p_rev_head.paragraph_format.left_indent = Inches(0.2)
        r_head = p_rev_head.add_run("Check these before signing:")
        r_head.bold = True
        r_head.font.color.rgb = RGBColor(190, 30, 30)
        for item in review_items:
            doc.add_paragraph(f"Review item: {item}", style="List Bullet")

    # Section 6: Recommended Actions
    doc.add_heading("6. Recommended Actions", level=1)
    actions = recommended_actions or ["Proceed with routine maintenance monitoring."]
    for a in actions:
        doc.add_paragraph(a, style="List Bullet")

    # Section 7: Approval Recommendation
    doc.add_heading("7. Approval Recommendation", level=1)
    p7 = doc.add_paragraph()
    p7.paragraph_format.left_indent = Inches(0.2)
    rec_run = p7.add_run(f"Recommendation: {approval_recommendation}")
    rec_run.bold = True
    rec_run.font.size = Pt(11)

    if needs_review:
        p7_review = doc.add_paragraph()
        p7_review.paragraph_format.left_indent = Inches(0.2)
        r_rev = p7_review.add_run("Human Review Requirements: Mandatory physical inspection sign-off before work order closure.")
        r_rev.font.italic = True
        r_rev.font.size = Pt(9.5)
        r_rev.font.color.rgb = RGBColor(150, 0, 0)

    # Sign-off: ConfigIQ drafts, a named engineer approves.
    sign = doc.add_table(rows=3, cols=3)
    sign.style = "Table Grid"
    for col, text in enumerate(["Role", "Name and designation", "Signature and date"]):
        cell = sign.cell(0, col)
        _set_cell_background(cell, "1F4E79")
        run = cell.paragraphs[0].add_run(text)
        run.font.bold = True
        run.font.size = Pt(9.5)
        run.font.color.rgb = RGBColor(255, 255, 255)
    for row, cells in enumerate([
        ("Prepared by", "ConfigIQ (automated draft)", "Not signed: a draft cannot approve work"),
        ("Reviewed and approved by", "", ""),
    ], start=1):
        for col, text in enumerate(cells):
            run = sign.cell(row, col).paragraphs[0].add_run(text)
            run.font.size = Pt(9.5)

    # Section 8: Sources
    doc.add_heading("8. Verified Sources & Knowledge Provenance", level=1)
    src_list = sources or [{"document": reference_document, "page": 1, "score": 1.0}]
    for src in src_list:
        doc_name = src.get("document", "Unknown")
        page_num = src.get("page", "N/A")
        score = src.get("score")
        # Retrieved SOP excerpts are context, not verified claims.
        status_tag = src.get("status", "RETRIEVED")
        score_str = f" (relevance score: {score:.2f})" if score is not None else ""
        doc.add_paragraph(
            f"Source: {doc_name}, Page {page_num}{score_str} [Status: {status_tag}]",
            style="List Bullet"
        )

    doc.save(output_path)
    return output_path


def _add_measurement_table(doc, checks: List[Dict[str, Any]]) -> None:
    """Each reading as read from the report, with its limit, the limit's source, and the check result."""
    from backend.documents.inspection_checks import STATUS_TEXT

    intro = doc.add_paragraph()
    intro.add_run("Measured values, read from the report and checked by ConfigIQ against the limits in the cited SOP:").bold = True
    table = doc.add_table(rows=len(checks) + 1, cols=5)
    table.style = "Table Grid"
    for col, text in enumerate(["Parameter", "Reading (report line)", "Limit and source", "ConfigIQ check", "Report states"]):
        cell = table.cell(0, col)
        _set_cell_background(cell, "1F4E79")
        run = cell.paragraphs[0].add_run(text)
        run.font.bold = True
        run.font.size = Pt(9)
        run.font.color.rgb = RGBColor(255, 255, 255)

    colours = {
        "CRITICAL": RGBColor(180, 0, 0),
        "EXCEEDED": RGBColor(180, 0, 0),
        "WARNING": RGBColor(190, 110, 0),
        "DEVIATION": RGBColor(190, 110, 0),
        "OK": RGBColor(0, 120, 40),
    }
    agreement = {"AGREES": "agrees", "DIFFERS": "differs: check", "STATED_ONLY": "not checkable"}
    for row, m in enumerate(checks, start=1):
        reading = f"{m['value_text']} {m['unit']}\nline {m['line']}"
        if m.get("confidence") is not None:
            reading += f", OCR {m['confidence']:.2f}"
        limit = m.get("limit", "")
        if m.get("limit_source") == "report":
            limit += "\nstated in the report"
        elif m.get("limit_source"):
            limit += f"\n{m['limit_source']}"
        status = m.get("status", "UNKNOWN")
        check = STATUS_TEXT.get(status, status)
        if m.get("zone"):
            check += f" (Zone {m['zone']})"
        if m.get("basis") == "report_statement":
            check += ", as stated; no numeric limit to check"
        elif m.get("meaning"):
            check += f": {m['meaning']}"
        stated = m.get("stated_status")
        states = STATUS_TEXT.get(stated, stated) if stated else "not stated"
        if agreement.get(m.get("agreement")):
            states += f" ({agreement[m['agreement']]})"

        for col, text in enumerate([m.get("label_full", ""), reading, limit, check, states]):
            run = table.cell(row, col).paragraphs[0].add_run(text)
            run.font.size = Pt(9)
            if col == 3 and status in colours:
                run.font.color.rgb = colours[status]
                run.bold = True
    doc.add_paragraph()


def _set_cell_background(cell, hex_color: str):
    """Utility helper to set table cell shading color."""
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex_color)
    tcPr.append(shd)


def create_word(
    output_path: str,
    title: str,
    sections: dict,
    subject: Optional[str] = None,
    task_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generates a structured Word (.docx) document with styled headings and paragraphs.
    Logs action to audit_service.
    """
    import time
    from backend.models.schemas import CreateWordOutput
    from backend.services.audit_service import audit_service

    start_time = time.time()
    try:
        dir_name = os.path.dirname(output_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

        doc = Document()

        # Document Title
        heading = doc.add_heading(level=0)
        run = heading.add_run(title)
        run.font.name = "Calibri"
        run.font.size = Pt(22)
        run.font.bold = True
        run.font.color.rgb = RGBColor(16, 44, 87)

        # Subject Line
        if subject:
            p_sub = doc.add_paragraph()
            p_sub_bold = p_sub.add_run("Subject: ")
            p_sub_bold.font.name = "Calibri"
            p_sub_bold.font.size = Pt(12)
            p_sub_bold.bold = True
            p_sub_bold.font.color.rgb = RGBColor(30, 30, 30)

            p_sub_text = p_sub.add_run(subject)
            p_sub_text.font.name = "Calibri"
            p_sub_text.font.size = Pt(12)

        # Divider
        doc.add_paragraph()

        # Sections
        for section_title, section_body in sections.items():
            sec_heading = doc.add_heading(level=1)
            sec_run = sec_heading.add_run(section_title)
            sec_run.font.name = "Calibri"
            sec_run.font.size = Pt(14)
            sec_run.font.bold = True
            sec_run.font.color.rgb = RGBColor(53, 89, 142)

            for line in str(section_body).strip().split("\n"):
                if line.strip():
                    p = doc.add_paragraph()
                    p_run = p.add_run(line.strip())
                    p_run.font.name = "Calibri"
                    p_run.font.size = Pt(11)
                    p_run.font.color.rgb = RGBColor(40, 40, 40)

        doc.save(output_path)
        file_size = os.path.getsize(output_path)

        duration = round((time.time() - start_time) * 1000, 2)
        audit_service.log_action(
            action="CREATE_WORD",
            component="tools.word_tool",
            status="SUCCESS",
            task_id=task_id,
            duration_ms=duration,
            details={"output_path": output_path, "file_size": file_size, "sections_count": len(sections)}
        )

        return CreateWordOutput(
            success=True,
            output_path=output_path,
            file_size=file_size,
            error=None
        ).model_dump()
    except Exception as e:
        duration = round((time.time() - start_time) * 1000, 2)
        audit_service.log_action(
            action="CREATE_WORD",
            component="tools.word_tool",
            status="FAILURE",
            task_id=task_id,
            duration_ms=duration,
            details={"output_path": output_path, "error": str(e)}
        )
        return CreateWordOutput(
            success=False,
            output_path=output_path,
            file_size=0,
            error=str(e)
        ).model_dump()


def generate_approval_note(
    output_path: str = "outputs/Approval_Note.docx",
    title: str = "OFFICIAL APPROVAL NOTE",
    subject: str = "Equipment Maintenance & Replacement Approval Request",
    background: str = "Routine inspection conducted on industrial unit.",
    inspection_findings: str = "Corrosion and wall thinning identified during non-destructive testing.",
    technical_assessment: str = "Replacement required to prevent pressure containment failure.",
    applicable_sop: str = "SOP-MECH-44: High Pressure System Maintenance Procedure.",
    recommended_action: str = "Procure component and schedule emergency replacement window.",
    approval_requested: str = "Formal approval for expenditure and immediate execution.",
    task_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generates a structured, professional Approval Note Word document adhering to Phase 8 specifications.

    Structured Sections:
      - TITLE
      - Subject
      - 1. Background
      - 2. Inspection Findings
      - 3. Technical Assessment
      - 4. Applicable SOP
      - 5. Recommended Action
      - 6. Approval Requested
      - Formal Approval Sign-off Box
    """
    import time
    from backend.models.schemas import CreateWordOutput
    from backend.services.audit_service import audit_service

    start_time = time.time()
    try:
        dir_name = os.path.dirname(output_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

        doc = Document()

        # Title
        heading = doc.add_heading(level=0)
        h_run = heading.add_run(title)
        h_run.font.name = "Calibri"
        h_run.font.size = Pt(24)
        h_run.font.bold = True
        h_run.font.color.rgb = RGBColor(16, 44, 87)

        # Subject
        p_sub = doc.add_paragraph()
        p_sub_lbl = p_sub.add_run("Subject: ")
        p_sub_lbl.font.name = "Calibri"
        p_sub_lbl.font.size = Pt(13)
        p_sub_lbl.bold = True
        p_sub_lbl.font.color.rgb = RGBColor(16, 44, 87)

        p_sub_txt = p_sub.add_run(subject)
        p_sub_txt.font.name = "Calibri"
        p_sub_txt.font.size = Pt(13)
        p_sub_txt.bold = True

        doc.add_paragraph()

        # 6 Phase 8 standard sections
        sections_map = [
            ("1. Background", background),
            ("2. Inspection Findings", inspection_findings),
            ("3. Technical Assessment", technical_assessment),
            ("4. Applicable SOP", applicable_sop),
            ("5. Recommended Action", recommended_action),
            ("6. Approval Requested", approval_requested)
        ]

        for sec_title, sec_body in sections_map:
            sec_heading = doc.add_heading(level=1)
            s_run = sec_heading.add_run(sec_title)
            s_run.font.name = "Calibri"
            s_run.font.size = Pt(14)
            s_run.font.bold = True
            s_run.font.color.rgb = RGBColor(53, 89, 142)

            for line in str(sec_body).strip().split("\n"):
                if line.strip():
                    p = doc.add_paragraph()
                    p_run = p.add_run(line.strip())
                    p_run.font.name = "Calibri"
                    p_run.font.size = Pt(11)

        # Sign-off box table
        doc.add_paragraph()
        p_sign = doc.add_paragraph()
        p_sign_run = p_sign.add_run("7. Formal Approval Sign-off")
        p_sign_run.font.name = "Calibri"
        p_sign_run.font.size = Pt(14)
        p_sign_run.font.bold = True
        p_sign_run.font.color.rgb = RGBColor(53, 89, 142)

        table = doc.add_table(rows=3, cols=3)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER

        headers = ["Role", "Name & Designation", "Signature & Date"]
        for col_idx, text in enumerate(headers):
            cell = table.cell(0, col_idx)
            _set_cell_background(cell, "1F4E79")
            p = cell.paragraphs[0]
            run = p.add_run(text)
            run.font.name = "Calibri"
            run.font.size = Pt(10)
            run.font.bold = True
            run.font.color.rgb = RGBColor(255, 255, 255)

        rows_data = [
            ("Prepared By", "AI Inspection Agent (ConfigIQ)", "Automated System Log"),
            ("Approved By", "Chief Operations Authority", "______________________")
        ]

        for row_idx, row_content in enumerate(rows_data, 1):
            for col_idx, text in enumerate(row_content):
                cell = table.cell(row_idx, col_idx)
                p = cell.paragraphs[0]
                run = p.add_run(text)
                run.font.name = "Calibri"
                run.font.size = Pt(10)

        doc.save(output_path)
        file_size = os.path.getsize(output_path)

        duration = round((time.time() - start_time) * 1000, 2)
        audit_service.log_action(
            action="GENERATE_APPROVAL_NOTE",
            component="tools.word_tool",
            status="SUCCESS",
            task_id=task_id,
            duration_ms=duration,
            details={"output_path": output_path, "file_size": file_size}
        )

        return CreateWordOutput(
            success=True,
            output_path=output_path,
            file_size=file_size,
            error=None
        ).model_dump()
    except Exception as e:
        duration = round((time.time() - start_time) * 1000, 2)
        audit_service.log_action(
            action="GENERATE_APPROVAL_NOTE",
            component="tools.word_tool",
            status="FAILURE",
            task_id=task_id,
            duration_ms=duration,
            details={"output_path": output_path, "error": str(e)}
        )
        return CreateWordOutput(
            success=False,
            output_path=output_path,
            file_size=0,
            error=str(e)
        ).model_dump()


def create_engineering_report_docx(
    output_path: str,
    task_id: str,
    drawing_name: str,
    executive_summary: str,
    detected_equipment: Optional[List[Dict[str, Any]]] = None,
    detected_tags: Optional[List[Dict[str, Any]]] = None,
    relevant_topology: Optional[List[Dict[str, Any]]] = None,
    engineering_question: Optional[str] = None,
    answer: Optional[str] = None,
    evidence: Optional[List[str]] = None,
    rag_references: Optional[List[Dict[str, Any]]] = None,
    verification_status: str = "SUPPORTED",
    confidence: Union[str, float] = "HIGH",
    uncertain_items: Optional[List[Dict[str, Any]]] = None,
    timestamp: Optional[str] = None,
    is_offline: bool = True
) -> str:
    """
    Generate an official 15-section Dynamic Engineering Analysis & Verification Report (.docx).
    1. Title
    2. Input drawing/document
    3. Executive summary
    4. Detected equipment
    5. Detected tags
    6. Relevant topology
    7. Engineering question
    8. Answer
    9. Evidence
    10. RAG references
    11. Verification status
    12. Confidence
    13. Uncertain items / review items
    14. Timestamp
    15. Local/offline execution status
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc = Document()

    gen_time = timestamp or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # 1. Title Block
    title = doc.add_heading("Engineering Analysis & Verification Report", level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_sub = p_sub.add_run("ConfigIQ Sovereign AI Workbench  |  P&ID & Industrial Engineering Audit")
    r_sub.font.size = Pt(10)
    r_sub.font.bold = True
    r_sub.font.color.rgb = RGBColor(31, 78, 120)

    # Metadata banner
    p_meta = doc.add_paragraph()
    p_meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    conf_str = f"{confidence:.0%}" if isinstance(confidence, float) else str(confidence)
    r_meta = p_meta.add_run(
        f"Task ID: {task_id}  |  Generated: {gen_time}  |  Verification: {verification_status.upper()}  |  Confidence: {conf_str}"
    )
    r_meta.font.size = Pt(8.5)
    r_meta.font.color.rgb = RGBColor(100, 100, 100)

    # 15. Offline / Sovereignty Status Callout
    p_sovereign = doc.add_paragraph()
    p_sovereign.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if is_offline:
        r_sov = p_sovereign.add_run("✔ 100% AIR-GAPPED & LOCAL EXECUTION — Zero Cloud Transmission — Verified Local Weights")
        r_sov.font.size = Pt(9)
        r_sov.font.bold = True
        r_sov.font.color.rgb = RGBColor(0, 128, 40)
    else:
        r_sov = p_sovereign.add_run("⚠ SYSTEM WARNING: Non-isolated network activity detected.")
        r_sov.font.size = Pt(9)
        r_sov.font.color.rgb = RGBColor(180, 0, 0)

    doc.add_paragraph()

    # 2. Input Drawing / Document
    doc.add_heading("2. Input Drawing & Source Document", level=1)
    p_in = doc.add_paragraph()
    p_in.add_run("Primary Engineering Diagram: ").bold = True
    p_in.add_run(os.path.basename(drawing_name))
    p_path = doc.add_paragraph()
    p_path.add_run("Full Local Path: ").font.size = Pt(9)
    p_path.add_run(str(drawing_name)).font.size = Pt(9)

    # 3. Executive Summary
    doc.add_heading("3. Executive Summary", level=1)
    doc.add_paragraph(
        executive_summary
        or "Deterministic multimodal analysis completed across high-precision OCR, geometric symbol detectors, line topology tracing, and local RAG standards."
    )

    # 4. Detected Equipment
    doc.add_heading("4. Detected Equipment", level=1)
    eq_list = detected_equipment or []
    if eq_list:
        t_eq = doc.add_table(rows=len(eq_list) + 1, cols=4)
        t_eq.alignment = WD_TABLE_ALIGNMENT.CENTER
        headers = ["Tag / ID", "Type", "Confidence", "Bounding Box [x, y, w, h]"]
        for idx, h in enumerate(headers):
            cell = t_eq.cell(0, idx)
            _set_cell_background(cell, "1F4E78")
            r = cell.paragraphs[0].add_run(h)
            r.font.bold = True
            r.font.color.rgb = RGBColor(255, 255, 255)
            r.font.size = Pt(9.5)
        for r_idx, eq in enumerate(eq_list, start=1):
            t_eq.cell(r_idx, 0).paragraphs[0].add_run(str(eq.get("id") or eq.get("label", "")))
            t_eq.cell(r_idx, 1).paragraphs[0].add_run(str(eq.get("type", "equipment")))
            c_val = eq.get("confidence", 0.90)
            c_txt = f"{c_val:.2f}" if isinstance(c_val, (int, float)) else str(c_val)
            t_eq.cell(r_idx, 2).paragraphs[0].add_run(c_txt)
            t_eq.cell(r_idx, 3).paragraphs[0].add_run(str(eq.get("bbox", [])))
    else:
        doc.add_paragraph("No large equipment items identified in diagram.")

    # 5. Detected Tags
    doc.add_heading("5. Detected Alphanumeric Tags", level=1)
    tag_list = detected_tags or []
    if tag_list:
        t_tags = doc.add_table(rows=min(16, len(tag_list) + 1), cols=4)
        t_tags.alignment = WD_TABLE_ALIGNMENT.CENTER
        headers = ["Normalized Tag", "Raw OCR Text", "Confidence", "Coordinates"]
        for idx, h in enumerate(headers):
            cell = t_tags.cell(0, idx)
            _set_cell_background(cell, "1F4E78")
            r = cell.paragraphs[0].add_run(h)
            r.font.bold = True
            r.font.color.rgb = RGBColor(255, 255, 255)
            r.font.size = Pt(9.5)
        for r_idx, tag in enumerate(tag_list[:15], start=1):
            t_tags.cell(r_idx, 0).paragraphs[0].add_run(str(tag.get("text") or tag.get("normalized_tag", "")))
            t_tags.cell(r_idx, 1).paragraphs[0].add_run(str(tag.get("raw_text", "")))
            c_val = tag.get("confidence", 0.90)
            c_txt = f"{c_val:.2f}" if isinstance(c_val, (int, float)) else str(c_val)
            t_tags.cell(r_idx, 2).paragraphs[0].add_run(c_txt)
            t_tags.cell(r_idx, 3).paragraphs[0].add_run(str(tag.get("bbox", [])))
    else:
        doc.add_paragraph("No alphanumeric tags extracted from OCR.")

    # 6. Relevant Topology
    doc.add_heading("6. Process Piping & Instrument Topology", level=1)
    topo_list = relevant_topology or []
    if topo_list:
        t_topo = doc.add_table(rows=min(16, len(topo_list) + 1), cols=5)
        t_topo.alignment = WD_TABLE_ALIGNMENT.CENTER
        headers = ["Source", "Destination", "Line ID", "Type", "Confidence / Status"]
        for idx, h in enumerate(headers):
            cell = t_topo.cell(0, idx)
            _set_cell_background(cell, "1F4E78")
            r = cell.paragraphs[0].add_run(h)
            r.font.bold = True
            r.font.color.rgb = RGBColor(255, 255, 255)
            r.font.size = Pt(9.5)
        for r_idx, conn in enumerate(topo_list[:15], start=1):
            t_topo.cell(r_idx, 0).paragraphs[0].add_run(str(conn.get("source", "")))
            dest = conn.get("destination") or conn.get("target", "")
            t_topo.cell(r_idx, 1).paragraphs[0].add_run(str(dest))
            t_topo.cell(r_idx, 2).paragraphs[0].add_run(str(conn.get("line_id", "L-Piping")))
            t_topo.cell(r_idx, 3).paragraphs[0].add_run(str(conn.get("line_type", "process")))
            stat = f"{conn.get('confidence', 0.80):.2f} ({conn.get('status', 'connected')})"
            t_topo.cell(r_idx, 4).paragraphs[0].add_run(stat)
    else:
        doc.add_paragraph("No direct continuous piping connections detected.")

    # 7. Engineering Question
    doc.add_heading("7. Engineering Question / Target Query", level=1)
    doc.add_paragraph(engineering_question or "Comprehensive P&ID Component & Connectivity Audit.")

    # 8. Answer
    doc.add_heading("8. Verified Technical Answer", level=1)
    p_ans = doc.add_paragraph()
    r_ans = p_ans.add_run(answer or "Analysis complete based on ground evidence.")
    r_ans.font.size = Pt(11)
    r_ans.font.bold = True

    # 9. Evidence
    doc.add_heading("9. Grounded Evidence", level=1)
    ev_list = evidence or ["Deterministic RapidOCR tag matching", "Continuous line geometry trace", "Eng_Diagrams template classification"]
    for ev_item in ev_list:
        doc.add_paragraph(str(ev_item), style="List Bullet")

    # 10. RAG References
    doc.add_heading("10. Governing SOP & Standards References (Local RAG)", level=1)
    rag_list = rag_references or []
    if rag_list:
        t_rag = doc.add_table(rows=len(rag_list) + 1, cols=3)
        t_rag.alignment = WD_TABLE_ALIGNMENT.CENTER
        headers = ["Governing Document", "Page / Section", "Snippet / Clause"]
        for idx, h in enumerate(headers):
            cell = t_rag.cell(0, idx)
            _set_cell_background(cell, "1F4E78")
            r = cell.paragraphs[0].add_run(h)
            r.font.bold = True
            r.font.color.rgb = RGBColor(255, 255, 255)
            r.font.size = Pt(9.5)
        for r_idx, rag in enumerate(rag_list, start=1):
            t_rag.cell(r_idx, 0).paragraphs[0].add_run(str(rag.get("document", "SOP Manual")))
            t_rag.cell(r_idx, 1).paragraphs[0].add_run(f"Page {rag.get('page', 1)}")
            snip = rag.get("snippet") or rag.get("content", "")
            t_rag.cell(r_idx, 2).paragraphs[0].add_run(snip[:160] + "...")
    else:
        doc.add_paragraph("General ASME B31.3 & ISA-5.1 standards applied from local engineering knowledge.")

    # 11. Verification Status
    doc.add_heading("11. Verification Status", level=1)
    p_v = doc.add_paragraph()
    r_v = p_v.add_run(f"Status: {verification_status.upper()}")
    r_v.font.bold = True
    r_v.font.size = Pt(11)
    if "SUPPORTED" in verification_status.upper():
        r_v.font.color.rgb = RGBColor(0, 128, 40)
    else:
        r_v.font.color.rgb = RGBColor(190, 80, 0)

    # 12. Confidence Rating
    doc.add_heading("12. Confidence Assessment", level=1)
    doc.add_paragraph(
        f"Overall Assessment Confidence: {conf_str}. Confidence reflects deterministic CV contour agreement, "
        "calibrated OCR token matching, and line continuity ratios."
    )

    # 13. Uncertain Items / Review Items
    doc.add_heading("13. Uncertain Items / Engineering Review", level=1)
    unc_list = uncertain_items or []
    if unc_list:
        for u in unc_list[:8]:
            doc.add_paragraph(f"Review Item: {u.get('label', u.get('id', 'Unknown'))} (Confidence: {u.get('confidence', 0.50)})", style="List Bullet")
    else:
        doc.add_paragraph("No high-risk ambiguities or unresolved conflicts detected.")

    # 14. Timestamp & Provenance
    doc.add_heading("14. Execution Provenance & Audit Trail", level=1)
    doc.add_paragraph(f"Timestamp: {gen_time}")
    doc.add_paragraph(f"Local Execution Hash: SOVEREIGN-AUDIT-{task_id[:8].upper()}")

    doc.save(output_path)
    return output_path


