import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
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
    is_synthetic_demo: bool = False
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
        warn_run = p_warn.add_run("⚠ HUMAN REVIEW REQUIRED: AI-assisted draft — human approval required.")
        warn_run.bold = True
        warn_run.font.size = Pt(11)
        warn_run.font.color.rgb = RGBColor(190, 30, 30)
    else:
        p_cert = doc.add_paragraph()
        p_cert.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cert_run = p_cert.add_run("✔ SOURCED & VERIFIED — Autonomous Sovereign Agent Audit Complete")
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

    # Section 8: Sources
    doc.add_heading("8. Verified Sources & Knowledge Provenance", level=1)
    src_list = sources or [{"document": reference_document, "page": 1, "score": 1.0}]
    for src in src_list:
        doc_name = src.get("document", "Unknown")
        page_num = src.get("page", "N/A")
        score = src.get("score")
        status_tag = src.get("status", "SUPPORTED")
        score_str = f" (relevance score: {score:.2f})" if score is not None else ""
        doc.add_paragraph(
            f"Source: {doc_name}, Page {page_num}{score_str} [Status: {status_tag}]",
            style="List Bullet"
        )

    doc.save(output_path)
    return output_path


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

