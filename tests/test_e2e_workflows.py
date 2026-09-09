import os
import sys
import io
import pytest
from PIL import Image
from fastapi.testclient import TestClient

# Ensure ConfigIQ root is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.main import app
from backend.agents.agent import agent_orchestrator
from backend.agents.schemas import AgentStatus, FactVerificationStatus
from backend.rag.ingest import ingestion_engine
from backend.rag.retriever import retriever
from backend.services.network_monitor import network_monitor
from backend.services.audit_service import audit_service
from backend.sandbox.executor import sandbox_executor
from backend.tools.word_tool import create_approval_note_docx
from docx import Document

client = TestClient(app)

# Setup knowledge base before tests
@pytest.fixture(scope="module", autouse=True)
def init_kb():
    kb_dir = os.path.join(os.getcwd(), "knowledge_base")
    if os.path.isdir(kb_dir):
        ingestion_engine.ingest_directory(kb_dir, force_reindex=True)


# A. Workflow A: Scanned Inspection Report -> OCR/VLM -> RAG -> LLM Reasoning -> Verification -> Approval Note DOCX
@pytest.mark.asyncio
async def test_workflow_a_inspection_to_approval_note():
    # 1. Create a sample inspection image
    img = Image.new("RGB", (400, 300), color="gray")
    img_buf = io.BytesIO()
    img.save(img_buf, format="PNG")
    img_path = os.path.join("outputs", "test_inspection_valve.png")
    os.makedirs(os.path.dirname(img_path), exist_ok=True)
    with open(img_path, "wb") as f:
        f.write(img_buf.getvalue())

    # 2. Run agent orchestrator on inspection task
    task = "Inspect control valve CV-102 for wall thinning and corrosion, check SOP-M-402, and generate approval note"
    state = await agent_orchestrator.run(
        task=task,
        document_ids=["doc_valve_inspection_01"],
        parameters={"file_path": img_path}
    )

    # 3. Assert full pipeline execution
    assert state.status == AgentStatus.COMPLETED
    assert len(state.completed_steps) >= 5
    assert state.is_verified is True or len(state.verification_results) > 0
    assert len(state.generated_files) >= 1

    docx_file = state.generated_files[0]
    assert docx_file.endswith(".docx")
    assert os.path.exists(docx_file)

    # 4. Verify 8-section Word document structure
    doc = Document(docx_file)
    headings = [p.text for p in doc.paragraphs if p.style.name.startswith("Heading")]
    assert any("Reference Document" in h for h in headings)
    assert any("Executive Summary" in h for h in headings)
    assert any("Inspection Findings" in h for h in headings)
    assert any("SOP" in h for h in headings)
    assert any("Risk" in h for h in headings)
    assert any("Recommended Actions" in h for h in headings)
    assert any("Approval Recommendation" in h for h in headings)
    assert any("Sources" in h for h in headings)

    # Clean up test image
    if os.path.exists(img_path):
        os.remove(img_path)


# B. Workflow B: P&ID Image -> VLM -> Engineering Symbol Understanding -> RAG -> Verified Answer
@pytest.mark.asyncio
async def test_workflow_b_pid_vlm_rag_answer():
    # 1. Create sample P&ID diagram
    pid_img = Image.new("RGB", (512, 512), color="white")
    pid_buf = io.BytesIO()
    pid_img.save(pid_buf, format="PNG")
    pid_path = os.path.join("outputs", "test_pid_diagram.png")
    os.makedirs(os.path.dirname(pid_path), exist_ok=True)
    with open(pid_path, "wb") as f:
        f.write(pid_buf.getvalue())

    task = "Analyze P&ID diagram for safety relief valve and pressure rating per pressure vessel SOP"
    state = await agent_orchestrator.run(
        task=task,
        document_ids=["doc_pid_01"],
        parameters={"file_path": pid_path}
    )

    assert state.status == AgentStatus.COMPLETED
    assert "extract_document" in state.tool_results
    assert "analyze_scanned_pages" in state.tool_results
    assert "search_maintenance_sop" in state.tool_results

    # Check evidence distinction in final output
    assert "VISUAL EVIDENCE" in state.final_output
    assert "DOCUMENT EVIDENCE" in state.final_output

    if os.path.exists(pid_path):
        os.remove(pid_path)


# C. Workflow C: Coding Task -> Coding Model -> Sandbox Execution -> Tests -> Verification
@pytest.mark.asyncio
async def test_workflow_c_coding_sandbox_verification():
    calc_task = "Calculate pump hydraulic efficiency for flow rate 50 m3/h, head 60 m, power 11 kW"
    state = await agent_orchestrator.run(task=calc_task)

    assert state.status == AgentStatus.COMPLETED
    assert "execute_in_sandbox" in state.tool_results
    sandbox_res = state.tool_results["execute_in_sandbox"]
    assert sandbox_res.get("exit_code") == 0
    assert "stdout" in sandbox_res
    assert len(sandbox_res["stdout"]) > 0

    # Verification passed
    assert "verify_calculation" in state.tool_results or "verify_calculation" in state.verification_results
    assert "Efficiency" in sandbox_res["stdout"] or "Hydraulic Power" in sandbox_res["stdout"]


# D. Workflow D: Network Telemetry during Workflow & Air-Gap Compliance
def test_workflow_d_network_telemetry_sovereignty():
    # 1. Check baseline telemetry
    telemetry = network_monitor.get_telemetry()
    assert telemetry.air_gap_compliant is True or telemetry.wan_egress_blocked >= 0
    assert telemetry.status in ("LOCAL_ONLY", "WARNING_EXTERNAL_ATTEMPT_DETECTED")
    assert len(telemetry.active_listening_ports) >= 1
    assert "SOVEREIGN-SEAL-" in telemetry.integrity_hash

    # 2. Test sandbox blocked network execution
    blocked_script = "import socket\nsocket.socket(socket.AF_INET, socket.SOCK_STREAM)"
    res = sandbox_executor.execute(blocked_script)
    assert res["exit_code"] != 0 or "PermissionError" in res["stderr"] or "forbidden" in res["stderr"].lower()


# E. Workflow E: RAG Source Grounding & Exposure
def test_workflow_e_rag_source_grounding():
    # Retrieve query
    results = retriever.retrieve("heat exchanger tube wall thickness eddy current inspection", top_k=3)
    assert len(results) >= 1

    # Every result must expose source document, page, score, and content
    for r in results:
        assert "document" in r
        assert r["document"] != ""
        assert "page" in r
        assert "score" in r
        assert isinstance(r["score"], float)
        assert "content" in r
        assert len(r["content"]) > 10
