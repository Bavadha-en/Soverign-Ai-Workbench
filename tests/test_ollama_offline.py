import pytest
import httpx

REQUIRED_OFFLINE_MODELS = [
    "llama3:latest",
    "qwen2.5-coder:7b",
    "qwen2.5-coder:14b",
    "moondream:latest",
    "nomic-embed-text:latest"
]

def test_ollama_required_models_installed_offline():
    """
    Phase 6 Verification:
    1. Queries strictly the LOCAL Ollama service (127.0.0.1:11434).
    2. Verifies the required models exist.
    3. Never attempts to pull/download a model.
    4. Never contacts the internet.
    """
    ollama_url = "http://127.0.0.1:11434"
    try:
        resp = httpx.get(f"{ollama_url}/api/tags", timeout=4.0)
    except Exception as exc:
        pytest.fail(f"Local Ollama service is not reachable at {ollama_url}: {exc}. Please start Ollama before the offline demo.")

    assert resp.status_code == 200, f"Ollama returned HTTP status {resp.status_code}"

    data = resp.json()
    installed_models = [m.get("name", "") for m in data.get("models", [])]
    
    # Normalize model names to handle :latest suffix
    normalized_installed = set()
    for name in installed_models:
        normalized_installed.add(name)
        if ":" not in name:
            normalized_installed.add(f"{name}:latest")
        elif name.endswith(":latest"):
            normalized_installed.add(name.replace(":latest", ""))

    missing_models = []
    for req_model in REQUIRED_OFFLINE_MODELS:
        req_base = req_model.replace(":latest", "")
        if req_model not in normalized_installed and req_base not in normalized_installed:
            missing_models.append(req_model)

    if missing_models:
        missing_str = ", ".join(missing_models)
        pytest.fail(
            f"Required local Ollama model(s) {missing_str} are not installed. "
            f"Install before starting the offline demo. (Installed: {installed_models})"
        )
