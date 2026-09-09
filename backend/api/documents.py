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


@router.get("/samples/list")
async def list_sample_documents():
    """
    List pre-packaged sample industrial inspection images and test documents available in the repository.
    """
    sample_dir = os.path.join(os.getcwd(), "datasets", "sample_images")
    if not os.path.exists(sample_dir):
        return {"samples": []}

    samples_info = [
        {
            "filename": "metal_nut_surface_scratch.png",
            "title": "Metal Nut Surface Scratch",
            "category": "Hardware / Fastener",
            "description": "Surface defect and thread scratch on industrial metal fastener.",
        },
        {
            "filename": "metal_nut_bent_deformation.png",
            "title": "Metal Nut Bent Deformation",
            "category": "Hardware / Fastener",
            "description": "Plastic deformation and bent geometry on mechanical component.",
        },
        {
            "filename": "cable_insulation_cut.png",
            "title": "Cable Insulation Cut Defect",
            "category": "Electrical Cabling",
            "description": "Exposed conductor and cut outer protective insulation.",
        },
        {
            "filename": "structural_surface_crack.png",
            "title": "Structural Surface Crack",
            "category": "Material / Cladding",
            "description": "Linear stress crack and fracture on component surface.",
        },
        {
            "filename": "scanned_inspection_sheet.png",
            "title": "Scanned Inspection Log",
            "category": "Inspection Logs / Forms",
            "description": "Scanned industrial maintenance sheet suitable for OCR extraction.",
        },
    ]

    available = []
    for s in samples_info:
        file_path = os.path.join(sample_dir, s["filename"])
        if os.path.exists(file_path):
            available.append({
                **s,
                "file_size": os.path.getsize(file_path),
                "url": f"/public/sample_images/{s['filename']}"
            })
    return {"samples": available}


@router.post("/samples/load/{filename}", response_model=DocumentUploadResponse)
async def load_sample_document(filename: str):
    """
    Load a pre-packaged sample inspection image or document directly into active documents for demo tasks.
    """
    sample_dir = os.path.join(os.getcwd(), "datasets", "sample_images")
    source_path = os.path.join(sample_dir, filename)

    if not os.path.exists(source_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sample document '{filename}' not found in datasets/sample_images."
        )

    document_id = f"sample_{uuid.uuid4().hex[:6]}"
    safe_filename = f"{document_id}_{filename}"
    target_path = os.path.join(STORAGE_DIR, safe_filename)

    with open(source_path, "rb") as src, open(target_path, "wb") as dst:
        content = src.read()
        dst.write(content)

    ext = os.path.splitext(filename)[1].lower()
    content_type = "image/png" if ext in (".png", ".jpg", ".jpeg") else "application/pdf"
    now = datetime.now(timezone.utc).isoformat()

    doc_meta = DocumentMetadataResponse(
        document_id=document_id,
        filename=filename,
        file_size=len(content),
        content_type=content_type,
        storage_path=target_path,
        uploaded_at=now,
        status="uploaded",
        pages=1,
        text_extracted=False,
        ocr_pages=[],
        source="sample_dataset"
    )

    DOCUMENTS_DB[document_id] = doc_meta

    audit_service.log_action(
        action="DOCUMENT_LOAD_SAMPLE",
        component="api.documents",
        status="SUCCESS",
        details={"document_id": document_id, "filename": filename, "size": len(content)}
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
