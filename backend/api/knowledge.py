from fastapi import APIRouter, status

from backend.models.schemas import (
    KnowledgeIngestRequest,
    KnowledgeIngestResponse,
    KnowledgeSearchRequest,
    KnowledgeSearchResultItem,
    KnowledgeSearchResponse,
)
from backend.services.audit_service import audit_service

router = APIRouter(prefix="/knowledge", tags=["Knowledge Base"])


@router.post("/ingest", response_model=KnowledgeIngestResponse, status_code=status.HTTP_200_OK)
async def ingest_knowledge(request: KnowledgeIngestRequest):
    """
    Ingest local organizational documents into vector store.
    Placeholder implementation for Phase 1 foundation.
    """
    audit_service.log_action(
        action="KNOWLEDGE_INGEST_REQUEST",
        component="api.knowledge",
        status="SUCCESS",
        details={"directory": request.directory_path, "force_reindex": request.force_reindex}
    )

    return KnowledgeIngestResponse(
        status="success",
        documents_indexed=3,
        chunks_created=45,
        message=f"Placeholder ingestion completed for directory '{request.directory_path}'."
    )


@router.post("/search", response_model=KnowledgeSearchResponse, status_code=status.HTTP_200_OK)
async def search_knowledge(request: KnowledgeSearchRequest):
    """
    Search local vector database for relevant industrial SOPs and technical manuals.
    Placeholder implementation for Phase 1 foundation.
    """
    audit_service.log_action(
        action="KNOWLEDGE_SEARCH",
        component="api.knowledge",
        status="SUCCESS",
        details={"query": request.query, "top_k": request.top_k}
    )

    mock_results = [
        KnowledgeSearchResultItem(
            document="maintenance_sop.pdf",
            page=17,
            content=(
                "Section 4.3: Procedure for replacing corroded valve CV-102. "
                "Ensure line depressurization and double block and bleed isolation before flange unbolting."
            ),
            score=0.89,
            metadata={"category": "SOP", "section": "4.3"}
        ),
        KnowledgeSearchResultItem(
            document="inspection_guidelines.pdf",
            page=5,
            content="Visual inspection criteria for industrial pipe wall degradation and pit corrosion measurement.",
            score=0.78,
            metadata={"category": "Guidelines"}
        )
    ]

    return KnowledgeSearchResponse(
        query=request.query,
        results=mock_results[: request.top_k]
    )
