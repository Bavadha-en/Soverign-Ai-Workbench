# ConfigIQ Sovereign AI Workbench — Offline Dependency Audit
**Date & Timestamp:** 2026-09-09T19:45:00+05:30  
**Scope:** Complete repository audit of backend, frontend, models, RAG, OCR, CV, sandbox, and network monitor  
**Status:** AIR-GAP READY / ZERO EXTERNAL RUNTIME DEPENDENCIES  

---

## 1. Executive Summary

A comprehensive code-level audit was conducted across the entire ConfigIQ / Sovereign AI Workbench repository to identify and classify every dependency, import, network call, asset, and runtime requirement.

The audit confirms:
- **Zero Cloud AI Dependencies:** No OpenAI, Anthropic, Gemini, Azure, Cohere, or Hugging Face Hub runtime calls.
- **Zero Remote Frontend Assets:** No CDN scripts, remote stylesheets, Google Fonts, or external tracking/analytics. All UI components (React 18, Lucide icons, Vite) are bundled locally.
- **100% Local Model Execution:** All 5 required models (`llama3:latest`, `qwen2.5-coder:7b`, `qwen2.5-coder:14b`, `moondream:latest`, `nomic-embed-text:latest`) are verified present on the local Ollama daemon (`http://127.0.0.1:11434`).
- **100% Local RAG & Document Generation:** Embeddings run locally via Ollama; vector store is a local JSON database; OCR runs via local ONNX runtime (`rapidocr-onnxruntime`); Word, Excel, and PowerPoint files are generated entirely in-process (`python-docx`, `openpyxl`, `python-pptx`).
- **Sandbox Network Hardened:** The Python execution sandbox explicitly monkey-patches Python's `socket` module (`socket.socket`, `socket.create_connection`, `socket.getaddrinfo`) to throw `PermissionError` on any connection attempt.

---

## 2. Classification Schema

Every identified dependency and endpoint is classified into one of the following 6 standardized categories:

1. **REQUIRED AT RUNTIME:** Essential local package or component executed during normal system operation.
2. **REQUIRED ONLY DURING DEVELOPMENT/INSTALLATION:** Tooling needed only to build, test, or package the project.
3. **OPTIONAL:** Fallback component that gracefully degrades if missing.
4. **DEAD / UNUSED:** Deprecated, referenced purely for negative security testing, or documentation only.
5. **LOCALHOST ONLY:** Network-capable component strictly bound to local loopback (`127.0.0.1`, `localhost`, `0.0.0.0`).
6. **MUST BE REMOVED FOR OFFLINE DEMO:** Any external runtime internet dependency that would fail if Wi-Fi/Ethernet is disabled.

---

## 3. Detailed Component & Dependency Audit

### 3.1 Backend Python Packages (`requirements.txt` & Environment)

| Component / Package | Classification | Purpose / Runtime Behavior | Destination / Protocol | Air-Gap Risk |
| :--- | :--- | :--- | :--- | :--- |
| **FastAPI** (`fastapi>=0.100.0`) | **5. LOCALHOST ONLY** | REST API application framework | `http://0.0.0.0:8000` / `localhost` | **NONE** |
| **Uvicorn** (`uvicorn>=0.22.0`) | **5. LOCALHOST ONLY** | Local ASGI web server | Port 8000 local loopback | **NONE** |
| **Pydantic** (`pydantic>=2.0.0`) | **1. REQUIRED AT RUNTIME** | Request/response data models & validation | Local CPU in-memory | **NONE** |
| **Pydantic Settings** | **1. REQUIRED AT RUNTIME** | Local environment variable parser | Local filesystem `.env` | **NONE** |
| **Python Multipart** | **1. REQUIRED AT RUNTIME** | Local file upload parser for inspection files | Local memory / disk | **NONE** |
| **HTTPX** (`httpx>=0.24.0`) | **5. LOCALHOST ONLY** | HTTP client for Ollama local IPC | `http://127.0.0.1:11434` strictly | **NONE** (Enforced by `is_local_url()`) |
| **psutil** (`psutil>=5.9.0`) | **1. REQUIRED AT RUNTIME** | OS process & local socket telemetry daemon | Local Windows OS API (`net_connections`) | **NONE** |
| **PyMuPDF / fitz** (`PyMuPDF>=1.23.0`) | **1. REQUIRED AT RUNTIME** | PDF text and vector extraction | Local CPU in-memory | **NONE** |
| **RapidOCR** (`rapidocr-onnxruntime`) | **1. REQUIRED AT RUNTIME** | High-precision text & tag OCR on diagrams | Local ONNX Runtime weights (embedded) | **NONE** |
| **OpenCV** (`opencv-python`) | **1. REQUIRED AT RUNTIME** | Image filtering, tiling, line/symbol extraction | Local CPU in-memory | **NONE** |
| **Pillow** (`Pillow>=10.0.0`) | **1. REQUIRED AT RUNTIME** | Image loading, resizing, base64 encoding | Local CPU in-memory | **NONE** |
| **python-docx** (`python-docx>=0.8.11`) | **1. REQUIRED AT RUNTIME** | Generates verified Word approval notes | Local disk write (`outputs/`) | **NONE** |
| **openpyxl** (`openpyxl>=3.1.0`) | **1. REQUIRED AT RUNTIME** | Generates verified Excel calculation sheets | Local disk write (`outputs/`) | **NONE** |
| **python-pptx** (`python-pptx>=0.6.21`) | **1. REQUIRED AT RUNTIME** | Generates executive PowerPoint briefings | Local disk write (`outputs/`) | **NONE** |
| **PyTesseract** (`pytesseract>=0.3.10`) | **3. OPTIONAL** | Legacy fallback OCR if Tesseract binary installed | Local binary via CLI subprocess | **NONE** |
| **PyPDF** (`pypdf>=6.16.2`) | **3. OPTIONAL** | Secondary PDF fallback text reader | Local CPU in-memory | **NONE** |
| **ReportLab** (`reportlab>=5.0.1`) | **3. OPTIONAL** | Synthetic test report generator | Local CPU in-memory | **NONE** |
| **pytest / pytest-asyncio** | **2. REQUIRED ONLY DURING DEV** | Test runner for regression testing | Local CPU execution | **NONE** |
| **python-dotenv** | **2. REQUIRED ONLY DURING DEV** | Environment variable bootstrapper | Local disk read | **NONE** |

---

### 3.2 Frontend Dependencies & Assets (`frontend/`)

| Asset / Package | Classification | Purpose / Runtime Behavior | Destination / Protocol | Air-Gap Risk |
| :--- | :--- | :--- | :--- | :--- |
| **React** (`react@^18.3.1`) | **1. REQUIRED AT RUNTIME** | UI Component engine; bundled into `dist/assets` | Client browser local JS | **NONE** |
| **React DOM** (`react-dom@^18.3.1`) | **1. REQUIRED AT RUNTIME** | Virtual DOM renderer; bundled into `dist/assets` | Client browser local JS | **NONE** |
| **Lucide React** (`lucide-react@^0.475.0`) | **1. REQUIRED AT RUNTIME** | Industrial icons bundled as inline SVGs | Bundled statically by Vite | **NONE** |
| **Vite** (`vite@^5.4.2`) | **2. REQUIRED ONLY DURING DEV** | Dev server and production asset bundler | Local port 5173 / `dist/` compilation | **NONE** |
| **TypeScript** (`typescript@^5.5.3`) | **2. REQUIRED ONLY DURING DEV** | Static type checking at build time | Build time compiler | **NONE** |
| **Google Fonts** | **4. DEAD / UNUSED** | None referenced; uses system font stack | N/A (zero external font requests) | **NONE** |
| **Remote CDN Scripts/CSS** | **4. DEAD / UNUSED** | None referenced in `index.html` or code | N/A (all bundled in `dist/assets`) | **NONE** |
| **Telemetry / Analytics** | **4. DEAD / UNUSED** | Zero Google Analytics, Sentry, Mixpanel | N/A | **NONE** |
| **Favicon** | **1. REQUIRED AT RUNTIME** | Browser tab icon | Inline SVG `data:image/svg+xml,...` | **NONE** |
| **Frontend API Base URL** | **5. LOCALHOST ONLY** | API client gateway in `src/services/api.ts` | `http://localhost:8000` | **NONE** |

---

### 3.3 Artificial Intelligence Models & Embeddings (Local Ollama)

| Model Identifier | Classification | Assigned Role | Inference Engine | Air-Gap Status |
| :--- | :--- | :--- | :--- | :--- |
| **`llama3:latest`** | **5. LOCALHOST ONLY** | General engineering reasoning, synthesis, verifier | Ollama (`http://localhost:11434`) | **INSTALLED / VERIFIED** |
| **`qwen2.5-coder:7b`** | **5. LOCALHOST ONLY** | Fast code generation, physics math validation | Ollama (`http://localhost:11434`) | **INSTALLED / VERIFIED** |
| **`qwen2.5-coder:14b`** | **5. LOCALHOST ONLY** | Heavy calculation, complex simulation | Ollama (`http://localhost:11434`) | **INSTALLED / VERIFIED** |
| **`moondream:latest`** | **5. LOCALHOST ONLY** | Visual inspection, P&ID visual observation | Ollama (`http://localhost:11434`) | **INSTALLED / VERIFIED** |
| **`nomic-embed-text:latest`**| **5. LOCALHOST ONLY** | Semantic text embedding for local RAG | Ollama (`http://localhost:11434/api/embed`)| **INSTALLED / VERIFIED** |

*Verification Command:* `ollama list` confirms all 5 models are present locally on disk.

---

### 3.4 Network Endpoints, Cloud SDKs, and Security Probes

| Pattern / Endpoint | Classification | Usage in Repository | Action Taken / Status |
| :--- | :--- | :--- | :--- |
| `http://localhost:11434` | **5. LOCALHOST ONLY** | Ollama local model inference endpoint | Permitted; enforced by `is_local_url()` |
| `http://localhost:8000` | **5. LOCALHOST ONLY** | Backend FastAPI server port | Permitted; local machine IPC |
| `http://localhost:5173` | **5. LOCALHOST ONLY** | Frontend Vite development/web console port | Permitted; local browser interface |
| `https://api.openai.com` | **4. DEAD / UNUSED** | Used strictly in test suites (`run_network_sovereignty.py`, `test_network_monitor.py`, `test_phase2.py`) to verify that non-local URLs are dropped and flagged as violations | Preserved as negative test fixture; runtime code never initiates contact |
| `https://api.anthropic.com` | **4. DEAD / UNUSED** | Negative assertion test in `tests/test_phase2.py` | Preserved as negative test fixture |
| Google AI / Gemini API | **4. DEAD / UNUSED** | Zero runtime occurrences | Fully absent |
| Azure AI API | **4. DEAD / UNUSED** | Zero runtime occurrences | Fully absent |
| Hugging Face Hub | **4. DEAD / UNUSED** | Zero runtime downloads; weights are local | Fully absent |

---

### 3.5 Python Execution Sandbox Security

| Control | Classification | Implementation Detail | Status |
| :--- | :--- | :--- | :--- |
| **Subprocess Isolation** | **1. REQUIRED AT RUNTIME** | Runs in isolated subprocess with clean environment | **PASS** |
| **Socket Network Guard** | **1. REQUIRED AT RUNTIME** | `NETWORK_GUARD_PREAMBLE` in `backend/sandbox/executor.py` overrides `socket.socket`, `socket.create_connection`, `socket.getaddrinfo` with `PermissionError` | **PASS (VERIFIED)** |
| **Execution Timeout** | **1. REQUIRED AT RUNTIME** | Hard subprocess timeout (10s default) prevents hangs | **PASS** |

---

## 4. Category 6: Items That Must Be Removed

| Item | Found in Codebase? | Resolution |
| :--- | :--- | :--- |
| External Cloud AI API keys | No (Config uses local Ollama) | Clean |
| CDN Links in HTML/CSS | No (Vite local bundling) | Clean |
| Remote Google Fonts | No (Local system typography) | Clean |
| Remote WebSockets / Analytics | No (Local in-memory telemetry) | Clean |
| Automatic model pull scripts | No (Offline guards check local tags only) | Clean |

**Total Items Requiring Removal for Offline Demo:** `0` (Zero). The application codebase already implements 100% strict air-gapped sovereign architecture.

---

## 5. Audit Conclusion

The ConfigIQ Sovereign AI Workbench contains **no mandatory external runtime network dependencies**. When Wi-Fi and Ethernet are disconnected, every single workflow (Inspection, P&ID visual understanding, RAG retrieval, Qwen Coder sandbox execution, Word/Excel generation, and live network socket telemetry) operates with 100% local fidelity.
