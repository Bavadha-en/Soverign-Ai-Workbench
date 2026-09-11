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

    async def chat(
        self,
        messages: list,
        model: Any = None,
        temperature: float = 0.5,
        max_tokens: int = 2048,
        **kwargs
    ) -> LLMGenerateResponse:
        """Multi-turn or conversational chat interface."""
        prompt_parts = []
        system = None
        for m in messages:
            role = m.get("role", "user")
            content = m.get("content", "")
            if role == "system":
                system = content
            else:
                prompt_parts.append(f"{role.capitalize()}: {content}")
        prompt = "\n".join(prompt_parts)
        req = LLMGenerateRequest(
            prompt=prompt,
            system_prompt=system,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return await self.generate(req)
