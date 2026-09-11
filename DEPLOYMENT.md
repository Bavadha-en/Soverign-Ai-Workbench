# ConfigIQ Sovereign On-Premise Agentic AI Workbench
## Deployment & Air-Gap Operations Guide (SIH PS 26117)

This guide details the deployment of **ConfigIQ** in an air-gapped, zero-internet industrial environment (Refineries, Defence manufacturing, PSUs, Government entities).

---

## 1. Architecture Overview

ConfigIQ operates entirely on-premise on a single workstation or server with a mid-range GPU:

```
+-------------------------------------------------------------------------------+
|                       AIR-GAPPED HOST / ON-PREMISE GPU SERVER                 |
|                                                                               |
|  +---------------------------+        +------------------------------------+  |
|  | ConfigIQ React Dashboard  |        | ConfigIQ FastAPI Sovereign Backend |  |
|  | (Port 5173 / Port 80)     | <----> | (Port 8000)                        |  |
|  +---------------------------+        +-----------------+------------------+  |
|                                                         |                     |
|                                                         v                     |
|  +-------------------------------------------------------------------------+  |
|  |  Local Open-Weight Model Engine (Ollama - Port 11434)                   |  |
|  |  - General & Reasoning:    llama3:latest (8B)                           |  |
|  |  - Coding Specialist:      qwen2.5-coder:7b / qwen2.5-coder:14b         |  |
|  |  - Vision / Inspection:    moondream:latest / llava                     |  |
|  |  - Embeddings (Local):     nomic-embed-text:latest                      |  |
|  +-------------------------------------------------------------------------+  |
|                                                                               |
|  +----------------------+ +-----------------------+ +----------------------+  |
|  | Local Knowledge Base | | Python Code Sandbox   | | Deliverable Engines  |  |
|  | (SOPs, P&IDs, Chunks)| | (Network-Blocked Sockets)| (.docx, .xlsx, .pptx) |  |
|  +----------------------+ +-----------------------+ +----------------------+  |
+-------------------------------------------------------------------------------+
                 | (NO EXTERNAL INTERNET / ZERO EGRESS)
                 X [FIREWALL / AIR-GAP BOUNDARY]
```

---

## 2. Hardware & System Prerequisites

- **Host OS**: Linux (Ubuntu 22.04 LTS / RHEL 9 recommended) or Windows 10/11 / Windows Server.
- **GPU**: NVIDIA RTX 3060/4060 (8-16 GB VRAM) or RTX 3090/4090/A4000/A5000/A100.
  *(CPU fallback mode supported for demo if GPU is unavailable).*
- **RAM**: Minimum 16 GB (32 GB recommended).
- **Disk**: 50 GB SSD for model weights and offline vector store.

---

## 3. Quick Start (1-Click Launch)

### Option A: Native Mode (Fastest for Local Testing)

#### On Windows:
```cmd
start.bat
```

#### On Linux / macOS:
```bash
chmod +x start.sh
./start.sh
```

### Option B: Docker Compose (Isolated Containers)

```bash
docker-compose up -d --build
```
Access the services at:
- **Operations Console**: `http://localhost:5173`
- **Backend API Docs**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/health`
- **Network Sovereignty**: `http://localhost:8000/network/status`

### Network exposure

Every port is bound to the loopback address, so ConfigIQ is reachable only from the machine it runs on:

| Service | Native mode | Docker Compose |
|---|---|---|
| Operations Console | `localhost:5173` (Vite dev server), or served by the backend on `127.0.0.1:8000` | `127.0.0.1:5173` |
| Backend API | `127.0.0.1:8000` | `127.0.0.1:8000` |
| Ollama | `127.0.0.1:11434` (Ollama's default) | Not published; only the backend reaches it at `ollama:11434` |

Serving the console to other machines on the plant network is a deliberate step, not a default: bind to the server's LAN address, route the API through the console's `/api` proxy, and put TLS and a login in front first.

---

## 4. Offline Model Weight Provisioning (Air-Gapped Ingestion)

In an air-gapped facility, model weights are transferred via USB/secure staging media:

### Step 1: Export models on internet-connected staging machine
```bash
ollama pull llama3:latest
ollama pull qwen2.5-coder:7b
ollama pull qwen2.5-coder:14b
ollama pull moondream:latest
ollama pull nomic-embed-text:latest
```

### Step 2: Copy Ollama model directory to air-gapped server
- **Linux**: Copy `~/.ollama/models` to target host `~/.ollama/models`
- **Windows**: Copy `%USERPROFILE%\.ollama\models` to target host `%USERPROFILE%\.ollama\models`

### Docker Compose: models inside the container
The Ollama container publishes no port, so manage its models from the host with `docker exec`:
```bash
docker exec -it configiq-ollama ollama list
```
On the air-gapped server, copy the staged `models` directory into the `configiq_ollama_models` volume instead of pulling.

---

## 5. Network Sovereignty & Verification Proof

To audit and verify zero-telemetry operations for industrial security teams:

1. **Self-Contained Sandbox**: Sockets in the Python execution sandbox are blocked via socket monkey-patching and subnet isolation.
2. **Localhost Validation**: All LLM requests are verified using `is_local_url()`, rejecting any non-local URI.
3. **Forensic Audit Trail**: All model invocations, OCR actions, and document generations are stamped with an immutable UTC audit entry.
4. **Live Network Telemetry**: The UI Network Monitor and `/network/status` endpoint provide verification of 0 WAN calls and 0 egress packets.
