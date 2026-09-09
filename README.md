# ConfigIQ - Sovereign On-Premise Agentic AI Workbench

ConfigIQ is a sovereign on-premise agentic AI workbench designed for confidential industrial engineering workflows (Problem Statement 26117). Operating in a 100% air-gapped environment with zero external telemetry, ConfigIQ processes technical inspection documents, extracts multimodal anomalies, cross-references local SOP knowledge bases, executes sandboxed engineering calculations, verifies factual and numerical accuracy, and generates certified deliverables.

---

### Phase 5A — Professional Deliverable Generation Architecture

ConfigIQ's Phase 5A transforms verified agent reasoning and calculations into certified, audit-ready deliverables generated 100% locally in Word (.docx), Excel (.xlsx), and PowerPoint (.pptx).

```text
                                 +-------------------------+
                                 |       User Task         |
                                 +------------+------------+
                                              |
                                              v
                                 +-------------------------+
                                 |      Agent Planner      |
                                 | (Structured Plan Graph) |
                                 +------------+------------+
                                              |
                                              v
      +---------------------------------------------------------------------------------+
      |                                Tool Executor                                    |
      |  +-----------------+  +-----------------+  +----------------+  +-------------+  |
      |  | document_reader |  |     vision      |  |   rag_search   |  |llm_generate |  |
      |  +-----------------+  +-----------------+  +----------------+  +-------------+  |
      |  +-----------------+  +-----------------+  +----------------+                   |
      |  |  code_executor  |  |  pdf_processor  |  |      ocr       |                   |
      |  +-----------------+  +-----------------+  +----------------+                   |
      +---------------------------------------+-----------------------------------------+
                                              |
                                              v
                                 +-------------------------+
                                 |     Verifier Engine     |
                                 | - Fact Provenance Match |
                                 | - Physics/Bounds Check  |
                                 +------------+------------+
                                              |
                                              v
                                 +-------------------------+
                                 |  Deliverable Generator  |
                                 | - Word (.docx)          |
                                 | - Excel (.xlsx)         |
                                 | - PowerPoint (.pptx)    |
                                 +------------+------------+
                                              |
                                              v
                                 +-------------------------+
                                 |  Verified Deliverables  |
                                 |      (in outputs/)      |
                                 +-------------------------+
```

---

## Agent State Machine

The agent operates across explicit, serializable lifecycle states:
- **`PLANNING`**: Analyzes the objective, identifies required tools, and constructs an ordered execution graph.
- **`EXECUTING`**: Invokes tools sequentially with dynamic state context and records structured outputs.
- **`VERIFYING`**: Audits factual statements against RAG context (`SUPPORTED`, `UNSUPPORTED`, `NEEDS REVIEW`) and verifies calculation exit codes, units, and bounds.
- **`RETRYING`**: Safely re-executes failed steps with parameter corrections (enforces max 3 retries to prevent infinite loops).
- **`COMPLETED`**: Finalizes execution trace, synthesizes user response, and emits deliverables.
- **`FAILED`**: Captures diagnostic failure trace when unrecoverable errors occur.

---

## Open-Weight Model Routing

ConfigIQ routes tasks to local open-weight models via `ModelRouter`:
- **General Reasoning & Reports**: `llama3:latest`
- **Standard Coding & Engineering Scripts**: `qwen2.5-coder:7b`
- **Complex Numerical Simulation**: `qwen2.5-coder:14b`
- **Vision & Defect Analysis**: `moondream:latest`
- **Local Vector Embeddings**: `nomic-embed-text:latest`

---

## Controlled Local Code Sandbox

Engineering calculations run in an isolated local Python subprocess with strict security controls:
- **Timeout Enforcement**: Configurable (default 10s) with graceful abort.
- **Network Isolation**: Socket creation is intercepted and blocked at the runtime level.
- **Directory Isolation**: Scripts execute in dedicated `./sandbox/workspace/`.
- **Output Capture**: Stdout, stderr, and return codes are isolated and audited.

---

---

## Deliverable Specifications

### 1. Word Approval Note (.docx)
Structure:
1. **Reference Document**: Primary document metadata, page numbers.
2. **Executive Summary**: Core narrative synthesis.
3. **Inspection Findings**: Detailed observations with evidence.
4. **SOP / Manual References**: Referenced SOP clauses and specifications.
5. **Risk / Severity Assessment**: Color-coded risk level (HIGH, MEDIUM, LOW).
6. **Recommended Actions**: Prioritized actionable steps.
7. **Approval Recommendation**: Formal recommendation with human review stipulations.
8. **Verified Sources & Knowledge Provenance**: Document, page number, relevance score, and status.

### 2. Excel Calculation Workbook (.xlsx)
4 Sheets:
- **`Inputs`**: Parameter, Value, Unit, Source.
- **`Calculation`**: Step / Parameter, Formula, Substitution, Intermediate Values, Final Result, Units.
- **`Verification`**: Python Sandbox Execution status, Runtime errors check, Physical range boundary check ($0\% \le \eta \le 100\%$), Air-gapped local audit.
- **`Sources`**: Input Parameter / Finding, Source Type, Document / Reference, Page / Details, Verification Status.

### 3. PowerPoint Executive Presentation (.pptx)
8 Slides (16:9 Widescreen):
- **Slide 1**: Title Slide (Task ID, Reference Document, Date, Classification)
- **Slide 2**: Executive Summary (Overall finding, severity, conclusion, verification status)
- **Slide 3**: Detailed Inspection Findings (Table: Finding, Severity, Evidence, Source / Page)
- **Slide 4**: SOP Compliance Matrix (Table: Finding, Relevant SOP, Expected, Observed, Status)
- **Slide 5**: Risk Assessment & Prioritization (Table: Risk, Severity, Operational Impact, Priority)
- **Slide 6**: Recommended Actions & Work Order (Table: Action, Priority, Justification, Source)
- **Slide 7**: Formal Approval Recommendation & Sign-Off Requirements
- **Slide 8**: Data Provenance & Air-Gapped Sovereignty Attestation

---

## Key End-to-End Demonstrations

### 1. Primary Demo: Inspection Report Review & Multi-Deliverable Output

```bash
curl -X POST http://localhost:8000/agent/run \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Analyze this inspection report and prepare an approval note and executive summary.",
    "document_ids": ["doc_valve_inspection_report"]
  }'
```

**Autonomous Execution Trace:**
```text
[1] PLANNING - Created 7-step structured execution plan
[2] DOCUMENT_READER - Extracted document content (1 pages)
[3] VISION - Identified 2 structured inspection observations
[4] RAG_SEARCH - Retrieved 3 relevant SOP chunks from local vector store
[5] LLM_GENERATE - Analyzed findings using llama3:latest
[6] VERIFICATION - 3/3 claims verified against knowledge sources
[7] DOCUMENT_GENERATOR - Generated Word deliverable Approval_Note_task_xxxx.docx
[8] PPT_GENERATOR - Generated PowerPoint executive presentation Executive_Summary_task_xxxx.pptx
[9] COMPLETED - Task finished in 2.35s
```

**Generated Deliverables:**
- `outputs/Approval_Note_<task_id>.docx` (8 sections)
- `outputs/Executive_Summary_<task_id>.pptx` (8 widescreen slides)

---

### 2. Secondary Demo: Verified Engineering Calculation Workbook

```bash
curl -X POST http://localhost:8000/agent/run \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Calculate pump efficiency using flow rate of 50 m3/h, head of 60 m, and power of 11 kW and create a calculation workbook."
  }'
```

**Verified Results:**
- Hydraulic Power: $\approx 8.175\text{ kW}$
- Efficiency: $\approx 74.32\%$
- **Generated Deliverable**: `outputs/Calculation_<task_id>.xlsx` (4 sheets: Inputs, Calculation, Verification, Sources)

---

## REST API Reference

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/health` | `GET` | Health status and local model availability |
| `/network/status` | `GET` | Air-gapped sovereignty status (`LOCAL_ONLY`) |
| `/chat/registry` | `GET` | Active open-weight model registry mappings |
| `/agent/run` | `POST` | Execute autonomous agent workflow |
| `/agent/{task_id}` | `GET` | Retrieve full agent state and execution trace |
| `/agent/tools` | `GET` | List all 11 registered local agent tools |
| `/outputs/{filename}` | `GET` | Securely download generated deliverable files (.docx, .xlsx, .pptx) |
| `/documents/upload` | `POST` | Upload local PDF/Image document |
| `/knowledge/search` | `POST` | Query local vector store |

---

## Running the Verification Test Suite

```bash
# Run complete test suite (Phases 1, 2, 3, 4, and 5A)
pytest -v
```

All 62 automated tests pass with 100% offline local validation.

---

## Phase 5B — Interactive React Web Dashboard

ConfigIQ includes an enterprise industrial operations dashboard built with **React**, **Vite**, and **TypeScript** designed specifically for air-gapped sovereign AI workflows.

### Dashboard Architecture & Capabilities:
- **● LOCAL / AIR-GAPPED Live Attestation**: Real-time network sovereignty verification with 0 external AI telemetry.
- **Open-Weight Model Routing Matrix**: Visual registry tracking `llama3:latest`, `qwen2.5-coder:7b/14b`, `moondream:latest`, and `nomic-embed-text:latest`.
- **Autonomous Agent Execution Trace**: Step-by-step lifecycle tracking (`PLANNING` $\rightarrow$ `EXECUTING` $\rightarrow$ `VERIFYING` $\rightarrow$ `COMPLETED`).
- **Fact & Physics Verifier Panel**: Triaged claims (`SUPPORTED`, `NEEDS REVIEW`, `UNSUPPORTED`) with source provenance and human review stipulations.
- **RAG Knowledge Provenance Viewer**: Vector cosine similarity ranking and SOP chunk inspector.
- **Certified Deliverables Downloader**: One-click direct downloads for generated Word (`.docx`), Excel (`.xlsx`), and PowerPoint (`.pptx`) deliverables.
- **Forensic Audit Log Ledger**: Immutable audit trail of every tool call, sandbox execution, and local inference duration.

---

## System Startup Guide

### 1. Start the FastAPI Backend
Ensure your Python virtual environment is active, then launch the local server:
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
The backend API and Swagger UI will be available locally at `http://localhost:8000/docs`.

### 2. Start the React Frontend Dashboard
In a separate terminal, navigate to the `frontend` directory:
```bash
cd frontend
npm install
npm run dev
```
Open your browser at `http://localhost:5173` to access the ConfigIQ Sovereign Operations Console.

> **Note:** The backend server (`http://localhost:8000`) must be running before launching agent tasks in the dashboard.

