import uuid
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from backend.models.schemas import AuditLogEntry

class AuditService:
    """
    Service for recording and retrieving audit logs in an air-gapped environment.
    Tracks operation status, component traces, and timing.
    """

    def __init__(self):
        self._logs: List[AuditLogEntry] = []

    def log_action(
        self,
        action: str,
        component: str,
        status: str = "SUCCESS",
        task_id: Optional[str] = None,
        duration_ms: float = 0.0,
        details: Optional[Dict[str, Any]] = None,
        is_external: bool = False
    ) -> AuditLogEntry:
        entry = AuditLogEntry(
            id=f"audit_{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            task_id=task_id,
            action=action,
            component=component,
            status=status,
            duration_ms=duration_ms,
            details=details or {},
            is_external=is_external
        )
        self._logs.append(entry)
        return entry

    def get_logs(self, task_id: Optional[str] = None, limit: int = 100) -> List[AuditLogEntry]:
        if task_id:
            filtered = [l for l in self._logs if l.task_id == task_id]
            return filtered[-limit:]
        return self._logs[-limit:]

    def get_external_attempts_count(self) -> int:
        return sum(1 for l in self._logs if l.is_external)

# Global audit service instance
audit_service = AuditService()
