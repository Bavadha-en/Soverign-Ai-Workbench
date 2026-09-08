import json
import re
import time
from typing import Any, Dict, List, Optional
import httpx

from backend.config import is_local_url, settings
from backend.llm.interface import LLMProvider
from backend.models.schemas import LLMGenerateRequest, LLMGenerateResponse
from backend.services.audit_service import audit_service


class OllamaLLMProvider(LLMProvider):
    """
    Local Open-Weight LLM Provider using the local Ollama HTTP API.
    Enforces strict air-gapped / on-premise execution with zero external network connectivity.
    """

    def __init__(self, base_url: Optional[str] = None, default_model: Optional[str] = None):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.default_model = default_model or settings.GENERAL_MODEL

        # Strict Network Sovereignty check: Reject non-local hostnames/IPs
        if not is_local_url(self.base_url):
            audit_service.log_action(
                action="SECURITY_VIOLATION_BLOCKED",
                component="llm.ollama_provider",
                status="BLOCKED",
                details={
                    "error": "External URL rejected by network sovereignty policy",
                    "attempted_url": self.base_url,
                    "external_call": True
                },
                is_external=True
            )
            raise ValueError(
                f"Network sovereignty violation: ConfigIQ only permits local inference endpoints "
                f"(localhost / 127.0.0.1). Rejected external URL: {self.base_url}"
            )

    async def generate(self, request: LLMGenerateRequest) -> LLMGenerateResponse:
        """Generate text using a local Ollama model."""
        start_time = time.time()
        model_name = getattr(request, "model", None) or self.default_model

        payload: Dict[str, Any] = {
            "model": model_name,
            "prompt": request.prompt,
            "stream": False,
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens,
            }
        }
        if request.system_prompt:
            payload["system"] = request.system_prompt
        if getattr(request, "images", None):
            payload["images"] = request.images


        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                response = await client.post(f"{self.base_url}/api/generate", json=payload)
                response.raise_for_status()
                data = response.json()

            duration_ms = round((time.time() - start_time) * 1000, 2)
            generated_text = data.get("response", "")

            # Extract token usage metadata from Ollama
            prompt_eval_count = data.get("prompt_eval_count", len(request.prompt.split()))
            eval_count = data.get("eval_count", len(generated_text.split()))
            usage = {
                "prompt_tokens": prompt_eval_count,
                "completion_tokens": eval_count,
                "total_tokens": prompt_eval_count + eval_count
            }

            # Log audit trail for sovereign LLM generation
            audit_service.log_action(
                action="LLM_GENERATION",
                component="llm.ollama_provider",
                status="SUCCESS",
                duration_ms=duration_ms,
                details={
                    "provider": "ollama",
                    "model": model_name,
                    "network_scope": "LOCALHOST",
                    "external_call": False,
                    "tokens": usage
                },
                is_external=False
            )

            return LLMGenerateResponse(
                text=generated_text,
                model=model_name,
                usage=usage,
                duration_ms=duration_ms
            )

        except Exception as exc:
            duration_ms = round((time.time() - start_time) * 1000, 2)
            audit_service.log_action(
                action="LLM_GENERATION",
                component="llm.ollama_provider",
                status="FAILED",
                duration_ms=duration_ms,
                details={
                    "provider": "ollama",
                    "model": model_name,
                    "error": str(exc),
                    "network_scope": "LOCALHOST",
                    "external_call": False
                },
                is_external=False
            )
            raise RuntimeError(f"Ollama local generation failed for model '{model_name}': {str(exc)}") from exc

    async def generate_structured(self, prompt: str, schema: Dict[str, Any], model: Optional[str] = None) -> Dict[str, Any]:
        """Generate structured JSON output adhering to a specified JSON schema."""
        start_time = time.time()
        model_name = model or self.default_model

        schema_str = json.dumps(schema, indent=2)
        system_instruction = (
            "You are a strict structured data generator. "
            "You MUST respond ONLY with a valid JSON object matching the JSON Schema provided below.\n"
            f"JSON Schema:\n{schema_str}"
        )

        payload = {
            "model": model_name,
            "prompt": prompt,
            "system": system_instruction,
            "format": "json",
            "stream": False,
            "options": {"temperature": 0.1, "num_predict": 2048}
        }

        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                response = await client.post(f"{self.base_url}/api/generate", json=payload)
                response.raise_for_status()
                data = response.json()

            raw_text = data.get("response", "").strip()
            parsed_json = self._safe_parse_json(raw_text)

            duration_ms = round((time.time() - start_time) * 1000, 2)
            audit_service.log_action(
                action="LLM_STRUCTURED_GENERATION",
                component="llm.ollama_provider",
                status="SUCCESS" if "error" not in parsed_json else "PARSE_ERROR",
                duration_ms=duration_ms,
                details={
                    "provider": "ollama",
                    "model": model_name,
                    "network_scope": "LOCALHOST",
                    "external_call": False
                },
                is_external=False
            )

            return parsed_json

        except Exception as exc:
            duration_ms = round((time.time() - start_time) * 1000, 2)
            audit_service.log_action(
                action="LLM_STRUCTURED_GENERATION",
                component="llm.ollama_provider",
                status="FAILED",
                duration_ms=duration_ms,
                details={"error": str(exc), "provider": "ollama", "network_scope": "LOCALHOST"},
                is_external=False
            )
            return {
                "status": "error",
                "error": f"Failed structured generation: {str(exc)}",
                "raw_output": None
            }

    def _safe_parse_json(self, text: str) -> Dict[str, Any]:
        """Safely parse JSON response with regex fallback for clean data extraction."""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try finding JSON block in markdown code block or braces
            match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    pass

            brace_match = re.search(r"(\{[\s\S]*\})", text)
            if brace_match:
                try:
                    return json.loads(brace_match.group(1))
                except json.JSONDecodeError:
                    pass

            return {
                "status": "error",
                "error": "Output was not valid JSON conforming to the requested schema",
                "raw_output": text
            }

    async def health_check(self) -> bool:
        """Verify local Ollama service availability."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception:
            return False

    async def list_available_models(self) -> List[str]:
        """List all locally installed open-weight models in Ollama."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    return [m.get("name") for m in data.get("models", []) if m.get("name")]
                return []
        except Exception:
            return []
