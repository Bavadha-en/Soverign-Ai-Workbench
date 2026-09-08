from abc import ABC, abstractmethod
from typing import Any, Dict
from backend.models.schemas import LLMGenerateRequest, LLMGenerateResponse

class LLMProvider(ABC):
    """
    Abstract Interface for Local Open-Weight LLM Providers.
    Decouples application logic from serving infrastructure (vLLM, Ollama, TGI, Llama.cpp, etc.)
    """

    @abstractmethod
    async def generate(self, request: LLMGenerateRequest) -> LLMGenerateResponse:
        """Generate plain text output for a prompt."""
        pass

    @abstractmethod
    async def generate_structured(self, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate structured JSON output adhering to a given JSON schema."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Verify local LLM service availability."""
        pass
