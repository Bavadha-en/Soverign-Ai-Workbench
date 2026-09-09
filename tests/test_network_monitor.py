import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.network_monitor import network_monitor

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_network():
    network_monitor.reset()
    yield
    network_monitor.reset()


def test_network_telemetry_endpoint():
    """Verify that /network/telemetry returns full air-gap socket telemetry."""
    response = client.get("/network/telemetry")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] in ["LOCAL_ONLY", "WARNING_EXTERNAL_ATTEMPT_DETECTED"]
    assert data["air_gap_compliant"] is True
    assert data["internet_required"] is False
    assert data["external_ai_calls"] == 0
    assert data["external_connections"] == 0
    assert len(data["active_listening_ports"]) >= 3
    assert len(data["interfaces"]) >= 1
    assert "SOVEREIGN-SEAL" in data["integrity_hash"]


def test_network_monitor_event_logging():
    """Verify that recording network events updates telemetry counters correctly."""
    initial_requests = network_monitor.get_telemetry().total_local_requests

    event = network_monitor.record_connection(
        source="127.0.0.1:9000",
        destination="127.0.0.1:8000",
        process="test_process",
        protocol="HTTP",
        status="ALLOWED_LOCAL",
        is_external=False,
        bytes_transferred=512
    )

    assert event.source == "127.0.0.1:9000"
    assert event.is_external is False
    assert network_monitor.get_telemetry().total_local_requests >= initial_requests + 1


def test_network_monitor_external_blocking():
    """Verify that external egress attempts are detected, logged as blocked, and flagged."""
    initial_blocked = network_monitor.get_telemetry().wan_egress_blocked

    blocked_event = network_monitor.record_connection(
        source="127.0.0.1:8000",
        destination="https://api.openai.com/v1/chat",
        process="unauthorized_cloud_attempt",
        protocol="HTTPS",
        status="BLOCKED_EXTERNAL_VIOLATION",
        is_external=True
    )

    assert blocked_event.is_external is True
    telemetry = network_monitor.get_telemetry()
    assert telemetry.wan_egress_blocked >= initial_blocked + 1
    network_monitor.reset()
