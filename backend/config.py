import os
from urllib.parse import urlparse

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Allowed local hostnames and IP addresses for strict network sovereignty
ALLOWED_LOCAL_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "::1", "[::1]"}


def is_local_url(url: str) -> bool:
    """
    Validates if a given URL points strictly to a local address (localhost / 127.0.0.1 / ::1).
    Enforces air-gapped / on-premise network sovereignty.
    """
    if not url:
        return False
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        if not hostname:
            return False
        return hostname.lower() in ALLOWED_LOCAL_HOSTS
    except Exception:
        return False


def detect_default_llm_provider() -> str:
    """
    Detect default LLM provider. If LLM_PROVIDER is explicitly set, use it.
    Otherwise, if local Ollama instance is reachable at OLLAMA_BASE_URL, auto-select 'ollama'.
    Falls back safely to 'mock' if Ollama is not running.
    """
    env_provider = os.getenv("LLM_PROVIDER")
    if env_provider:
        return env_provider.lower().strip()

    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    try:
        import urllib.request
        req = urllib.request.Request(f"{ollama_url.rstrip('/')}/api/tags", headers={"User-Agent": "ConfigIQ"})
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            if resp.status == 200:
                return "ollama"
    except Exception:
        pass
    return "mock"


class Settings:
    """ConfigIQ On-Premise System Configuration."""

    # Server
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "on-premise / air-gapped")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

    # LLM Settings
    LLM_PROVIDER: str = detect_default_llm_provider()
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


    # Model Registry Settings (Customizable via environment variables)
    GENERAL_MODEL: str = os.getenv("GENERAL_MODEL", "llama3:latest")
    CODING_MODEL: str = os.getenv("CODING_MODEL", "qwen2.5-coder:7b")
    CODING_HEAVY_MODEL: str = os.getenv("CODING_HEAVY_MODEL", "qwen2.5-coder:7b")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
    VISION_MODEL: str = os.getenv("VISION_MODEL", "moondream")


    # Storage Paths
    STORAGE_DIR: str = os.getenv("STORAGE_DIR", "./outputs/storage")
    KNOWLEDGE_BASE_DIR: str = os.getenv("KNOWLEDGE_BASE_DIR", "./knowledge_base")
    LOGS_DIR: str = os.getenv("LOGS_DIR", "./logs")
    SANDBOX_DIR: str = os.getenv("SANDBOX_DIR", "./sandbox")


settings = Settings()
