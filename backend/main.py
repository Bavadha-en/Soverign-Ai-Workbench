import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from backend.api.agent import router as agent_router
from backend.api.chat import router as chat_router
from backend.api.documents import router as documents_router
from backend.api.knowledge import router as knowledge_router
from backend.api.logs import router as logs_router
from backend.api.tasks import router as tasks_router
from backend.api.tools import router as tools_router
from backend.llm.ollama_provider import OllamaLLMProvider
from backend.llm.registry import model_registry
from backend.models.schemas import HealthResponse
from backend.rag.ingest import ingestion_engine

logger = logging.getLogger("configiq")

@asynccontextmanager
async def lifespan(application: FastAPI):
    kb_dir = os.path.join(os.getcwd(), "knowledge_base")
    if os.path.isdir(kb_dir):
        try:
            result = ingestion_engine.ingest_directory(kb_dir)
            logger.info("Knowledge base auto-indexed: %d documents, %d chunks", result.get("documents_indexed", 0), result.get("chunks_created", 0))
        except Exception as exc:
            logger.warning("Knowledge base auto-ingest failed (non-fatal): %s", exc)
    yield


app = FastAPI(
    title="ConfigIQ - Sovereign Agentic AI Workbench API",
    description=(
        "Sovereign On-Premise Agentic AI Workbench using Open-Weight Multimodal LLMs "
        "for Confidential Industrial Work (Problem Statement 26117)."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
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
app.include_router(tools_router)


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


@app.get("/outputs/{filename:path}", tags=["Deliverables"])
async def download_output_file(filename: str):
    """
    Securely download generated deliverable files (.docx, .xlsx, .pptx) from outputs directory.
    Strictly prevents directory traversal and unauthorized filesystem access.
    """
    # Reject suspicious path traversal attempts immediately
    if ".." in filename or filename.startswith("/") or filename.startswith("\\") or ":" in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename: Path traversal is strictly forbidden."
        )

    base_output_dir = os.path.abspath(os.path.join(os.getcwd(), "outputs"))
    requested_path = os.path.abspath(os.path.join(base_output_dir, filename))

    # Verify that requested path is within the base output directory
    common_prefix = os.path.commonpath([base_output_dir, requested_path])
    if common_prefix != base_output_dir or not requested_path.startswith(base_output_dir):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Path outside outputs directory."
        )

    if not os.path.exists(requested_path) or not os.path.isfile(requested_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deliverable file '{filename}' not found."
        )

    ext = os.path.splitext(requested_path)[1].lower()
    media_types = {
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ".pdf": "application/pdf",
        ".json": "application/json",
        ".txt": "text/plain",
        ".csv": "text/csv"
    }
    media_type = media_types.get(ext, "application/octet-stream")

    return FileResponse(
        path=requested_path,
        media_type=media_type,
        filename=os.path.basename(requested_path)
    )

