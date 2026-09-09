import os
import sys
import pytest
from typing import Dict, Any

# Ensure ConfigIQ root is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.tools import (
    read_file,
    write_file,
    extract_pdf,
    perform_ocr,
    search_knowledge,
    execute_python,
    create_word,
    create_excel
)
from backend.sandbox.executor import SandboxExecutor
from backend.services.audit_service import audit_service


def test_file_tool(tmp_path):
    test_file = str(tmp_path / "sample.txt")
    content = "Confidential Industrial Specification 2026"

    # Test write_file
    write_res = write_file(test_file, content, task_id="task_test_1")
    assert write_res["success"] is True
    assert write_res["path"] == test_file
    assert write_res["bytes_written"] == len(content.encode("utf-8"))

    # Test read_file
    read_res = read_file(test_file, task_id="task_test_1")
    assert read_res["success"] is True
    assert read_res["content"] == content
    assert read_res["file_size"] == len(content)

    # Test read_file failure for missing file
    missing_res = read_file(str(tmp_path / "nonexistent.txt"))
    assert missing_res["success"] is False
    assert missing_res["error"] is not None


def test_pdf_tool(tmp_path):
    # Test missing PDF file error handling
    missing_pdf = extract_pdf(str(tmp_path / "missing.pdf"), task_id="task_pdf_1")
    assert missing_pdf["success"] is False
    assert "not found" in missing_pdf["error"]

    # Test dummy PDF processing
    pdf_file = str(tmp_path / "test.pdf")
    with open(pdf_file, "wb") as f:
        f.write(b"%PDF-1.4 Mock PDF Data")

    extract_res = extract_pdf(pdf_file, task_id="task_pdf_2")
    assert extract_res["success"] is True
    assert extract_res["file_path"] == pdf_file


def test_ocr_tool(tmp_path):
    # Test missing image file
    missing_img = perform_ocr(str(tmp_path / "missing.png"), task_id="task_ocr_1")
    assert missing_img["success"] is False
    assert "not found" in missing_img["error"]

    # Test valid image file
    img_file = str(tmp_path / "sample.png")
    with open(img_file, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\nFake ImageData")

    ocr_res = perform_ocr(img_file, task_id="task_ocr_2")
    assert ocr_res["success"] is True
    assert "image_path" in ocr_res


def test_rag_tool():
    res = search_knowledge(query="corroded valve procedure", top_k=3, task_id="task_rag_1")
    assert res["success"] is True
    assert res["query"] == "corroded valve procedure"
    assert isinstance(res["results"], list)


def test_sandbox_executor():
    executor = SandboxExecutor(timeout_sec=5)

    # Test standard execution
    code = "print('ConfigIQ Sandbox Active'); x = 10 + 20; print(f'Result: {x}')"
    res = executor.execute(code)
    assert res["success"] is True
    assert "ConfigIQ Sandbox Active" in res["stdout"]
    assert "Result: 30" in res["stdout"]
    assert res["exit_code"] == 0

    # Test execution with error
    err_code = "raise ValueError('Industrial Safety Limit Exceeded')"
    err_res = executor.execute(err_code)
    assert err_res["success"] is False
    assert err_res["exit_code"] != 0
    assert "Industrial Safety Limit Exceeded" in err_res["stderr"]

    # Test execution timeout
    timeout_code = "import time; time.sleep(10)"
    executor_short = SandboxExecutor(timeout_sec=1)
    timeout_res = executor_short.execute(timeout_code)
    assert timeout_res["success"] is False
    assert "timed out" in timeout_res["stderr"].lower()


def test_python_tool():
    code = "import math; print(math.sqrt(144))"
    res = execute_python(code, task_id="task_py_1")
    assert res["success"] is True
    assert "12.0" in res["stdout"]
    assert res["exit_code"] == 0


def test_word_tool(tmp_path):
    output_docx = str(tmp_path / "Approval_Note.docx")
    title = "APPROVAL NOTE FOR VALVE REPLACEMENT"
    subject = "Corroded Valve CV-102 Repair Approval"
    sections = {
        "1. Background": "Inspection on 2026-09-08 identified severe surface corrosion on CV-102.",
        "2. Inspection Findings": "Wall thickness reduced below minimum threshold. Replacement required.",
        "3. Technical Assessment": "Valve replacement is critical to maintain pressure containment.",
        "4. Applicable SOP": "SOP-MECH-44: High Pressure Valve Servicing.",
        "5. Recommended Action": "Replace CV-102 during scheduled maintenance window.",
        "6. Approval Requested": "Immediate approval to order replacement assembly."
    }

    res = create_word(
        output_path=output_docx,
        title=title,
        sections=sections,
        subject=subject,
        task_id="task_word_1"
    )

    assert res["success"] is True
    assert res["output_path"] == output_docx
    assert res["file_size"] > 0
    assert os.path.exists(output_docx)


def test_excel_tool(tmp_path):
    output_xlsx = str(tmp_path / "Inspection_Summary.xlsx")
    data = [
        {"Component_ID": "CV-101", "Status": "PASS", "Thickness_mm": 12.5, "Corrosion": "None"},
        {"Component_ID": "CV-102", "Status": "ACTION REQUIRED", "Thickness_mm": 4.2, "Corrosion": "Severe"},
        {"Component_ID": "CV-103", "Status": "PASS", "Thickness_mm": 11.8, "Corrosion": "Minor"}
    ]

    res = create_excel(
        output_path=output_xlsx,
        data=data,
        sheet_name="Inspection Audit",
        task_id="task_excel_1"
    )

    assert res["success"] is True
    assert res["output_path"] == output_xlsx
    assert res["rows_written"] == 3
    assert res["file_size"] > 0
    assert os.path.exists(output_xlsx)


def test_audit_logs_for_tools():
    # Verify that tool executions generated audit log entries
    logs = audit_service.get_logs()
    actions = [l.action for l in logs]
    assert "READ_FILE" in actions or "WRITE_FILE" in actions
    assert "EXECUTE_PYTHON" in actions
    assert "CREATE_WORD" in actions
    assert "CREATE_EXCEL" in actions
