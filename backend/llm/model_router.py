import json
import re
from typing import Any, Dict, Optional
from backend.config import settings
from backend.llm.registry import model_registry


class ModelRouter:
    """
    Model Router for ConfigIQ Sovereign Workbench.
    Attempts LLM-based classification first, falls back to keyword-based routing.
    """

    def __init__(self, registry=None):
        self.registry = registry or model_registry
        self._llm_available: Optional[bool] = None

    async def _classify_with_llm(self, prompt: str, image_present: bool) -> Optional[str]:
        if image_present:
            return "vision"
        try:
            from backend.llm.factory import get_llm_provider
            from backend.models.schemas import LLMGenerateRequest

            provider = get_llm_provider()
            if provider.__class__.__name__ == "MockLLMProvider":
                return None
            classification_prompt = (
                "Classify this task into exactly one category. "
                "Categories: vision, coding_heavy, coding, general.\n"
                "- vision: image analysis, visual inspection, diagram reading\n"
                "- coding_heavy: complex simulations, FEA, optimization solvers, distributed systems\n"
                "- coding: standard programming, scripts, calculations, debugging\n"
                "- general: document analysis, summarization, reasoning, SOP review\n\n"
                f"Task: {prompt[:500]}\n\n"
                "Respond with ONLY the category name, nothing else."
            )
            request = LLMGenerateRequest(
                prompt=classification_prompt,
                temperature=0.0,
                max_tokens=20,
            )
            response = await provider.generate(request)
            category = response.text.strip().lower().replace('"', '').replace("'", "")
            if category in ("vision", "coding_heavy", "coding", "general"):
                return category
        except Exception:
            pass
        return None

    def route(self, prompt: str, image_present: bool = False) -> Dict[str, Any]:
        """
        Classify task and select the appropriate local open-weight model.
        Executes fast deterministic keyword matching first (<1ms) to eliminate latency.
        """
        return self._keyword_route(prompt, image_present)

    def _resolve_model(self, task_type: str, llm_routed: bool = False) -> Dict[str, Any]:
        method = "LLM classification" if llm_routed else "keyword matching"
        if task_type == "vision":
            model = self.registry.get_model("vision") or settings.GENERAL_MODEL
            return {"task_type": "vision", "model": model, "reason": f"Vision task detected via {method}; routed to local vision model."}
        elif task_type == "coding_heavy":
            model = self.registry.get_model("coding_heavy") or settings.CODING_HEAVY_MODEL
            return {"task_type": "coding_heavy", "model": model, "reason": f"Complex coding task detected via {method}; routed to high-parameter coding model."}
        elif task_type == "coding":
            model = self.registry.get_model("coding") or settings.CODING_MODEL
            return {"task_type": "coding", "model": model, "reason": f"Coding task detected via {method}; routed to local coding specialist model."}
        else:
            model = self.registry.get_model("general") or settings.GENERAL_MODEL
            return {"task_type": "general", "model": model, "reason": f"General reasoning task detected via {method}; routed to general language model."}

    def _keyword_route(self, prompt: str, image_present: bool = False) -> Dict[str, Any]:
        prompt_lower = prompt.lower().strip()

        if image_present or any(kw in prompt_lower for kw in [
            "scanned image", "scan analysis", "visual inspection", "analyze image",
            "image analysis", "read diagram", "ocr scan", "inspect photo"
        ]):
            return self._resolve_model("vision")

        heavy_coding_keywords = [
            "complex coding", "complex calculation", "difficult calculation",
            "complex engineering", "heavy coding", "advanced algorithm",
            "finite element", "numerical simulation", "complex program",
            "engineering calculation program", "multiprocessing architecture",
            "distributed pipeline", "optimization solver"
        ]
        if any(kw in prompt_lower for kw in heavy_coding_keywords):
            return self._resolve_model("coding_heavy")

        coding_keywords = [
            "python", "write code", "programming", "script", "function", "debug",
            "refactor", "algorithm", "class", "syntax", "compile", "unit test",
            "sql", "regex", "fastapi", "def ", "import ",
            "implement code", "bug fix", "coding", "calculate", "computation",
            "formula", "equation", "pump efficiency", "pressure drop", "pipe friction"
        ]
        if any(kw in prompt_lower for kw in coding_keywords):
            return self._resolve_model("coding")

        return self._resolve_model("general")


model_router = ModelRouter()
