from typing import Any, Dict, List, Optional
from backend.config import settings


class ModelRegistry:
    """
    Local Open-Weight Model Registry for ConfigIQ.
    Maps capability roles to concrete open-weight models and tracks local availability.
    """

    def __init__(self):
        self._registry = {
            "general": settings.GENERAL_MODEL,
            "coding": settings.CODING_MODEL,
            "coding_heavy": settings.CODING_HEAVY_MODEL,
            "embedding": settings.EMBEDDING_MODEL,
            "vision": settings.VISION_MODEL if settings.VISION_MODEL else None,
        }

    def get_model(self, role: str) -> Optional[str]:
        """Retrieve model name for a specific role."""
        return self._registry.get(role)

    def get_all_models(self) -> Dict[str, Optional[str]]:
        """Retrieve all registered models by role."""
        return dict(self._registry)

    def set_model(self, role: str, model_name: str) -> None:
        """Update a model mapping dynamically."""
        self._registry[role] = model_name

    def verify_availability(self, installed_models: List[str]) -> Dict[str, bool]:
        """
        Compare configured model registry against installed models from local Ollama.
        Cleanly identifies available vs missing models without failing the application.
        """
        installed_set = {m.lower().strip() for m in installed_models}
        
        # Also handle bare names without tags (e.g. 'llama3' matches 'llama3:latest')
        bare_installed = {m.split(":")[0] for m in installed_set}

        status: Dict[str, bool] = {}
        for role, model_name in self._registry.items():
            if not model_name:
                status[role] = False
                continue
            name_lower = model_name.lower().strip()
            bare_name = name_lower.split(":")[0]
            
            is_available = (
                name_lower in installed_set or
                bare_name in bare_installed or
                any(inst.startswith(name_lower) or name_lower.startswith(inst) for inst in installed_set)
            )
            status[role] = is_available

        return status


model_registry = ModelRegistry()
