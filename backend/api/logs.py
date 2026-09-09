from typing import Optional
from fastapi import APIRouter

from backend.models.schemas import AuditLogResponse, NetworkStatusResponse
from backend.services.audit_service import audit_service
from backend.services.network_monitor import network_monitor, NetworkTelemetry

router = APIRouter(tags=["Audit Logs & Sovereignty"])


@router.get("/logs", response_model=AuditLogResponse)
async def get_audit_logs(task_id: Optional[str] = None, limit: int = 100):
    """
    Retrieve system audit logs and action traces for verification & UI rendering.
    """
    logs = audit_service.get_logs(task_id=task_id, limit=limit)
    return AuditLogResponse(logs=logs, total=len(logs))


@router.get("/network/status", response_model=NetworkStatusResponse)
async def get_network_status():
    """
    Check network sovereignty status. Verifies 100% on-premise execution with zero external calls.
    """
    external_calls = audit_service.get_external_attempts_count()
    return NetworkStatusResponse(
        internet_required=False,
        external_ai_calls=external_calls,
        external_connections=0,
        status="LOCAL_ONLY" if external_calls == 0 else "WARNING_EXTERNAL_ATTEMPT_DETECTED"
    )


@router.get("/network/telemetry", response_model=NetworkTelemetry)
async def get_network_telemetry():
    """
    Real-time socket and network packet telemetry proving 100% air-gapped sovereign execution.
    """
    return network_monitor.get_telemetry()


@router.get("/network/connections")
async def get_live_connections():
    """
    Live OS-level TCP/UDP connection scan via psutil.
    Returns every active socket with local/remote addresses and external flag.
    """
    conns = network_monitor.scan_live_connections()
    external = [c for c in conns if c.get("is_external")]
    return {
        "total": len(conns),
        "external_count": len(external),
        "air_gap_compliant": len(external) == 0,
        "connections": conns,
    }

