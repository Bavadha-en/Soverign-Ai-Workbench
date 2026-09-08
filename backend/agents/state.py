from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class AgentState(BaseModel):
    """LangGraph state representation for agentic multi-step workflows."""
    task_id: str
    description: str
    document_id: Optional[str] = None
    steps: List[str] = Field(default_factory=list)
    plan: List[str] = Field(default_factory=list)
    current_step: int = 0
    context: Dict[str, Any] = Field(default_factory=dict)
    findings: List[str] = Field(default_factory=list)
    sop_references: List[str] = Field(default_factory=list)
    generated_docx_path: Optional[str] = None
    is_verified: bool = False
    error: Optional[str] = None
