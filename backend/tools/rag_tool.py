import time
from typing import Optional, Dict, Any, List
from backend.models.schemas import SearchKnowledgeOutput
from backend.services.audit_service import audit_service
from backend.rag.retriever import RAGRetriever


def search_knowledge(query: str, top_k: int = 5, task_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Searches the local knowledge base using RAGRetriever.
    Logs action to audit_service.
    """
    start_time = time.time()
    try:
        retriever = RAGRetriever()
        results = retriever.retrieve(query=query, top_k=top_k)

        duration = round((time.time() - start_time) * 1000, 2)
        audit_service.log_action(
            action="SEARCH_KNOWLEDGE",
            component="tools.rag_tool",
            status="SUCCESS",
            task_id=task_id,
            duration_ms=duration,
            details={"query": query, "top_k": top_k, "result_count": len(results)}
        )
        return SearchKnowledgeOutput(
            success=True,
            query=query,
            results=results if isinstance(results, list) else [],
            error=None
        ).model_dump()
    except Exception as e:
        duration = round((time.time() - start_time) * 1000, 2)
        audit_service.log_action(
            action="SEARCH_KNOWLEDGE",
            component="tools.rag_tool",
            status="FAILURE",
            task_id=task_id,
            duration_ms=duration,
            details={"query": query, "error": str(e)}
        )
        return SearchKnowledgeOutput(
            success=False,
            query=query,
            results=[],
            error=str(e)
        ).model_dump()
