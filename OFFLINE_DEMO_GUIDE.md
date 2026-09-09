# ConfigIQ — Offline Demo Guide (100% Air-Gapped)

This guide provides step-by-step instructions for demonstrating **ConfigIQ Sovereign AI Workbench** in a strictly disconnected, air-gapped environment with **Wi-Fi disabled** and **Ethernet disconnected**.

---

## 1. Pre-Flight Preparation Checklist (Before Live Demo)

Complete these verification steps on the workstation while connected to power:

### Step 1: Boot Workstation & Start Ollama
1. Power on your Windows workstation.
2. Ensure Ollama service is running. If not already running in the background, open PowerShell and run:
   ```powershell
   ollama serve
   ```
3. Verify that all 5 required local models are registered:
   ```powershell
   ollama list
   ```
   **Expected Models:**
   - `llama3:latest` (4.7 GB)
   - `qwen2.5-coder:7b` (4.7 GB)
   - `qwen2.5-coder:14b` (9.0 GB)
   - `moondream:latest` (1.7 GB)
   - `nomic-embed-text:latest` (274 MB)

### Step 2: Run Pre-Flight Offline Demo Check
Open PowerShell in the project directory:
```powershell
cd <path-to-your-clone>
python scripts\run_offline_demo_check.py
```
**Expected Terminal Output:**
```
================================
CONFIGIQ OFFLINE DEMO CHECK
================================
Ollama                   PASS
Llama                    PASS
Qwen Coder 7B            PASS
Qwen Coder 14B           PASS
Moondream                PASS
Nomic Embeddings         PASS
RAG                      PASS
OCR                      PASS
P&ID Pipeline            PASS
Sandbox                  PASS
DOCX                     PASS
XLSX                     PASS
Frontend                 PASS
External AI dependency   NONE
Offline readiness        PASS
================================
```

---

## 2. Disconnecting from Network (Physical Air-Gap)

### Step 3: Turn Off Wi-Fi and Disconnect Ethernet
1. Click the Network icon in the Windows Taskbar (or press `Win + A`).
2. Click the **Wi-Fi** quick-toggle to switch Wi-Fi **OFF**.
3. Unplug any physical RJ-45 Ethernet cables connected to the workstation.
4. Verify in PowerShell that external internet access is down:
   ```powershell
   Test-Connection -ComputerName 8.8.8.8 -Count 1 -Quiet
   ```
   *Should return `False`.*

---

## 3. Launching ConfigIQ in Air-Gapped Mode

### Step 4: 1-Click Launch
Double-click `start_offline_demo.bat` in the project root, or execute via PowerShell:
```powershell
.\start_offline_demo.bat
```

The launcher will:
1. Re-validate all local dependencies and Ollama models.
2. Launch the FastAPI backend on `http://localhost:8000`.
3. Launch the Vite Operations Console on `http://localhost:5173`.
4. Open the browser to `http://localhost:5173`.

---

## 4. Demonstrating the 5 Core Industrial Workflows (Offline)

### Workflow 1: Network Sovereignty & Socket Proof
1. Navigate to the **Network Monitor** tab in the web console (`http://localhost:5173`).
2. Point out:
   - **Air-Gap Status:** `LOCAL_ONLY` (Green badge)
   - **External AI Calls:** `0` (Zero calls to OpenAI, Anthropic, Google)
   - **Cryptographic Seal:** `SOVEREIGN-SEAL-...` SHA-256 hash.
   - **Active Listening Ports:** Strictly local loopback (`127.0.0.1:11434`, `0.0.0.0:8000`, `127.0.0.1:5173`).

### Workflow 2: Industrial Inspection to Verified Word Approval Note
1. Navigate to the **Guided Demo** or **Agent Tasks** tab.
2. Select or upload `demo_data/inspection/inspection_report_P101_clean.pdf`.
3. Enter task:
   `"Analyze this industrial equipment inspection report for centrifugal pump P-101 and prepare an official verified Approval Note DOCX."`
4. Click **Run Sovereign Agent**.
5. Watch the real-time execution:
   - PyMuPDF extracts text and tables locally.
   - Local RAG matches bearing vibration against `SOP-M-104` and `ISO 10816-3`.
   - Local `llama3:latest` synthesizes findings and action plan.
   - Verifier checks extracted values against ground truth.
   - `python-docx` outputs `outputs/Approval_Note_task_....docx`.
6. Download and open the generated Word document.

### Workflow 3: P&ID Visual Understanding & Tag Extraction
1. In the console, select `demo_data/pid/pid.png`.
2. Enter task:
   `"Analyze the piping connections and instrument tags between the inlet flow orifice FO-1035 and pressure indicator PI-1027."`
3. Observe:
   - Local RapidOCR extracts all ISA-5.1 tags (`FO-1035`, `PI-1027`, `V-1063`, etc.).
   - Local OpenCV detects valve symbols and connects piping graph.
   - Local `moondream:latest` performs visual verification.
   - Local RAG cross-references standard piping practices.
   - Local `llama3:latest` produces tripartite report (Visual Evidence, Document Evidence, Model Inference).

### Workflow 4: Code Generation, Local Sandbox & Excel Deliverable
1. Submit task:
   `"Calculate centrifugal pump hydraulic efficiency from volumetric flow rate 50 m3/h, differential pressure 6.0 bar, and 11 kW electrical power input. Validate inputs and generate an audited Excel report."`
2. Observe:
   - Model Router classifies task as `coding` and routes to `qwen2.5-coder:7b`.
   - Qwen Coder generates verified Python code.
   - Sandbox executes code locally in ~100ms with socket networking strictly blocked (`PermissionError` guard).
   - Verifier checks mathematical boundaries (efficiency = 75.76%).
   - `openpyxl` generates `outputs/Pump_Efficiency_Calculation.xlsx`.

### Workflow 5: Local RAG Knowledge Base Retrieval
1. Ask questions regarding plant SOPs, electrical isolation (LOTO), or valve maintenance.
2. Retrieval uses local `nomic-embed-text:latest` vectors stored in local JSON vector database with zero cloud retrieval.

---

## 5. Troubleshooting Matrix

| Issue | Root Cause | Solution (100% Offline) |
| :--- | :--- | :--- |
| **Ollama service not running** | Ollama daemon stopped | Open terminal and run `ollama serve`. |
| **Model missing error** | Required model tag was removed | Run `ollama list` to check installed tags. (All 5 models are already installed on this machine). |
| **Port 8000 already in use** | Stale uvicorn process running | Run `Get-Process python \| Stop-Process` in PowerShell, then restart. |
| **Port 5173 already in use** | Stale Node / Vite process running | Run `Get-Process node \| Stop-Process` in PowerShell, then restart. |
| **Frontend not loading** | Node dependencies or build missing | `cd frontend; npm run build` (all dependencies are already vendored in `node_modules`). |
| **RAG vector store empty** | New knowledge documents added without indexing | Run `python scripts\run_rag_demo.py` to auto-reindex local knowledge base. |
| **RapidOCR engine error** | ONNX Runtime initialization hiccup | Verify with `python -c "from backend.documents.ocr import ocr_engine; print(ocr_engine.is_available())"`. |

---

## 6. Critical Demo Rules

1. **NEVER reconnect Wi-Fi or Ethernet during the presentation.** The entire demonstration is designed to run 100% offline on localhost.
2. **NEVER attempt `ollama pull` or `pip install` during the presentation.** All required weights and binaries are already on disk.
3. **Keep browser tabs pointing strictly to `http://localhost:5173` and `http://localhost:8000`.**
