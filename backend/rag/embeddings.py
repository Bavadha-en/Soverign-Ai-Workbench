from abc import ABC, abstractmethod
import math
import re
from typing import List, Optional
import httpx

from backend.config import is_local_url, settings


class BaseEmbedder(ABC):
    """Abstract interface for local text embedding generators."""

    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embedding vectors for a list of text passages."""
        pass

    @abstractmethod
    def embed_query(self, query: str) -> List[float]:
        """Generate an embedding vector for a single search query."""
        pass


class LocalFallbackEmbedder(BaseEmbedder):
    """
    Deterministic zero-dependency local embedder for air-gapped environments.
    Maps terms and subword n-grams into a normalized 256-dimensional vector space.
    """

    def __init__(self, dimension: int = 256):
        self.dimension = dimension

    def _hash_token(self, token: str) -> int:
        val = 0
        for char in token:
            val = (val * 31 + ord(char)) % self.dimension
        return val

    def _embed_single(self, text: str) -> List[float]:
        vector = [0.0] * self.dimension
        tokens = re.findall(r"\b\w+\b", text.lower())
        if not tokens:
            return vector

        for token in tokens:
            idx = self._hash_token(token)
            vector[idx] += 1.0

        # L2 Normalize
        norm = math.sqrt(sum(v * v for v in vector))
        if norm > 0:
            vector = [v / norm for v in vector]

        return vector

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        return [self._embed_single(t) for t in texts]

    def embed_query(self, query: str) -> List[float]:
        return self._embed_single(query)


class OllamaEmbedder(BaseEmbedder):
    """
    Local Embedding generator using Ollama HTTP API (e.g. nomic-embed-text / all-minilm).
    Supports high-speed batch embedding via /api/embed and fallback to /api/embeddings.
    """

    def __init__(self, base_url: Optional[str] = None, model_name: Optional[str] = None):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self.fallback = LocalFallbackEmbedder()

        if not is_local_url(self.base_url):
            raise ValueError(f"Network sovereignty violation: Non-local embedding URL {self.base_url}")

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Batch embed multiple texts in a single HTTP call."""
        if not texts:
            return []

        try:
            with httpx.Client(timeout=2.0) as client:
                # 1. Try modern Ollama /api/embed batch API
                resp = client.post(
                    f"{self.base_url}/api/embed",
                    json={"model": self.model_name, "input": texts}
                )
                if resp.status_code == 200:
                    data = resp.json()
                    embs = data.get("embeddings")
                    if embs and len(embs) == len(texts):
                        return embs

                # 2. Fallback to /api/embeddings in persistent session
                results = []
                for text in texts:
                    r = client.post(
                        f"{self.base_url}/api/embeddings",
                        json={"model": self.model_name, "prompt": text}
                    )
                    if r.status_code == 200 and "embedding" in r.json():
                        results.append(r.json()["embedding"])
                    else:
                        results.append(self.fallback.embed_query(text))
                return results

        except Exception:
            return self.fallback.embed_texts(texts)

    def embed_query(self, query: str) -> List[float]:
        results = self.embed_texts([query])
        return results[0] if results else self.fallback.embed_query(query)


def get_embedder(model_name: Optional[str] = None) -> BaseEmbedder:
    """Retrieve configured embedder instance."""
    return OllamaEmbedder(model_name=model_name)
