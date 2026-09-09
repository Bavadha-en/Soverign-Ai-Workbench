from typing import List, Optional
from fastapi import APIRouter, status
from pydantic import BaseModel, Field

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


class ChatMessage(BaseModel):
    role: str = Field(..., description="'user' or 'assistant'")
    content: str


class ChatConversationRequest(BaseModel):
    messages: List[ChatMessage]
    system_prompt: Optional[str] = None
    auto_route: bool = True


class ChatConversationResponse(BaseModel):
    reply: str
    model: str
    task_type: Optional[str] = None
    duration_ms: float = 0.0
    usage: dict = Field(default_factory=dict)


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


@router.post("/conversation", response_model=ChatConversationResponse, status_code=status.HTTP_200_OK)
async def chat_conversation(request: ChatConversationRequest):
    """
    Multi-turn conversational chat with the local LLM.
    Formats message history into a single prompt for Ollama's /api/generate endpoint.
    """
    if not request.messages:
        return ChatConversationResponse(reply="Please send a message.", model="none")

    last_user_msg = ""
    for m in reversed(request.messages):
        if m.role == "user":
            last_user_msg = m.content
            break

    task_type = None
    model_name = None
    if request.auto_route and last_user_msg:
        routing_decision = model_router.route(last_user_msg)
        model_name = routing_decision["model"]
        task_type = routing_decision["task_type"]

    history_parts = []
    for m in request.messages:
        prefix = "User" if m.role == "user" else "Assistant"
        history_parts.append(f"{prefix}: {m.content}")
    conversation_prompt = "\n".join(history_parts) + "\nAssistant:"

    system = request.system_prompt or (
        "You are ConfigIQ, a sovereign on-premise AI assistant for industrial engineering. "
        "You help with inspection reports, engineering calculations, SOP compliance, "
        "and confidential document analysis. All processing happens locally with zero external calls."
    )

    llm_request = LLMGenerateRequest(
        prompt=conversation_prompt,
        system_prompt=system,
        temperature=0.7,
        max_tokens=1500,
        model=model_name,
    )

    provider = get_llm_provider()
    response = await provider.generate(llm_request)

    audit_service.log_action(
        action="CHAT_CONVERSATION",
        component="api.chat",
        status="SUCCESS",
        duration_ms=response.duration_ms,
        details={
            "model": response.model,
            "message_count": len(request.messages),
            "task_type": task_type,
        },
    )

    return ChatConversationResponse(
        reply=response.text.strip(),
        model=response.model,
        task_type=task_type,
        duration_ms=response.duration_ms,
        usage=response.usage or {},
    )
