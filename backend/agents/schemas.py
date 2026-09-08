from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    PLANNING = "PLANNING"
    EXECUTING = "EXECUTING"
    VERIFYING = "VERIFYING"
    RETRYING = "RETRYING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class FactVerificationStatus(str, Enum):
    SUPPORTED = "SUPPORTED"
    UNSUPPORTED = "UNSUPPORTED"
    NEEDS_REVIEW = "NEEDS REVIEW"


class PlanStep(BaseModel):
    step: int = Field(..., description="Step index (1-based)")
    action: str = Field(..., description="Action name/identifier")
    tool: str = Field(..., description="Tool registry identifier")
    description: str = Field("", description="Human-readable description of this step")
    params: Dict[str, Any] = Field(default_factory=dict, description="Parameters to pass to the tool")
    status: str = Field("pending", description="Status of the step (pending, running, completed, failed, retried)")
    result: Optional[Any] = Field(None, description="Output from tool execution")
    error: Optional[str] = Field(None, description="Error message if step failed")


class ToolDefinition(BaseModel):
    name: str
    description: str
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    output_schema: Dict[str, Any] = Field(default_factory=dict)


class FactClaimVerification(BaseModel):
    claim: str
    status: FactVerificationStatus = FactVerificationStatus.SUPPORTED
    source_document: Optional[str] = None
    page: Optional[int] = None
    confidence: float = 1.0
    evidence: Optional[str] = None


class VerificationSummary(BaseModel):
    is_valid: bool = True
    total_claims: int = 0
    supported_claims: int = 0
    unsupported_claims: int = 0
    needs_review_claims: int = 0
    claims: List[FactClaimVerification] = Field(default_factory=list)
    calculation_valid: Optional[bool] = None
    notes: List[str] = Field(default_factory=list)


class AgentRunRequest(BaseModel):
    task: str = Field(..., json_schema_extra={"example": "Analyze this inspection report and prepare an approval note."})
    document_ids: Optional[List[str]] = Field(default_factory=list, json_schema_extra={"example": ["doc_12345"]})
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)


class AgentRunResponse(BaseModel):
    task_id: str
    status: str
    plan: List[Dict[str, Any]]
    steps_completed: int
    final_output: Optional[str] = None
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    generated_files: List[str] = Field(default_factory=list)
    verification: Optional[Dict[str, Any]] = None
    execution_trace: List[str] = Field(default_factory=list)
    local: bool = True
