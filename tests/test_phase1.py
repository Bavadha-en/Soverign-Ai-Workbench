import io
import sys
import os
import pytest
from fastapi.testclient import TestClient

# Ensure ConfigIQ root is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["system"] == "ConfigIQ"
    assert data["mode"] == "100% Offline / Air-Gapped"


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app_name"] == "ConfigIQ Backend"
    assert "timestamp" in data


def test_document_upload_and_get():
    file_content = b"%PDF-1.4 Mock PDF Content for Industrial Inspection Report"
    file_tuple = ("test_report.pdf", io.BytesIO(file_content), "application/pdf")

    upload_resp = client.post("/documents/upload", files={"file": file_tuple})
    assert upload_resp.status_code == 201
    upload_data = upload_resp.json()
    assert "document_id" in upload_data
    assert upload_data["filename"] == "test_report.pdf"
    assert upload_data["source"] == "local"

    doc_id = upload_data["document_id"]

    get_resp = client.get(f"/documents/{doc_id}")
    assert get_resp.status_code == 200
    get_data = get_resp.json()
    assert get_data["document_id"] == doc_id
    assert get_data["file_size"] == len(file_content)


def test_knowledge_base_endpoints():
    ingest_resp = client.post("/knowledge/ingest", json={"directory_path": "knowledge_base", "force_reindex": False})
    assert ingest_resp.status_code == 200
    assert ingest_resp.json()["status"] == "success"

    search_resp = client.post("/knowledge/search", json={"query": "corroded valve procedure", "top_k": 3})
    assert search_resp.status_code == 200
    search_data = search_resp.json()
    assert search_data["query"] == "corroded valve procedure"
    assert len(search_data["results"]) > 0


def test_task_endpoints():
    create_resp = client.post("/tasks", json={"description": "Analyze inspection report and SOP"})
    assert create_resp.status_code == 201
    task_data = create_resp.json()
    assert "task_id" in task_data
    assert task_data["status"] == "pending"

    task_id = task_data["task_id"]
    get_resp = client.get(f"/tasks/{task_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["task_id"] == task_id


def test_chat_mock_llm():
    chat_resp = client.post("/chat/generate", json={"prompt": "Analyze inspection findings for CV-102"})
    assert chat_resp.status_code == 200
    chat_data = chat_resp.json()
    assert "text" in chat_data
    assert chat_data["model"] == "mock-open-weight-industrial-v1"


def test_logs_and_network_sovereignty():
    logs_resp = client.get("/logs")
    assert logs_resp.status_code == 200
    assert "logs" in logs_resp.json()

    net_resp = client.get("/network/status")
    assert net_resp.status_code == 200
    net_data = net_resp.json()
    assert net_data["status"] == "LOCAL_ONLY"
    assert net_data["internet_required"] is False
    assert net_data["external_ai_calls"] == 0
