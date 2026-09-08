from fastapi import APIRouter, status

from backend.llm.factory import get_llm_provider
from backend.llm.model_router import model_router
from backend.llm.registry import model_registry
from backend.models.schemas import (
    LLMGenerateRequest,
    LLMGenerateResponse,
    ModelRoutingResponse,
)
from backend.services.audit_service import audit_service

router = APIRouter(prefix="/chat", tags=["LLM Chat"])


@router.post("/route", response_model=ModelRoutingResponse, status_code=status.HTTP_200_OK)
async def route_task(request: LLMGenerateRequest):
    """
    Classify input task and determine the optimal local open-weight model.
    """
    decision = model_router.route(request.prompt)
    return ModelRoutingResponse(
        task_type=decision["task_type"],
        model=decision["model"],
        reason=decision["reason"],
    )


@router.get("/registry", tags=["LLM Chat"])
async def get_model_registry():
    """
    Retrieve configured model registry mapping roles to open-weight models.
    """
    return {
        "registry": model_registry.get_all_models(),
        "status": "configured"
    }


@router.post("/generate", response_model=LLMGenerateResponse, status_code=status.HTTP_200_OK)
async def generate_response(request: LLMGenerateRequest):
    """
    Generate response via local LLM abstraction layer with optional deterministic auto-routing.
    Supports switching between MockLLMProvider and OllamaLLMProvider.
    """
    task_type = None
    routing_reason = None

    # Auto-routing when explicitly requested
    if request.auto_route:
        routing_decision = model_router.route(request.prompt)
        request.model = routing_decision["model"]
        task_type = routing_decision["task_type"]
        routing_reason = routing_decision["reason"]

    provider = get_llm_provider(request.provider)
    response = await provider.generate(request)

    if task_type:
        response.task_type = task_type
        response.routing_reason = routing_reason

    audit_service.log_action(
        action="LLM_GENERATE",
        component="api.chat",
        status="SUCCESS",
        duration_ms=response.duration_ms,
        details={
            "model": response.model,
            "provider": getattr(request, "provider", None) or provider.__class__.__name__,
            "prompt_len": len(request.prompt),
            "task_type": task_type,
            "auto_route": request.auto_route
        }
    )

    return response
