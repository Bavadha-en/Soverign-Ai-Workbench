import json
import math
import os
from typing import Any, Dict, List, Optional, Tuple


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Compute cosine similarity between two numeric vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0

    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))

    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0

    return dot / (norm1 * norm2)


class LocalVectorStore:
    """
    On-premise persistent Vector Database for ConfigIQ.
    Stores chunk embeddings and provides cosine similarity semantic search with zero cloud dependencies.
    """

    def __init__(self, persistence_path: Optional[str] = None):
        self.persistence_path = persistence_path or os.path.join("outputs", "storage", "vector_store.json")
        self.documents: List[Dict[str, Any]] = []
        self.embeddings: List[List[float]] = []
        self.load()

    def add_documents(self, documents: List[Dict[str, Any]], embeddings: List[List[float]]) -> int:
        """
        Add chunked documents and their corresponding embedding vectors to the index.
        """
        if len(documents) != len(embeddings):
            raise ValueError("Document count must match embedding vector count.")

        added_count = 0
        existing_ids = {doc.get("id") for doc in self.documents if doc.get("id")}

        for doc, emb in zip(documents, embeddings):
            doc_id = doc.get("id")
            if doc_id and doc_id in existing_ids:
                # Update existing
                idx = next(i for i, d in enumerate(self.documents) if d.get("id") == doc_id)
                self.documents[idx] = doc
                self.embeddings[idx] = emb
            else:
                self.documents.append(doc)
                self.embeddings.append(emb)
                if doc_id:
                    existing_ids.add(doc_id)
                added_count += 1

        self.save()
        return added_count

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        score_threshold: float = -1.0
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic similarity search over stored document vectors.
        """
        if not self.embeddings or not query_embedding:
            return []

        scored_results: List[Tuple[float, Dict[str, Any]]] = []
        for doc, emb in zip(self.documents, self.embeddings):
            score = cosine_similarity(query_embedding, emb)
            if score >= score_threshold:
                scored_results.append((score, doc))

        # Sort descending by similarity score
        scored_results.sort(key=lambda x: x[0], reverse=True)

        results: List[Dict[str, Any]] = []
        for score, doc in scored_results[:top_k]:
            meta = dict(doc.get("metadata", {}))
            results.append({
                "id": doc.get("id"),
                "document": meta.get("document", "unknown"),
                "page": meta.get("page"),
                "content": doc.get("content", ""),
                "score": round(score, 4),
                "metadata": meta
            })

        return results

    def clear(self) -> None:
        """Clear all stored vectors and documents."""
        self.documents = []
        self.embeddings = []
        if os.path.exists(self.persistence_path):
            try:
                os.remove(self.persistence_path)
            except Exception:
                pass

    def save(self) -> None:
        """Persist vector index to local storage file."""
        os.makedirs(os.path.dirname(self.persistence_path), exist_ok=True)
        data = {
            "documents": self.documents,
            "embeddings": self.embeddings,
            "count": len(self.documents)
        }
        with open(self.persistence_path, "w", encoding="utf-8") as f:
            json.dump(data, f)

    def load(self) -> None:
        """Load vector index from local storage file if it exists."""
        if os.path.exists(self.persistence_path):
            try:
                with open(self.persistence_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.documents = data.get("documents", [])
                    self.embeddings = data.get("embeddings", [])
            except Exception:
                self.documents = []
                self.embeddings = []

    def count(self) -> int:
        return len(self.documents)


vector_store = LocalVectorStore()
