import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional
from backend.models.schemas import TaskCreateRequest, TaskResponse
from backend.services.audit_service import audit_service

class TaskService:
    """
    Service for managing asynchronous and multi-step agentic tasks.
    """

    def __init__(self):
        self._tasks: Dict[str, TaskResponse] = {}

    def create_task(self, request: TaskCreateRequest) -> TaskResponse:
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc).isoformat()
        task = TaskResponse(
            task_id=task_id,
            description=request.description,
            status="pending",
            created_at=now,
            updated_at=now,
            document_id=request.document_id,
            result=None,
            steps=["Task created"]
        )
        self._tasks[task_id] = task

        audit_service.log_action(
            action="TASK_CREATE",
            component="task_service",
            status="SUCCESS",
            task_id=task_id,
            details={"description": request.description, "document_id": request.document_id}
        )
        return task

    def get_task(self, task_id: str) -> Optional[TaskResponse]:
        return self._tasks.get(task_id)

    def list_tasks(self) -> List[TaskResponse]:
        return list(self._tasks.values())

    def update_task_status(
        self,
        task_id: str,
        status: str,
        step: Optional[str] = None,
        result: Optional[dict] = None
    ) -> Optional[TaskResponse]:
        task = self._tasks.get(task_id)
        if not task:
            return None

        task.status = status
        task.updated_at = datetime.now(timezone.utc).isoformat()
        if step:
            task.steps.append(step)
        if result is not None:
            task.result = result

        audit_service.log_action(
            action="TASK_UPDATE",
            component="task_service",
            status="SUCCESS",
            task_id=task_id,
            details={"status": status, "latest_step": step}
        )
        return task

# Global task service instance
task_service = TaskService()
