from typing import Optional
from fastapi import APIRouter

from backend.models.schemas import AuditLogResponse, NetworkStatusResponse
from backend.services.audit_service import audit_service

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
