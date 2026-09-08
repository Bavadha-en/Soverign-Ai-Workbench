import os
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
    is_synthetic_demo: bool = False
) -> str:
    """
    Generate an official Inspection Report Review & Approval Note as a Word (.docx) document.
    Structure:
      1. Reference Document
      2. Executive Summary
      3. Inspection Findings
      4. SOP/Manual References
      5. Risk/Severity
      6. Recommended Actions
      7. Approval Recommendation
      8. Sources
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc = Document()

    # Document Title
    title = doc.add_heading("Inspection Report Review & Approval Note", level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Subtitle / Metadata Table
    p_meta = doc.add_paragraph()
    p_meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    meta_run = p_meta.add_run(f"Task ID: {task_id}  |  Classification: Confidential / Sovereign Industrial Workbench")
    meta_run.font.size = Pt(9)
    meta_run.font.color.rgb = RGBColor(100, 100, 100)

    if is_synthetic_demo:
        p_demo = doc.add_paragraph()
        demo_run = p_demo.add_run("[DEMO NOTE: Synthetic evaluation data based on local industrial dataset]")
        demo_run.font.italic = True
        demo_run.font.size = Pt(9)
        demo_run.font.color.rgb = RGBColor(180, 50, 50)

    doc.add_paragraph() # Spacer

    # Section 1: Reference Document
    doc.add_heading("1. Reference Document", level=1)
    p1 = doc.add_paragraph(f"Primary Document: {reference_document}")
    p1.paragraph_format.left_indent = Inches(0.2)

    # Section 2: Executive Summary
    doc.add_heading("2. Executive Summary", level=1)
    p2 = doc.add_paragraph(executive_summary or "Autonomous inspection review completed successfully via ConfigIQ sovereign AI pipeline.")
    p2.paragraph_format.left_indent = Inches(0.2)

    # Section 3: Inspection Findings
    doc.add_heading("3. Inspection Findings", level=1)
    findings = inspection_findings or ["No anomalous inspection items recorded."]
    for f in findings:
        doc.add_paragraph(f, style="List Bullet")

    # Section 4: SOP/Manual References
    doc.add_heading("4. SOP / Manual References", level=1)
    sops = sop_references or ["Standard Maintenance Guidelines (General)"]
    for s in sops:
        doc.add_paragraph(s, style="List Bullet")

    # Section 5: Risk/Severity
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

    # Section 8: Sources
    doc.add_heading("8. Verified Sources & Knowledge Provenance", level=1)
    src_list = sources or [{"document": reference_document, "page": 1, "score": 1.0}]
    for src in src_list:
        doc_name = src.get("document", "Unknown")
        page_num = src.get("page", "N/A")
        score = src.get("score")
        score_str = f" (relevance score: {score:.2f})" if score is not None else ""
        doc.add_paragraph(f"Source: {doc_name}, Page {page_num}{score_str}", style="List Bullet")

    doc.save(output_path)
    return output_path


def create_word(output_path: str, title: str, sections: dict) -> str:
    """Generic Word document creator for backward compatibility."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc = Document()
    doc.add_heading(title, level=0)
    for section_title, content in sections.items():
        doc.add_heading(section_title, level=1)
        if isinstance(content, list):
            for item in content:
                doc.add_paragraph(str(item), style="List Bullet")
        else:
            doc.add_paragraph(str(content))
    doc.save(output_path)
    return output_path
