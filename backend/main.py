from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.agent import router as agent_router
from backend.api.chat import router as chat_router
from backend.api.documents import router as documents_router
from backend.api.knowledge import router as knowledge_router
from backend.api.logs import router as logs_router
from backend.api.tasks import router as tasks_router
from backend.llm.ollama_provider import OllamaLLMProvider
from backend.llm.registry import model_registry
from backend.models.schemas import HealthResponse

app = FastAPI(
    title="ConfigIQ - Sovereign Agentic AI Workbench API",
    description=(
        "Sovereign On-Premise Agentic AI Workbench using Open-Weight Multimodal LLMs "
        "for Confidential Industrial Work (Problem Statement 26117)."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable local CORS for frontend/development access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(agent_router)
app.include_router(documents_router)
app.include_router(knowledge_router)
app.include_router(tasks_router)
app.include_router(chat_router)
app.include_router(logs_router)

# Health check helper
ollama_probe = OllamaLLMProvider()


@app.get("/", tags=["System"])
async def root():
    """Root endpoint detailing system identity and status."""
    return {
        "system": "ConfigIQ",
        "name": "Sovereign On-Premise Agentic AI Workbench",
        "problem_statement": "26117",
        "mode": "100% Offline / Air-Gapped",
        "status": "operational",
        "docs_url": "/docs"
    }


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Health check endpoint for on-premise monitoring with local LLM & model verification."""
    ollama_available = False
    models_status = {}
    try:
        ollama_available = await ollama_probe.health_check()
        if ollama_available:
            installed = await ollama_probe.list_available_models()
            models_status = model_registry.verify_availability(installed)
    except Exception:
        ollama_available = False

    return HealthResponse(
        status="healthy",
        app_name="ConfigIQ Backend",
        version="1.0.0",
        environment="on-premise / air-gapped",
        timestamp=datetime.now(timezone.utc).isoformat(),
        ollama="available" if ollama_available else "unavailable",
        models=models_status if ollama_available else None,
        network="LOCAL_ONLY"
    )
