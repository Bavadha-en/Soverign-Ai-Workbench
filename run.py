#!/usr/bin/env python3
"""
ConfigIQ - Sovereign On-Premise Agentic AI Workbench
Single-command startup script for demo and development.

Usage:
    python run.py              # Start with auto-detected settings
    python run.py --mock       # Force mock LLM (no GPU needed)
    python run.py --port 9000  # Custom port
"""

import argparse
import logging
import os
import sys
import time
import webbrowser

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("configiq.launcher")

BANNER = r"""
   ____             __ _       ___ ___
  / ___|___  _ __  / _(_) __ _|_ _/ _ \
 | |   / _ \| '_ \| |_| |/ _` || | | | |
 | |__| (_) | | | |  _| | (_| || | |_| |
  \____\___/|_| |_|_| |_|\__, |___\__\_\
                          |___/
  Sovereign On-Premise Agentic AI Workbench
  Autonomous Engineering Intelligence
  100% Air-Gapped | Zero External Calls
"""


def check_ollama() -> bool:
    """Check if Ollama is running locally."""
    try:
        import httpx
        r = httpx.get("http://localhost:11434/api/tags", timeout=3.0)
        if r.status_code == 200:
            models = [m.get("name", "") for m in r.json().get("models", [])]
            logger.info("Ollama is running with %d model(s): %s", len(models), ", ".join(models[:5]))
            return True
    except Exception:
        pass
    return False


# Import name -> pip package, for every module the backend needs at start-up.
REQUIRED_MODULES = {
    "fastapi": "fastapi",
    "uvicorn": "uvicorn",
    "httpx": "httpx",
    "pydantic": "pydantic",
    "PIL": "Pillow",
    "docx": "python-docx",
    "openpyxl": "openpyxl",
    "pptx": "python-pptx",
    "psutil": "psutil",
    "pypdf": "pypdf",
    "cv2": "opencv-python",
    "numpy": "numpy",
    "rapidocr_onnxruntime": "rapidocr-onnxruntime",
}


def check_dependencies() -> list:
    """Report any missing Python dependency by its pip name."""
    missing = []
    for module, package in REQUIRED_MODULES.items():
        try:
            __import__(module)
        except ImportError:
            missing.append(package)
    return missing


def main():
    parser = argparse.ArgumentParser(description="ConfigIQ Launcher")
    parser.add_argument("--mock", action="store_true", help="Force mock LLM provider (no GPU needed)")
    parser.add_argument("--port", type=int, default=8000, help="Backend port (default: 8000)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Bind host (default: 127.0.0.1, this machine only)")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser on start")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    args = parser.parse_args()

    print(BANNER)

    # Check dependencies
    missing = check_dependencies()
    if missing:
        logger.error("Missing dependencies: %s", ", ".join(missing))
        logger.error("Run: pip install -r requirements.txt")
        sys.exit(1)
    logger.info("All Python dependencies OK")

    # Check Ollama
    ollama_ok = check_ollama()
    if args.mock or not ollama_ok:
        os.environ["LLM_PROVIDER"] = "mock"
        if not ollama_ok:
            logger.warning("Ollama not detected — using mock LLM provider")
            logger.warning("To use real models: ollama serve & ollama pull llama3:latest")
        else:
            logger.info("Mock mode forced via --mock flag")
    else:
        os.environ["LLM_PROVIDER"] = "ollama"
        logger.info("Using Ollama for local LLM inference")

    # Ensure output directories exist
    for d in ["outputs", "outputs/storage", "knowledge_base", "logs", "sandbox"]:
        os.makedirs(d, exist_ok=True)

    logger.info("Starting ConfigIQ backend on %s:%d", args.host, args.port)

    # Open browser after a short delay
    if not args.no_browser:
        import threading
        def open_browser():
            time.sleep(2)
            url = f"http://localhost:{args.port}"
            logger.info("Opening browser at %s", url)
            webbrowser.open(url)
        threading.Thread(target=open_browser, daemon=True).start()

    # Start uvicorn
    import asyncio
    import uvicorn

    # On Windows the default ProactorEventLoop tears down its accept loop when a
    # client resets a connection mid-accept (WinError 64). The process survives
    # but silently stops accepting requests, which during a demo looks like the
    # backend has died. The selector loop does not have that failure mode, and
    # nothing here needs asyncio subprocesses (the sandbox uses subprocess.run).
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        logger.info("Using selector event loop for stable connection handling")

    uvicorn.run(
        "backend.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info",
        loop="asyncio",
    )


if __name__ == "__main__":
    main()
