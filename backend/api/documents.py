import os
import uuid
from datetime import datetime, timezone
from typing import Dict
from fastapi import APIRouter, File, HTTPException, UploadFile, status

from backend.models.schemas import DocumentMetadataResponse, DocumentUploadResponse
from backend.services.audit_service import audit_service

router = APIRouter(prefix="/documents", tags=["Documents"])

# Local storage directory
STORAGE_DIR = os.path.join(os.getcwd(), "outputs", "storage")
os.makedirs(STORAGE_DIR, exist_ok=True)

# In-memory document metadata storage for Phase 1
DOCUMENTS_DB: Dict[str, DocumentMetadataResponse] = {}


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a document (PDF/Image) for ingestion and offline processing.
    Stores file locally without external transmission.
    """
    document_id = f"doc_{uuid.uuid4().hex[:8]}"
    file_extension = os.path.splitext(file.filename)[1]
    safe_filename = f"{document_id}_{file.filename}"
    file_path = os.path.join(STORAGE_DIR, safe_filename)

    content = await file.read()
    file_size = len(content)

    with open(file_path, "wb") as f:
        f.write(content)

    now = datetime.now(timezone.utc).isoformat()
    doc_meta = DocumentMetadataResponse(
        document_id=document_id,
        filename=file.filename,
        file_size=file_size,
        content_type=file.content_type or "application/octet-stream",
        storage_path=file_path,
        uploaded_at=now,
        status="uploaded",
        pages=None,
        text_extracted=False,
        ocr_pages=[],
        source="local"
    )

    DOCUMENTS_DB[document_id] = doc_meta

    audit_service.log_action(
        action="DOCUMENT_UPLOAD",
        component="api.documents",
        status="SUCCESS",
        details={"document_id": document_id, "filename": file.filename, "size": file_size}
    )

    return DocumentUploadResponse(**doc_meta.model_dump())


@router.get("/{document_id}", response_model=DocumentMetadataResponse)
async def get_document(document_id: str):
    """
    Retrieve document metadata and processing status by ID.
    """
    if document_id not in DOCUMENTS_DB:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{document_id}' not found."
        )

    audit_service.log_action(
        action="DOCUMENT_GET_METADATA",
        component="api.documents",
        status="SUCCESS",
        details={"document_id": document_id}
    )

    return DOCUMENTS_DB[document_id]
