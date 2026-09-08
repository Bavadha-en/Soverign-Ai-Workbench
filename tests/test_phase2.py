import asyncio
import os
import sys
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

# Ensure ConfigIQ root is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.main import app
from backend.config import is_local_url, settings
from backend.llm.mock_provider import MockLLMProvider
from backend.llm.ollama_provider import OllamaLLMProvider
from backend.llm.model_router import ModelRouter, model_router
from backend.llm.registry import ModelRegistry, model_registry
from backend.models.schemas import LLMGenerateRequest
from backend.services.audit_service import audit_service

client = TestClient(app)


# 1. Local URL Validation & Network Sovereignty
def test_local_url_validation():
    """Verify that only local/localhost URLs are permitted for sovereign inference."""
    assert is_local_url("http://localhost:11434") is True
    assert is_local_url("http://127.0.0.1:11434") is True
    assert is_local_url("http://0.0.0.0:8000") is True
    assert is_local_url("http://[::1]:11434") is True

    # External URLs must be rejected
    assert is_local_url("https://api.openai.com/v1") is False
    assert is_local_url("https://api.anthropic.com") is False
    assert is_local_url("http://cloud-inference.example.com") is False
    assert is_local_url("http://192.168.1.50:11434") is False
    assert is_local_url("") is False


def test_ollama_provider_rejects_external_url():
    """Verify that OllamaLLMProvider strictly blocks non-local URLs and audits the event."""
    initial_violations = audit_service.get_external_attempts_count()

    with pytest.raises(ValueError) as exc_info:
        OllamaLLMProvider(base_url="https://api.openai.com/v1")

    assert "Network sovereignty violation" in str(exc_info.value)
    assert audit_service.get_external_attempts_count() == initial_violations + 1


# 2. Model Registry & Availability Detection
def test_model_registry_verification():
    """Verify model registry detects available and missing models cleanly."""
    registry = ModelRegistry()
    installed = ["qwen2.5-coder:7b", "qwen2.5-coder:14b", "llama3:latest"]

    status = registry.verify_availability(installed)
    assert status["coding"] is True
    assert status["coding_heavy"] is True
    assert status["general"] is True
    assert status["embedding"] is False  # nomic-embed-text missing
    assert status["vision"] is False     # vision model missing


# 3. Deterministic Model Router Tests
def test_model_router_decisions():
    """Verify deterministic routing across coding, heavy coding, general, and vision tasks."""
    router = ModelRouter()

    # Coding task
    r_code = router.route("Write Python code to calculate pump efficiency.")
    assert r_code["task_type"] == "coding"
    assert r_code["model"] == "qwen2.5-coder:7b"

    # Heavy calculation / complex coding
    r_heavy = router.route("Write a complex engineering calculation program with finite element analysis.")
    assert r_heavy["task_type"] == "coding_heavy"
    assert r_heavy["model"] == "qwen2.5-coder:14b"

    # General reasoning / documentation
    r_general = router.route("Explain what a pressure relief valve does and draft maintenance SOP.")
    assert r_general["task_type"] == "general"
    assert r_general["model"] == "llama3:latest"

    # Visual inspection / image analysis
    r_vision = router.route("Perform visual inspection on scanned image diagram.")
    assert r_vision["task_type"] == "vision"


# 4. Mock LLM Provider Verification
def test_mock_llm_provider():
    """Verify MockLLMProvider works for offline unit tests and development."""
    provider = MockLLMProvider()

    async def _run():
        req = LLMGenerateRequest(prompt="Analyze inspection report for CV-102")
        resp = await provider.generate(req)
        assert "Critical Finding" in resp.text
        assert resp.model == "mock-open-weight-industrial-v1"

        structured = await provider.generate_structured("Analyze valve", {"type": "object"})
        assert structured["status"] == "success"
        assert "findings" in structured

        healthy = await provider.health_check()
        assert healthy is True

    asyncio.run(_run())


# 5. Ollama Provider with Mocked HTTP Client (CI/Offline Isolation)
def test_ollama_provider_generate_mocked():
    """Verify Ollama provider generate workflow using mocked HTTP transport."""
    provider = OllamaLLMProvider(base_url="http://localhost:11434")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "model": "qwen2.5-coder:7b",
        "response": "def calculate_pump_efficiency(power_in, power_out):\n    return (power_out / power_in) * 100",
        "prompt_eval_count": 12,
        "eval_count": 28
    }

    async def _run():
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
            req = LLMGenerateRequest(
                prompt="Write Python code to calculate pump efficiency",
                model="qwen2.5-coder:7b"
            )
            resp = await provider.generate(req)
            assert "calculate_pump_efficiency" in resp.text
            assert resp.model == "qwen2.5-coder:7b"
            assert resp.usage["prompt_tokens"] == 12
            assert resp.usage["completion_tokens"] == 28

    asyncio.run(_run())


# 6. Ollama Structured Output Generation
def test_ollama_provider_structured_output():
    """Verify structured output parsing with schema and fallback handling."""
    provider = OllamaLLMProvider(base_url="http://localhost:11434")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "response": '{"equipment": "CV-102", "status": "corroded", "risk_level": "HIGH"}'
    }

    schema = {
        "type": "object",
        "properties": {
            "equipment": {"type": "string"},
            "status": {"type": "string"},
            "risk_level": {"type": "string"}
        }
    }

    async def _run():
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_resp):
            res = await provider.generate_structured("Analyze valve CV-102", schema)
            assert res["equipment"] == "CV-102"
            assert res["risk_level"] == "HIGH"

    asyncio.run(_run())


# 7. Ollama Safe Parsing with Markdown Code Blocks
def test_safe_parse_json_markdown():
    provider = OllamaLLMProvider(base_url="http://localhost:11434")
    text_with_codeblock = "Here is the result:\n```json\n{\"valve\": \"P-101\", \"pressure\": 45.2}\n```"
    parsed = provider._safe_parse_json(text_with_codeblock)
    assert parsed["valve"] == "P-101"
    assert parsed["pressure"] == 45.2

    # Malformed text
    invalid_text = "This is not json at all."
    failed_parse = provider._safe_parse_json(invalid_text)
    assert failed_parse["status"] == "error"
    assert failed_parse["raw_output"] == invalid_text


# 8. Chat Route API Endpoint
def test_chat_route_endpoint():
    """Verify POST /chat/route determines model and task classification."""
    resp = client.post("/chat/route", json={"prompt": "Write Python code to calculate pump efficiency"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["task_type"] == "coding"
    assert data["model"] == "qwen2.5-coder:7b"
    assert "reason" in data


# 9. Chat Generate API with Auto-Route (using Mock Provider)
def test_chat_generate_auto_route_mock():
    """Verify POST /chat/generate with auto_route using mock provider."""
    resp = client.post("/chat/generate", json={
        "prompt": "Write Python code to calculate pump efficiency",
        "provider": "mock",
        "auto_route": True
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["task_type"] == "coding"
    assert "Mock LLM Response" in data["text"]


# 10. Extended Health Check API Endpoint
def test_extended_health_check():
    """Verify GET /health returns system status and local model indicators."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["app_name"] == "ConfigIQ Backend"
    assert data["network"] == "LOCAL_ONLY"
    assert "ollama" in data


# 11. Network Status API Endpoint
def test_network_status_sovereignty():
    """Verify GET /network/status maintains LOCAL_ONLY sovereignty status."""
    resp = client.get("/network/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("LOCAL_ONLY", "WARNING_EXTERNAL_ATTEMPT_DETECTED")
    assert data["internet_required"] is False


# 12. Audit Logging Verification
def test_audit_logging():
    """Verify audit log entries record component, timing, and local scope."""
    audit_service.log_action(
        action="LLM_TEST_AUDIT",
        component="test.suite",
        status="SUCCESS",
        duration_ms=12.5,
        details={"provider": "ollama", "network_scope": "LOCALHOST"},
        is_external=False
    )

    logs = audit_service.get_logs(limit=10)
    assert len(logs) > 0
    latest = logs[-1]
    assert latest.action == "LLM_TEST_AUDIT"
    assert latest.is_external is False
