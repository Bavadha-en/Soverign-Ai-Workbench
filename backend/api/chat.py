import logging
from typing import List, Optional
from fastapi import APIRouter, status
from pydantic import BaseModel, Field

logger = logging.getLogger("configiq.chat")

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


from pydantic import BaseModel, Field, ConfigDict
from typing import Any, Dict, List, Optional, Union

class ChatMessage(BaseModel):
    model_config = ConfigDict(extra="ignore")
    role: str = Field(default="user", description="'user' or 'assistant'")
    content: Optional[str] = None
    text: Optional[str] = None

    def get_content(self) -> str:
        return (self.content or self.text or "").strip()


class ChatConversationRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    messages: Optional[List[Union[ChatMessage, Dict[str, Any]]]] = Field(default_factory=list)
    prompt: Optional[str] = None
    message: Optional[str] = None
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
    Conversational chat with local open-weight LLMs.
    Uses native chat templates, local RAG retrieval, and automatic task routing.
    """
    message_list: List[ChatMessage] = []
    if request.messages:
        for m in request.messages:
            if isinstance(m, ChatMessage):
                message_list.append(m)
            elif isinstance(m, dict):
                role = m.get("role", "user")
                content = m.get("content") or m.get("text", "")
                message_list.append(ChatMessage(role=role, content=content))
    elif request.prompt:
        message_list.append(ChatMessage(role="user", content=request.prompt))
    elif request.message:
        message_list.append(ChatMessage(role="user", content=request.message))

    if not message_list:
        return ChatConversationResponse(reply="Please provide an engineering question or topic.", model="none")

    last_user_msg = ""
    for m in reversed(message_list):
        if m.role == "user" and m.get_content():
            last_user_msg = m.get_content()
            break

    task_type = None
    model_name = None
    if request.auto_route and last_user_msg:
        routing_decision = model_router.route(last_user_msg)
        model_name = routing_decision["model"]
        task_type = routing_decision["task_type"]

    rag_context = ""
    if last_user_msg:
        try:
            from backend.rag.retriever import retriever
            rag_results = retriever.retrieve(last_user_msg, top_k=3)
            if rag_results:
                snippets = []
                for r in rag_results:
                    doc = r.get("metadata", {}).get("document", "Knowledge Base")
                    content = r.get("content", "").strip()
                    if content and len(content) > 15:
                        snippets.append(f"[{doc}]:\n{content}")
                if snippets:
                    rag_context = "\n\nRelevant Local Knowledge Base & SOP Evidence:\n" + "\n\n".join(snippets)
        except Exception as rag_err:
            logger.debug("Chat RAG retrieval skipped: %s", rag_err)

    system = request.system_prompt or (
        "You are ConfigIQ, an expert sovereign on-premise AI assistant for industrial engineering, "
        "asset integrity, and plant operations. All computation is strictly local with zero external calls.\n\n"
        "Your instructions:\n"
        "1. Answer technical questions directly, clearly, and thoroughly.\n"
        "2. Structure your response logically with clear section headers, numbered steps, key parameters, and safety guidelines.\n"
        "3. Ground your answer in any provided Standard Operating Procedures (SOPs) and industrial codes (ASME, API, ISA, ISO).\n"
        "4. Do not cut off mid-sentence and do not hallucinate external conversation turns."
    )
    if rag_context:
        system += f"{rag_context}\n\nStrictly ground your answers in the local SOP knowledge base above whenever applicable."

    formatted_messages = [{"role": "system", "content": system}]
    for m in message_list:
        c = m.get_content()
        if c:
            formatted_messages.append({"role": "assistant" if m.role == "assistant" else "user", "content": c})

    provider = get_llm_provider()
    try:
        if hasattr(provider, "chat"):
            response = await provider.chat(
                messages=formatted_messages,
                model=model_name,
                temperature=0.4,
                max_tokens=2048,
            )
        else:
            conversation_prompt = "\n".join(f"{m['role'].capitalize()}: {m['content']}" for m in formatted_messages if m['role'] != 'system') + "\nAssistant:"
            llm_request = LLMGenerateRequest(
                prompt=conversation_prompt,
                system_prompt=system,
                temperature=0.4,
                max_tokens=2048,
                model=model_name,
            )
            response = await provider.generate(llm_request)
    except Exception as exc:
        logger.warning("Primary LLM provider failed (%s); falling back to sovereign domain engine.", exc)
        from backend.llm.mock_provider import MockLLMProvider
        fallback = MockLLMProvider()
        if hasattr(fallback, "chat"):
            response = await fallback.chat(messages=formatted_messages, model=model_name)
        else:
            llm_request = LLMGenerateRequest(
                prompt=last_user_msg or "Engineering assessment",
                system_prompt=system,
                temperature=0.4,
                max_tokens=2048,
                model=model_name,
            )
            response = await fallback.generate(llm_request)

    reply_text = response.text.strip()
    # Strip any accidental multi-turn simulation artifacts
    for stop_seq in ["\nUser:", "\nHuman:", "\n### User:", "\n\nUser:"]:
        if stop_seq in reply_text:
            reply_text = reply_text.split(stop_seq)[0].strip()

    audit_service.log_action(
        action="CHAT_CONVERSATION",
        component="api.chat",
        status="SUCCESS",
        duration_ms=response.duration_ms,
        details={
            "model": response.model,
            "message_count": len(message_list),
            "task_type": task_type,
        },
    )

    return ChatConversationResponse(
        reply=reply_text,
        model=response.model,
        task_type=task_type,
        duration_ms=response.duration_ms,
        usage=response.usage or {},
    )
