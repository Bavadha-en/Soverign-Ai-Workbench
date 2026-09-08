from typing import Any, Dict, List, Optional
from backend.rag.embeddings import get_embedder
from backend.rag.vector_store import vector_store


class RAGRetriever:
    """
    Local RAG Semantic Retriever for Industrial Technical Queries.
    Retrieves most relevant document sections using vector embeddings.
    """

    def __init__(self, store=None, embedder=None):
        self.store = store or vector_store
        self.embedder = embedder or get_embedder()

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Embed search query and retrieve top-k semantically relevant chunks.
        """
        if not query or not query.strip():
            return []

        query_vector = self.embedder.embed_query(query)
        results = self.store.search(query_vector, top_k=top_k)
        return results


retriever = RAGRetriever()
