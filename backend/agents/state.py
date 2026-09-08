import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.agents.schemas import AgentStatus, PlanStep


class AgentState(BaseModel):
    """
    Explicit, serializable state representation for ConfigIQ Agentic Workflows.
    Maintains complete auditability, execution trace, retrieved context, and verification state.
    """
    task_id: str
    user_request: str
    current_step: int = 0
    status: AgentStatus = AgentStatus.PLANNING
    document_ids: List[str] = Field(default_factory=list)
    plan: List[Dict[str, Any]] = Field(default_factory=list)
    completed_steps: List[Dict[str, Any]] = Field(default_factory=list)
    failed_steps: List[Dict[str, Any]] = Field(default_factory=list)
    tool_results: Dict[str, Any] = Field(default_factory=dict)
    retrieved_context: List[Dict[str, Any]] = Field(default_factory=list)
    model_outputs: Dict[str, Any] = Field(default_factory=dict)
    verification_results: Dict[str, Any] = Field(default_factory=dict)
    execution_trace: List[str] = Field(default_factory=list)
    generated_files: List[str] = Field(default_factory=list)
    final_output: Optional[str] = None
    retry_counts: Dict[str, int] = Field(default_factory=dict)
    max_retries: int = 3
    error: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # Backward compatibility with Phase 1-3 schemas
    description: Optional[str] = None
    document_id: Optional[str] = None
    steps: List[str] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)
    findings: List[str] = Field(default_factory=list)
    sop_references: List[str] = Field(default_factory=list)
    generated_docx_path: Optional[str] = None
    is_verified: bool = False

    def model_post_init(self, __context: Any) -> None:
        if not self.description:
            self.description = self.user_request
        if not self.document_id and self.document_ids:
            self.document_id = self.document_ids[0]

    def add_trace(self, message: str) -> None:
        """Add a timestamped/indexed entry to the human-readable execution trace."""
        self.execution_trace.append(message)
        self.steps.append(message)
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def set_status(self, new_status: AgentStatus) -> None:
        """Transition agent state machine status."""
        self.status = new_status
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def record_step_result(self, step_idx: int, action: str, tool_name: str, result: Any, success: bool = True) -> None:
        """Record the outcome of a plan step execution."""
        step_record = {
            "step": step_idx,
            "action": action,
            "tool": tool_name,
            "status": "completed" if success else "failed",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        if success:
            self.completed_steps.append(step_record)
            self.tool_results[action] = result
        else:
            self.failed_steps.append(step_record)
        self.current_step = step_idx
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def get_retry_count(self, action: str) -> int:
        return self.retry_counts.get(action, 0)

    def increment_retry_count(self, action: str) -> int:
        count = self.retry_counts.get(action, 0) + 1
        self.retry_counts[action] = count
        return count

    def can_retry(self, action: str) -> bool:
        return self.get_retry_count(action) < self.max_retries

    def to_dict(self) -> Dict[str, Any]:
        """Serialize state to standard Python dictionary."""
        return self.model_dump()

    def to_json(self, indent: int = 2) -> str:
        """Serialize state to JSON formatted string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)
