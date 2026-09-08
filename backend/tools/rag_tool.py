from typing import Any, Dict, List
from backend.rag.retriever import retriever


def search_knowledge(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Retrieve semantically relevant knowledge base chunks for a query."""
    return retriever.retrieve(query, top_k=top_k)
