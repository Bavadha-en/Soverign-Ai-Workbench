# ConfigIQ / Sovereign AI Workbench - Interactive Demonstration Guide
**SIH Problem Statement 26117: Sovereign AI Workbench for Enterprise Industrial Automation**

---

## 1. System Overview & Architecture

ConfigIQ is a 100% air-gapped, on-premise industrial AI workbench designed for high-security enterprise environments (oil & gas, defense, chemical processing, thermal power). It executes complete engineering workflows without any external API calls, cloud dependencies, or telemetry leakage.

### Available Local Open-Weight Models (Ollama)
| Model Name | Parameter Size | Specialized Task | Quantization / Context |
|---|---|---|---|
| `llama3:latest` | 8 Billion | General reasoning, compliance verification, executive approval drafting | 4-bit, 8k context |
| `qwen2.5-coder:7b` | 7 Billion | Fast engineering script generation, unit conversions, physics formulas | 4-bit, 32k context |
| `qwen2.5-coder:14b` | 14 Billion | Heavy thermodynamic simulations, complex code optimization | 4-bit, 32k context |
| `moondream:latest` | 1.8 Billion | Multimodal vision-language model for scanned documents, photos & P&IDs | 4-bit lightweight VLM |
| `nomic-embed-text:latest` | 137 Million | High-performance 768-dimensional local dense text embeddings | Local vector RAG |

---

## 2. Quickstart: Launching the Workbench

### Step 1: Confirm Local Ollama Engine
Ensure Ollama is running locally with required models loaded:
```powershell
ollama list
```

### Step 2: Start ConfigIQ

One command starts the backend and serves the console from the same origin:
```powershell
python run.py
```
Then open: `http://localhost:8000/`

The launcher checks dependencies, detects Ollama, auto-indexes the knowledge
base and reports the model it will use. No Node toolchain is required.

Useful URLs during the demo:
- Console: `http://localhost:8000/`
- API documentation: `http://localhost:8000/docs`
- Network telemetry: `http://localhost:8000/network/telemetry`
- Audit HTML report: `http://localhost:8000/audit/report`

*Developing the frontend?* Run `npm run dev` in `frontend/` and use
`http://localhost:5173/` instead; rebuild with `npm run build` before demoing.

---

## 3. DEMO 1: Scanned Inspection -> Approval Note (.docx)

### Objective
Demonstrate automated processing of noisy industrial inspection forms, cross-referencing extracted telemetry against local ISO/API engineering standards via RAG, and generating a validated Word (.docx) approval note with dynamic extraction (zero hardcoded values).

### Step-by-Step Instructions:
1. Navigate to **Workbench** in the left sidebar.
2. Upload Inspection Report A:
   - Under **Evidence**, drop or browse for `demo_data/inspection/inspection_report_P101_scanned.png` (or `inspection_report_P101_clean.pdf`).
   - Notice realistic scan artifacts, stamps, and signatures.
3. Execute Analysis:
   - Enter prompt: `"Analyze this inspection report for pump P-101. Cross-reference vibration and seal leakage against ISO 10816-3 and API 610 standards, and generate an executive approval note."`
   - Click **Run task**.
4. Observe Dynamic Execution:
   - **Step 1 (Vision/OCR):** `moondream:latest` and OCR engine extract:
     - Equipment ID: `P-101` (Heavy Crude Feed Pump)
     - Vibration Velocity: `7.4 mm/s RMS` (Horizontal Inboard Bearing)
     - Bearing Temperature: `88.5 deg C`
     - Mechanical Seal Leakage: `14 drops/min` (API Plan 53A)
   - **Step 2 (Local RAG Retrieval):** `nomic-embed-text:latest` queries ISO 10816-3 & API 610 standards.
     - ISO 10816-3 Zone C/D threshold: > 4.5 mm/s (Unacceptable).
     - API 610 Seal Leakage threshold: <= 5 drops/min.
   - **Step 3 (Reasoning & Synthesis):** `llama3:latest` classifies condition as **CRITICAL ALERT**.
   - **Step 4 (Verification):** Verifier confirms 100% of findings are grounded.
   - **Step 5 (Deliverable):** Word Tool generates `outputs/approval_notes/Inspection_Approval_Note_P-101.docx`.
5. Anti-Hardcode Dynamic Verification (Test with Report B):
   - Click **Clear run**, then attach `demo_data/inspection/inspection_report_P202_scanned.png`.
   - Enter: `"Analyze inspection report for pump P-202 and produce approval note."`
   - Verify that output dynamically reflects `P-202`, `5.1 mm/s`, `71.0 deg C`, `2 drops/min`, and **HIGH / WARNING** classification.

---

## 4. DEMO 2: P&ID Query -> Tripartite Grounded Answer

### Objective
Demonstrate multimodal interpretation of complex Process & Instrumentation Diagrams using a rigorous Tripartite Grounding structure:
1. **VISUAL EVIDENCE** (what the VLM directly sees)
2. **DOCUMENT EVIDENCE** (what the RAG retrieved from engineering standards)
3. **MODEL INFERENCE** (logical engineering deduction, explicitly separating fact from inference)

### Step-by-Step Instructions:
1. Navigate to **P&ID Diagrams** in Workbench.
2. Load Engineering Diagram: Select `demo_data/pid/pid_system_b.png` (self-made 1600x1000 process diagram).
3. Submit P&ID Query:
   `"Identify the isolation valves surrounding the primary pump suction line and describe the safety interlock procedure according to API 598 and ASME standards."`
4. Observe Tripartite Structured Output:
   - **Visual Evidence (VLM - Moondream):** Identifies pipeline headers, suction line branches, valve symbols (gate/globe), and pump block.
   - **Document Evidence (RAG - nomic-embed-text):** Retrieves API 598 Section 4 shell test requirements and ASME Section VIII isolation protocol.
   - **Model Inference (LLM - Llama 3):** Synthesizes isolation sequence with 85% grounding confidence score.

---

## 5. DEMO 3: Coding Request -> Sandbox Execution -> Multi-Sheet Excel

### Objective
Demonstrate local code generation via Qwen 2.5 Coder, safe sandboxed execution with blocked socket egress, automated mathematical verification, and formatted multi-sheet Excel spreadsheet creation.

### Step-by-Step Instructions:
1. Navigate to **Coding / Computation** tab.
2. Enter Engineering Calculation Request:
   `"Calculate the hydraulic efficiency and operating power of a centrifugal pump operating at flow rate Q = 180 m3/h, total head H = 82 m, fluid density rho = 850 kg/m3, and electrical motor shaft power Pin = 45 kW. Format the full calculation and compliance report into a multi-sheet Excel workbook."`
3. Observe Automated Workflow Execution:
   - **Router Decision:** Routes prompt to `qwen2.5-coder:7b`.
   - **Code Generation:** Generates Python calculation: P_hyd = 34.09 kW, Efficiency = 75.76%.
   - **Safe Sandbox Execution:** Runs in restricted sub-process (~105ms, exit code 0). Sockets are strictly blocked.
   - **Mathematical Verifier:** Verifier executes independent check and stamps `CALCULATION_VERIFIED`.
   - **Multi-Sheet Excel Generation:** Creates `outputs/Pump_Efficiency_Calculation.xlsx` with 4 formatted sheets (Executive Summary, Raw Inspection Findings, Computational Results, Verification Audit Trail).

---

## 6. DEMO 4: Network Sovereignty Verification & Zero External Call Proof

### Objective
Provide technical evidence that the workbench operates under 100% sovereign air-gapped constraints with zero data leakage.

### Step-by-Step Instructions:
1. Open **Network & Sovereignty** tab in UI.
2. Verify Telemetry:
   - **Status:** `LOCAL_ONLY` / `AIR-GAP VERIFIED`
   - **External AI Calls:** `0`
   - **External Application Sockets:** `0`
   - **Local Bindings:** `127.0.0.1:11434` (Ollama), `127.0.0.1:8000` (FastAPI, also serves the console)
   - **Sovereign Seal Hash:** Cryptographic SHA-256 hash (`SOVEREIGN-SEAL-...`)
3. View Audit Report: HTML download at `http://localhost:8000/audit/report`.

---

## 7. Automated Test Suite Verification

```powershell
pytest -v
```
**Status:** 92 passed in 58 seconds (100% PASS rate). Grounded across all system modules.
