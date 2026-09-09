import os
import time
from typing import Optional, Dict, Any
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from backend.models.schemas import CreateWordOutput
from backend.services.audit_service import audit_service


def _set_cell_background(cell, hex_color: str):
    """Utility helper to set table cell shading color."""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex_color)
    tcPr.append(shd)


def create_word(
    output_path: str,
    title: str,
    sections: Dict[str, str],
    subject: Optional[str] = None,
    task_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generates a Word (.docx) document (e.g. Approval Note or technical report) using python-docx.
    Logs action to audit_service.
    """
    start_time = time.time()
    try:
        dir_name = os.path.dirname(output_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

        doc = Document()

        # Document Header / Title
        heading = doc.add_heading(level=0)
        heading.alignment = WD_ALIGN_PARAGRAPH.LEFT
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
