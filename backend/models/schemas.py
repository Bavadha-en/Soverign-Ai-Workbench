from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

# --- Health & System ---

class HealthResponse(BaseModel):
    status: str = Field(..., json_schema_extra={"example": "healthy"})
    app_name: str = Field("ConfigIQ Backend", json_schema_extra={"example": "ConfigIQ Backend"})
    version: str = Field("1.0.0", json_schema_extra={"example": "1.0.0"})
    environment: str = Field("on-premise / air-gapped", json_schema_extra={"example": "on-premise / air-gapped"})
    timestamp: str
    ollama: Optional[str] = Field(None, json_schema_extra={"example": "available"})
    models: Optional[Dict[str, bool]] = Field(None, json_schema_extra={"example": {"general": True, "coding": True}})
    network: Optional[str] = Field("LOCAL_ONLY", json_schema_extra={"example": "LOCAL_ONLY"})


# --- Document Processing ---

class DocumentUploadResponse(BaseModel):
    document_id: str = Field(..., json_schema_extra={"example": "doc_abc123"})
    filename: str = Field(..., json_schema_extra={"example": "inspection_report.pdf"})
    file_size: int = Field(..., json_schema_extra={"example": 102450})
    content_type: str = Field("application/pdf", json_schema_extra={"example": "application/pdf"})
    storage_path: str
    uploaded_at: str
    status: str = Field("uploaded", json_schema_extra={"example": "uploaded"})
    pages: Optional[int] = Field(None, json_schema_extra={"example": 12})
    text_extracted: bool = Field(False)
    ocr_pages: List[int] = Field(default_factory=list, json_schema_extra={"example": [2, 3, 4]})
    source: str = Field("local", json_schema_extra={"example": "local"})

class DocumentMetadataResponse(BaseModel):
    document_id: str
    filename: str
    file_size: int
    content_type: str
    storage_path: str
    uploaded_at: str
    status: str
    pages: Optional[int] = None
    text_extracted: bool = False
    ocr_pages: List[int] = []
    source: str = "local"

class KnowledgeIngestRequest(BaseModel):
    directory_path: str = Field("knowledge_base", json_schema_extra={"example": "knowledge_base"})
    force_reindex: bool = Field(False, json_schema_extra={"example": False})

class KnowledgeIngestResponse(BaseModel):
    status: str = Field("success", json_schema_extra={"example": "success"})
    documents_indexed: int = Field(..., json_schema_extra={"example": 5})
    chunks_created: int = Field(..., json_schema_extra={"example": 120})
    message: str = Field(..., json_schema_extra={"example": "Knowledge base successfully ingested 5 documents."})

class KnowledgeSearchRequest(BaseModel):
    query: str = Field(..., json_schema_extra={"example": "procedure for replacing a corroded valve"})
    top_k: int = Field(5, json_schema_extra={"example": 5})

class KnowledgeSearchResultItem(BaseModel):
    document: str = Field(..., json_schema_extra={"example": "maintenance_sop.pdf"})
    page: Optional[int] = Field(None, json_schema_extra={"example": 17})
    content: str = Field(..., json_schema_extra={"example": "Step 1: Isolate valve line..."})
    score: float = Field(..., json_schema_extra={"example": 0.87})
    metadata: Optional[Dict[str, Any]] = None

class KnowledgeSearchResponse(BaseModel):
    query: str
    results: List[KnowledgeSearchResultItem]

# --- Tasks ---

class TaskCreateRequest(BaseModel):
    description: str = Field(..., json_schema_extra={"example": "Analyze uploaded inspection report and check SOP."})
    document_id: Optional[str] = Field(None, json_schema_extra={"example": "doc_abc123"})
    metadata: Optional[Dict[str, Any]] = None

class TaskResponse(BaseModel):
    task_id: str = Field(..., json_schema_extra={"example": "task_xyz789"})
    description: str
    status: str = Field("pending", json_schema_extra={"example": "pending"})
    created_at: str
    updated_at: str
    document_id: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    steps: List[str] = Field(default_factory=list)

# --- LLM Abstraction ---

class ModelRoutingResponse(BaseModel):
    task_type: str = Field(..., json_schema_extra={"example": "coding"})
    model: str = Field(..., json_schema_extra={"example": "qwen2.5-coder:7b"})
    reason: str = Field(..., json_schema_extra={"example": "Coding task detected"})

class LLMGenerateRequest(BaseModel):
    prompt: str = Field(..., json_schema_extra={"example": "Summarize the technical findings."})
    system_prompt: Optional[str] = Field(None, json_schema_extra={"example": "You are an industrial safety expert."})
    temperature: float = Field(0.7, json_schema_extra={"example": 0.7})
    max_tokens: int = Field(1000, json_schema_extra={"example": 1000})
    model: Optional[str] = Field(None, json_schema_extra={"example": "llama3:latest"})
    provider: Optional[str] = Field(None, json_schema_extra={"example": "ollama"})
    auto_route: bool = Field(False, json_schema_extra={"example": True})
    images: Optional[List[str]] = Field(default_factory=list, json_schema_extra={"example": []})


class LLMGenerateResponse(BaseModel):
    text: str
    model: str = Field("mock-open-weight-v1", json_schema_extra={"example": "mock-open-weight-v1"})
    usage: Optional[Dict[str, int]] = Field(default_factory=dict)
    duration_ms: float = Field(0.0)
    task_type: Optional[str] = None
    routing_reason: Optional[str] = None


# --- Audit Logs ---

class AuditLogEntry(BaseModel):
    id: str
    timestamp: str
    task_id: Optional[str] = None
    action: str = Field(..., json_schema_extra={"example": "PDF_PROCESS"})
    component: str = Field(..., json_schema_extra={"example": "pdf_processor"})
    status: str = Field(..., json_schema_extra={"example": "SUCCESS"})
    duration_ms: float = Field(0.0)
    details: Optional[Dict[str, Any]] = None
    is_external: bool = Field(False)

class AuditLogResponse(BaseModel):
    logs: List[AuditLogEntry]
    total: int

# --- Network Sovereignty ---

class NetworkStatusResponse(BaseModel):
    internet_required: bool = Field(False, json_schema_extra={"example": False})
    external_ai_calls: int = Field(0, json_schema_extra={"example": 0})
    external_connections: int = Field(0, json_schema_extra={"example": 0})
    status: str = Field("LOCAL_ONLY", json_schema_extra={"example": "LOCAL_ONLY"})


# --- Phase 6 & Phase 7 Tools & Sandbox Schemas ---

class ReadFileInput(BaseModel):
    path: str = Field(..., json_schema_extra={"example": "outputs/storage/doc.txt"})

class ReadFileOutput(BaseModel):
    success: bool
    path: str
    content: Optional[str] = None
    file_size: Optional[int] = None
    error: Optional[str] = None

class WriteFileInput(BaseModel):
    path: str = Field(..., json_schema_extra={"example": "outputs/output.txt"})
    content: str = Field(..., json_schema_extra={"example": "Sample content"})

class WriteFileOutput(BaseModel):
    success: bool
    path: str
    bytes_written: int = 0
    error: Optional[str] = None

class ExtractPDFInput(BaseModel):
    file_path: str = Field(..., json_schema_extra={"example": "outputs/storage/report.pdf"})

class ExtractPDFOutput(BaseModel):
    success: bool
    file_path: str
    pages: int = 0
    text: str = ""
    text_extracted: bool = False
    ocr_pages: List[int] = Field(default_factory=list)
    error: Optional[str] = None

class PerformOCRInput(BaseModel):
    image_path: str = Field(..., json_schema_extra={"example": "outputs/storage/page2.png"})

class PerformOCROutput(BaseModel):
    success: bool
    image_path: str
    text: str = ""
    error: Optional[str] = None

class SearchKnowledgeInput(BaseModel):
    query: str = Field(..., json_schema_extra={"example": "corroded valve replacement procedure"})
    top_k: int = Field(5, json_schema_extra={"example": 5})

class SearchKnowledgeOutput(BaseModel):
    success: bool
    query: str
    results: List[Dict[str, Any]] = Field(default_factory=list)
    error: Optional[str] = None

class ExecutePythonInput(BaseModel):
    code: str = Field(..., json_schema_extra={"example": "print(2 + 2)"})
    timeout_sec: int = Field(30, json_schema_extra={"example": 30})

class ExecutePythonOutput(BaseModel):
    success: bool
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    duration_ms: float = 0.0
    isolation_mode: str = "docker"
    error: Optional[str] = None

class CreateWordInput(BaseModel):
    output_path: str = Field("outputs/Approval_Note.docx", json_schema_extra={"example": "outputs/Approval_Note.docx"})
    title: str = Field(..., json_schema_extra={"example": "APPROVAL NOTE"})
    sections: Dict[str, str] = Field(..., json_schema_extra={"example": {"1. Background": "Details..."}})
    subject: Optional[str] = Field(None, json_schema_extra={"example": "Valve Maintenance Request"})

class CreateWordOutput(BaseModel):
    success: bool
    output_path: str
    file_size: int = 0
    error: Optional[str] = None

class ApprovalNoteInput(BaseModel):
    output_path: str = Field("outputs/Approval_Note.docx", json_schema_extra={"example": "outputs/Approval_Note.docx"})
    title: str = Field("CONFIDENTIAL APPROVAL NOTE", json_schema_extra={"example": "CONFIDENTIAL APPROVAL NOTE"})
    subject: str = Field("Equipment Maintenance & Repair Approval", json_schema_extra={"example": "Equipment Maintenance & Repair Approval"})
    background: str = Field(..., json_schema_extra={"example": "Routine plant inspection..."})
    inspection_findings: str = Field(..., json_schema_extra={"example": "Corrosion detected..."})
    technical_assessment: str = Field(..., json_schema_extra={"example": "Pressure limit exceeded..."})
    applicable_sop: str = Field(..., json_schema_extra={"example": "SOP-MECH-44..."})
    recommended_action: str = Field(..., json_schema_extra={"example": "Replace valve..."})
    approval_requested: str = Field(..., json_schema_extra={"example": "Approval for procurement..."})

class CreateExcelInput(BaseModel):
    output_path: str = Field("outputs/Report.xlsx", json_schema_extra={"example": "outputs/Report.xlsx"})
    data: List[Dict[str, Any]] = Field(..., json_schema_extra={"example": [{"ID": 1, "Item": "Valve", "Status": "Corroded"}]})
    sheet_name: str = Field("Sheet1", json_schema_extra={"example": "Sheet1"})

class CreateExcelOutput(BaseModel):
    success: bool
    output_path: str
    rows_written: int = 0
    file_size: int = 0
    error: Optional[str] = None


