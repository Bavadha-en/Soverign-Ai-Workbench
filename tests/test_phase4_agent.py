import os
import sys
import io
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from docx import Document

# Ensure ConfigIQ root is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.main import app
from backend.agents.schemas import (
    AgentStatus,
    FactVerificationStatus,
    PlanStep,
    ToolDefinition,
    AgentRunRequest
)
from backend.agents.state import AgentState
from backend.agents.planner import Planner, planner
from backend.agents.tool_registry import ToolRegistry, tool_registry, Tool
from backend.agents.executor import ToolExecutor, executor
from backend.agents.verifier import Verifier, verifier
from backend.agents.agent import ConfigIQAgent, agent_orchestrator
from backend.sandbox.executor import SandboxExecutor, sandbox_executor
from backend.tools.word_tool import create_approval_note_docx
from backend.services.audit_service import audit_service
from backend.llm.model_router import model_router

client = TestClient(app)


# 1. AgentState Tracking & Serialization
def test_agent_state_lifecycle_and_serialization():
    state = AgentState(
        task_id="task_test_001",
        user_request="Analyze inspection report for valve CV-102",
        document_ids=["doc_valve_01"]
    )
    assert state.task_id == "task_test_001"
    assert state.status == AgentStatus.PLANNING
    assert state.current_step == 0
    assert len(state.execution_trace) == 0

    state.add_trace("[1] PLANNING - Created 6-step plan")
    assert len(state.execution_trace) == 1
    assert "[1] PLANNING" in state.execution_trace[0]

    state.record_step_result(
        step_idx=1,
        action="extract_document",
        tool_name="document_reader",
        result={"pages": 5, "text": "Inspection findings for CV-102"},
        success=True
    )
    assert state.current_step == 1
    assert len(state.completed_steps) == 1
    assert "extract_document" in state.tool_results

    # Serialization
    state_dict = state.to_dict()
    assert state_dict["task_id"] == "task_test_001"
    assert state_dict["status"] == "PLANNING"
    assert "extract_document" in state_dict["tool_results"]

    json_str = state.to_json()
    assert "task_test_001" in json_str


# 2. Planner & Structured Plan Generation
def test_planner_structured_plan():
    p = Planner()

    # Document inspection plan
    plan = p.plan("Analyze this inspection report and prepare an approval note", document_ids=["doc_123"])
    assert len(plan) == 6
    actions = [step["action"] for step in plan]
    tools = [step["tool"] for step in plan]

    assert "extract_document" in actions
    assert "analyze_scanned_pages" in actions
    assert "search_maintenance_sop" in actions
    assert "analyze_findings" in actions
    assert "verify_findings" in actions
    assert "generate_approval_note" in actions

    assert "document_reader" in tools
    assert "vision" in tools
    assert "rag_search" in tools
    assert "llm_generate" in tools
    assert "verification" in tools
    assert "document_generator" in tools

    # Calculation plan
    calc_plan = p.plan("Calculate pump efficiency using flow rate, head and power")
    assert len(calc_plan) >= 3
    calc_tools = [step["tool"] for step in calc_plan]
    assert "code_executor" in calc_tools
    assert "verification" in calc_tools


# 3. Tool Registry Registration & Lookup
def test_tool_registry():
    reg = ToolRegistry()
    tools = reg.list_tools()
    tool_names = [t.name for t in tools]

    expected_tools = [
        "document_reader", "pdf_processor", "ocr", "vision",
        "rag_search", "llm_generate", "code_executor",
        "document_generator", "verification"
    ]
    for et in expected_tools:
        assert et in tool_names, f"Expected tool '{et}' not found in registry."

    doc_tool = reg.get("document_reader")
    assert doc_tool is not None
    assert doc_tool.name == "document_reader"


# 4. Tool Execution & Audit Logging
@pytest.mark.asyncio
async def test_tool_execution_and_audit():
    initial_log_count = len(audit_service.get_logs())
    state = AgentState(
        task_id="task_exec_test",
        user_request="Perform RAG search on SOP",
        document_ids=[]
    )

    exec_inst = ToolExecutor()
    step_data = {
        "step": 1,
        "action": "search_sop",
        "tool": "rag_search",
        "params": {"query": "valve replacement", "top_k": 2}
    }

    step_res = await exec_inst.execute_step(1, step_data, state)
    assert step_res["status"] == "success"
    assert "search_sop" in state.tool_results
    assert len(state.execution_trace) == 1
    assert "RAG_SEARCH" in state.execution_trace[0]

    # Verify audit log was recorded
    current_logs = audit_service.get_logs()
    assert any(l.task_id == "task_exec_test" for l in current_logs)
    latest_log = [l for l in current_logs if l.task_id == "task_exec_test"][-1]
    assert latest_log.task_id == "task_exec_test"
    assert latest_log.action == "TOOL_RAG_SEARCH"
    assert latest_log.status == "SUCCESS"


# 5. Model Routing Integration
def test_model_routing_for_agent_tasks():
    # General inspection task
    route_gen = model_router.route("Analyze inspection findings and prepare approval note")
    assert route_gen["model"] == "llama3:latest"
    assert route_gen["task_type"] == "general"

    # Coding task
    route_code = model_router.route("Write Python code to calculate pump efficiency and head")
    assert route_code["model"] == "qwen2.5-coder:7b"
    assert route_code["task_type"] == "coding"

    # Heavy engineering simulation
    route_heavy = model_router.route("Run finite element analysis and numerical simulation for pipe stress")
    assert route_heavy["model"] == "qwen2.5-coder:14b"
    assert route_heavy["task_type"] == "coding_heavy"


# 6. RAG Tool Semantic Search
def test_rag_tool_execution():
    res = tool_registry.get("rag_search")
    assert res is not None

    import asyncio
    output = asyncio.run(tool_registry.execute("rag_search", query="corrosion and valve replacement", top_k=3))
    assert output["query"] == "corrosion and valve replacement"
    assert "results" in output
    assert "sources" in output


# 7. Vision Tool Structured Findings
@pytest.mark.asyncio
async def test_vision_tool_structured_findings():
    vision_tool = tool_registry.get("vision")
    assert vision_tool is not None

    res = await vision_tool.execute(prompt="Inspect corroded control valve CV-102 flange")
    assert res["status"] == "success"
    assert isinstance(res["observations"], list)
    assert len(res["observations"]) > 0
    assert res["confidence"] > 0.5
    assert res["defect_detected"] is True
    assert any("corrosion" in obs.lower() for obs in res["observations"])


# 8. Controlled Code Sandbox Execution
def test_code_sandbox_execution():
    sandbox = SandboxExecutor()
    valid_code = (
        "power_in = 11.0\n"
        "power_out = 8.5\n"
        "eff = (power_out / power_in) * 100\n"
        "print(f'Efficiency: {eff:.2f}%')\n"
    )
    result = sandbox.execute(valid_code, timeout_sec=5)
    assert result["status"] == "success"
    assert result["exit_code"] == 0
    assert "Efficiency: 77.27%" in result["stdout"]
    assert result["stderr"] == ""


# 9. Sandbox Timeout Handling
def test_code_sandbox_timeout():
    sandbox = SandboxExecutor()
    infinite_loop_code = "import time\nwhile True:\n    time.sleep(0.1)\n"
    result = sandbox.execute(infinite_loop_code, timeout_sec=1)
    assert result["status"] == "timeout"
    assert result["exit_code"] == -1
    assert "timed out" in result["stderr"].lower()


# 10. Sandbox Network Blocking
def test_code_sandbox_network_blocking():
    sandbox = SandboxExecutor()
    network_attempt_code = (
        "import socket\n"
        "try:\n"
        "    s = socket.socket()\n"
        "    s.connect(('1.1.1.1', 80))\n"
        "except Exception as e:\n"
        "    print(f'Blocked: {e}')\n"
    )
    result = sandbox.execute(network_attempt_code, timeout_sec=5)
    assert result["status"] == "success"
    assert "Blocked:" in result["stdout"]
    assert "Network access is strictly forbidden" in result["stdout"]


# 11. Fact Verifier (SUPPORTED, UNSUPPORTED, NEEDS REVIEW)
def test_verifier_fact_checking():
    context = [
        {
            "content": "SOP-M-402 mandates replacement of control valve CV-102 with 316L stainless steel when wall loss exceeds 30%.",
            "metadata": {"document": "SOP-M-402.pdf", "page": 3}
        }
    ]

    claims = [
        "Control valve CV-102 requires 316L stainless steel replacement per SOP-M-402.", # Supported
        "The valve operates on helium gas inside nuclear reactor.",                     # Unsupported
        "Standard maintenance."                                                         # Needs review / generic
    ]

    summary = verifier.verify_facts(claims, context)
    assert summary.total_claims == 3
    assert summary.supported_claims >= 1
    assert summary.unsupported_claims >= 1

    statuses = [c.status for c in summary.claims]
    assert FactVerificationStatus.SUPPORTED in statuses
    assert FactVerificationStatus.UNSUPPORTED in statuses


# 12. Calculation Verifier
def test_verifier_calculation():
    # Success case
    good_res = {"status": "success", "stdout": "Pump Hydraulic Efficiency: 72.50%\n", "stderr": "", "exit_code": 0}
    v_good = verifier.verify_calculation(good_res)
    assert v_good["is_valid"] is True
    assert v_good["status"] == "PASSED"

    # Error case
    bad_res = {"status": "error", "stdout": "", "stderr": "ZeroDivisionError: division by zero", "exit_code": 1}
    v_bad = verifier.verify_calculation(bad_res)
    assert v_bad["is_valid"] is False
    assert v_bad["status"] == "FAILED"


# 13. Retry Mechanism & Retry Limit
@pytest.mark.asyncio
async def test_agent_retry_mechanism_and_limit():
    agent = ConfigIQAgent()

    state = AgentState(
        task_id="task_retry_test",
        user_request="Calculate pump efficiency",
        max_retries=3
    )

    action = "execute_in_sandbox"
    assert state.can_retry(action) is True
    assert state.get_retry_count(action) == 0

    state.increment_retry_count(action)
    state.increment_retry_count(action)
    assert state.can_retry(action) is True

    state.increment_retry_count(action)
    assert state.get_retry_count(action) == 3
    assert state.can_retry(action) is False # Max retries reached


# 14. Approval Note Word (.docx) Generation
def test_approval_note_generation():
    test_docx_path = os.path.join("outputs", "test_Approval_Note.docx")
    if os.path.exists(test_docx_path):
        os.remove(test_docx_path)

    saved_path = create_approval_note_docx(
        output_path=test_docx_path,
        task_id="test_task_docx_999",
        reference_document="Inspection_Report_CV102.pdf",
        executive_summary="Critical wall loss identified on CV-102; replacement required.",
        inspection_findings=["36% wall loss measured via UT.", "Flange corrosion severity high."],
        sop_references=["SOP-M-402: Section 3 Disassembly & Isolation"],
        risk_severity="HIGH",
        recommended_actions=["Isolate and replace valve."],
        approval_recommendation="APPROVED FOR WORK ORDER",
        sources=[{"document": "SOP-M-402.pdf", "page": 2, "score": 0.94}],
        is_synthetic_demo=True
    )

    assert os.path.exists(saved_path)
    doc = Document(saved_path)
    paragraphs = [p.text for p in doc.paragraphs if p.text]
    full_text = " ".join(paragraphs)

    # Check 8 required sections
    assert "Inspection Report Review & Approval Note" in full_text
    assert "1. Reference Document" in full_text
    assert "2. Executive Summary" in full_text
    assert "3. Inspection Findings" in full_text
    assert "4. SOP / Manual References" in full_text
    assert "5. Risk / Severity Assessment" in full_text
    assert "6. Recommended Actions" in full_text
    assert "7. Approval Recommendation" in full_text
    assert "8. Verified Sources & Knowledge Provenance" in full_text
    assert "CV-102" in full_text


# 15. Agent API Endpoints (/agent/run, /agent/{task_id}, /agent/tools)
def test_agent_api_endpoints():
    # 1. List tools
    tools_resp = client.get("/agent/tools")
    assert tools_resp.status_code == 200
    tools_data = tools_resp.json()
    assert len(tools_data) >= 8

    # 2. Run agent task
    run_resp = client.post("/agent/run", json={
        "task": "Analyze inspection report and prepare an approval note",
        "document_ids": ["doc_sample_101"]
    })
    assert run_resp.status_code == 200
    run_data = run_resp.json()
    assert "task_id" in run_data
    assert run_data["status"] == "completed"
    assert run_data["steps_completed"] >= 5
    assert run_data["local"] is True
    assert len(run_data["execution_trace"]) >= 5
    assert len(run_data["generated_files"]) >= 1

    task_id = run_data["task_id"]

    # 3. Get agent state
    state_resp = client.get(f"/agent/{task_id}")
    assert state_resp.status_code == 200
    state_data = state_resp.json()
    assert state_data["task_id"] == task_id
    assert state_data["status"] == "COMPLETED"
    assert "extract_document" in state_data["tool_results"]


# 16. End-to-End Primary Demo Workflow: Inspection Report -> Approval Note .docx
@pytest.mark.asyncio
async def test_primary_demo_inspection_to_docx():
    agent = ConfigIQAgent()
    state = await agent.run(
        task="Analyze this inspection report for control valve CV-102 and prepare an approval note.",
        document_ids=["doc_valve_inspection_report"]
    )

    assert state.status == AgentStatus.COMPLETED
    assert len(state.completed_steps) == 6
    assert len(state.generated_files) > 0

    docx_path = state.generated_files[0]
    assert os.path.exists(docx_path)
    assert "Approval_Note_" in docx_path

    # Verify trace steps
    trace_text = "\n".join(state.execution_trace)
    assert "[1] PLANNING" in trace_text
    assert "DOCUMENT_READER" in trace_text
    assert "VISION" in trace_text
    assert "RAG_SEARCH" in trace_text
    assert "LLM_GENERATE" in trace_text
    assert "VERIFICATION" in trace_text
    assert "DOCUMENT_GENERATOR" in trace_text
    assert "COMPLETED" in trace_text


# 17. End-to-End Secondary Demo Workflow: Engineering Calculation in Sandbox
@pytest.mark.asyncio
async def test_secondary_demo_engineering_calculation():
    agent = ConfigIQAgent()
    state = await agent.run(
        task="Calculate pump efficiency using flow rate of 50 m3/h, head of 60 m, and power of 11 kW."
    )

    assert state.status == AgentStatus.COMPLETED
    assert len(state.completed_steps) >= 3
    assert "execute_in_sandbox" in state.tool_results

    sandbox_res = state.tool_results["execute_in_sandbox"]
    assert sandbox_res["status"] == "success"
    assert sandbox_res["exit_code"] == 0
    assert "Efficiency" in sandbox_res["stdout"]
    assert state.final_output is not None
    assert "Engineering Calculation Result" in state.final_output
    # The summary must report the verifier's real verdict, never a fixed "passed".
    assert "- **Verification**:" in state.final_output
    verdict_line = next(
        line for line in state.final_output.splitlines() if line.startswith("- **Verification**:")
    )
    assert any(
        marker in verdict_line
        for marker in ("Passed physical range", "Requires engineer review", "Not accepted")
    ), verdict_line
