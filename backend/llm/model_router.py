from typing import Any, Dict, Optional
from backend.config import settings
from backend.llm.registry import model_registry


class ModelRouter:
    """
    Deterministic Model Router for ConfigIQ Sovereign Workbench.
    Routes incoming prompts to the optimal local open-weight model based on task classification.
    """

    def __init__(self, registry=None):
        self.registry = registry or model_registry

    def route(self, prompt: str, image_present: bool = False) -> Dict[str, Any]:
        """
        Classify task and select the appropriate local open-weight model.

        Returns:
            Dict containing:
                - task_type: str ("coding", "coding_heavy", "vision", "general")
                - model: str (model name, e.g. "qwen2.5-coder:7b")
                - reason: str (explanation for routing decision)
        """
        prompt_lower = prompt.lower().strip()

        # 1. Vision / Image Analysis Check
        if image_present or any(kw in prompt_lower for kw in [
            "scanned image", "scan analysis", "visual inspection", "analyze image",
            "image analysis", "read diagram", "ocr scan", "inspect photo"
        ]):
            vision_model = self.registry.get_model("vision")
            if vision_model:
                return {
                    "task_type": "vision",
                    "model": vision_model,
                    "reason": "Visual/image inspection task detected; routed to local vision model."
                }
            # Fallback when vision model is not installed
            general_model = self.registry.get_model("general") or settings.GENERAL_MODEL
            return {
                "task_type": "vision",
                "model": general_model,
                "reason": "Image task detected but no local vision model is installed; falling back to general model with text processing."
            }

        # 2. Complex Coding & Heavy Engineering Calculations
        heavy_coding_keywords = [
            "complex coding", "complex calculation", "difficult calculation",
            "complex engineering", "heavy coding", "advanced algorithm",
            "finite element", "numerical simulation", "complex program",
            "engineering calculation program", "multiprocessing architecture",
            "distributed pipeline", "optimization solver"
        ]
        if any(kw in prompt_lower for kw in heavy_coding_keywords):
            heavy_model = self.registry.get_model("coding_heavy") or settings.CODING_HEAVY_MODEL
            return {
                "task_type": "coding_heavy",
                "model": heavy_model,
                "reason": "Complex coding / heavy engineering calculation detected; routed to high-parameter coding model."
            }

        # 3. Standard Coding, Debugging & Scripting
        coding_keywords = [
            "python", "code", "programming", "script", "function", "debug",
            "refactor", "algorithm", "class", "syntax", "compile", "unit test",
            "sql", "regex", "fastapi", "def ", "import ", "write code",
            "implement", "bug fix", "coding", "calculate pump efficiency",
            "calculate pressure drop", "pipe friction"
        ]
        if any(kw in prompt_lower for kw in coding_keywords):
            coding_model = self.registry.get_model("coding") or settings.CODING_MODEL
            return {
                "task_type": "coding",
                "model": coding_model,
                "reason": "Standard coding/debugging task detected; routed to local coding specialist model."
            }

        # 4. Document Summarization, Approval Notes, General Industrial Reasoning
        general_model = self.registry.get_model("general") or settings.GENERAL_MODEL
        return {
            "task_type": "general",
            "model": general_model,
            "reason": "General reasoning / document summarization / SOP analysis task detected; routed to general language model."
        }


model_router = ModelRouter()
