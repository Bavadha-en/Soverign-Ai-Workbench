from fastapi import APIRouter, status

from backend.llm.mock_provider import MockLLMProvider
from backend.models.schemas import LLMGenerateRequest, LLMGenerateResponse
from backend.services.audit_service import audit_service

router = APIRouter(prefix="/chat", tags=["LLM Chat"])

# Global mock LLM provider for Phase 1
llm_provider = MockLLMProvider()


@router.post("/generate", response_model=LLMGenerateResponse, status_code=status.HTTP_200_OK)
async def generate_response(request: LLMGenerateRequest):
    """
    Generate response via local LLM abstraction layer (uses MockLLMProvider in Phase 1).
    """
    response = await llm_provider.generate(request)

    audit_service.log_action(
        action="LLM_GENERATE",
        component="api.chat",
        status="SUCCESS",
        duration_ms=response.duration_ms,
        details={"model": response.model, "prompt_len": len(request.prompt)}
    )

    return response
