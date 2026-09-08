from typing import Optional
from backend.config import settings
from backend.llm.interface import LLMProvider
from backend.llm.mock_provider import MockLLMProvider
from backend.llm.ollama_provider import OllamaLLMProvider


def get_llm_provider(provider_type: Optional[str] = None) -> LLMProvider:
    """
    Factory to retrieve configured LLM provider instance.
    Defaults to configured environment provider (ollama or mock).
    """
    selected = (provider_type or settings.LLM_PROVIDER).lower().strip()
    if selected == "ollama":
        return OllamaLLMProvider()
    return MockLLMProvider()
