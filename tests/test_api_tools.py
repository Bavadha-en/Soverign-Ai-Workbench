import os
import sys
import pytest
from fastapi.testclient import TestClient

# Ensure ConfigIQ root is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.main import app

client = TestClient(app)


def test_api_file_tools(tmp_path):
    file_path = str(tmp_path / "api_test.txt")
    write_resp = client.post("/tools/file/write", json={"path": file_path, "content": "API Tool Content"})
    assert write_resp.status_code == 200
    assert write_resp.json()["success"] is True

    read_resp = client.post("/tools/file/read", json={"path": file_path})
    assert read_resp.status_code == 200
    assert read_resp.json()["content"] == "API Tool Content"


def test_api_python_tool():
    resp = client.post("/tools/python/execute", json={"code": "print('API Python Execution')", "timeout_sec": 5})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "API Python Execution" in data["stdout"]


def test_api_approval_note(tmp_path):
    output_docx = str(tmp_path / "API_Approval_Note.docx")
    payload = {
        "output_path": output_docx,
        "title": "API APPROVAL NOTE",
        "subject": "Equipment Valve Replacement Approval",
        "background": "Inspection found corrosion.",
        "inspection_findings": "Wall thickness reduced.",
        "technical_assessment": "High risk of failure.",
        "applicable_sop": "SOP-MECH-44",
        "recommended_action": "Replace valve.",
        "approval_requested": "Procurement authorization."
    }
    resp = client.post("/tools/word/approval-note", json=payload)
    assert resp.status_code == 200
    assert resp.json()["success"] is True
    assert os.path.exists(output_docx)


def test_api_excel_create(tmp_path):
    output_xlsx = str(tmp_path / "API_Report.xlsx")
    payload = {
        "output_path": output_xlsx,
        "data": [{"Item": "Valve", "Qty": 2, "Status": "OK"}],
        "sheet_name": "API Sheet"
    }
    resp = client.post("/tools/excel/create", json=payload)
    assert resp.status_code == 200
    assert resp.json()["success"] is True
    assert os.path.exists(output_xlsx)
