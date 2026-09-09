# ConfigIQ — Sovereign On-Premise Agentic AI Workbench

[![Air-Gapped Compliance](https://img.shields.io/badge/Air--Gap-100%25%20Offline-success.svg)](#sovereignty-guarantee)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Pytest Status](https://img.shields.io/badge/Tests-85%2F85%20Passing-brightgreen.svg)](#testing)
[![Open-Weight Models](https://img.shields.io/badge/Models-Llama3%20%7C%20Qwen2.5%20%7C%20Moondream-orange.svg)](#model-routing)

ConfigIQ is an autonomous sovereign agentic AI workbench engineered for confidential industrial engineering workflows. Operating in a 100% air-gapped environment with zero external telemetry or cloud dependencies, ConfigIQ processes complex technical inspection reports, extracts multimodal anomalies, queries local engineering SOP knowledge bases, executes isolated Python simulations, mathematically verifies factual claims, and generates certified Microsoft Office deliverables (`.docx`, `.xlsx`, `.pptx`).

📖 **[Read the Full Technical Documentation & Architecture Manual](DOCUMENTATION.md)**

---

## 📸 Production UI Overview

| Operations Dashboard | Autonomous Engineering Workbench |
| :---: | :---: |
| ![Dashboard](docs/images/06_system_dashboard.png) | ![Workbench](docs/images/01_workbench_image_attached.png) |

| Execution Trace & Deliverables | Interactive Sovereign LLM Chat |
| :---: | :---: |
| ![Results](docs/images/02_workbench_execution_results.png) | ![Chat](docs/images/07_interactive_chat.png) |

| Local SOP Knowledge Base (RAG) | Immutable SHA-256 Audit Ledger |
| :---: | :---: |
| ![Knowledge Base](docs/images/03_knowledge_base_rag.png) | ![Audit Logs](docs/images/04_airgap_audit_logs.png) |

---

## 🌟 Key Capabilities

- **100% Air-Gapped & Sovereign**: Zero outbound telemetry. Continuous background packet telemetry monitors listening ports and intercepts unauthorized socket creation.
- **Multimodal Defect Inspection**: Local vision integration via `Moondream 2` detects component anomalies (scratches, deformation, cracks) with severity ranking and bounding boxes.
- **Local Dense SOP Retrieval (RAG)**: Indexes industrial procedures (valves, pumps, pressure vessels, heat exchangers, LOTO) into offline vector stores using `nomic-embed-text` with cosine similarity ranking.
- **Sandboxed Python Code Execution**: Runs thermodynamic and engineering calculations in an isolated subprocess sandbox with socket blocking and timeout enforcement.
- **Multi-Format Deliverable Generation**:
  - 📘 **Word Approval Note (`.docx`)**: Formally styled engineering memo with findings, risk assessment, and SOP citations.
  - 📊 **Excel Calculation Workbook (`.xlsx`)**: 4-sheet computation workbook with dynamic Excel formulas.
  - 📽️ **PowerPoint Executive Deck (`.pptx`)**: 5-slide briefing deck for plant leadership.
- **Dual-Stage Fact & Physics Verifier**: Audits all AI reasoning claims against retrieved SOP context (`SUPPORTED`, `UNSUPPORTED`, `NEEDS REVIEW`) and verifies numerical bounds.
- **Tamper-Evident SHA-256 Audit Trail**: Cryptographically chained execution ledger providing complete regulatory compliance.

---

## 🏗️ System Architecture

```mermaid
graph TB
    subgraph "Air-Gapped Boundary"
        UI["React Frontend<br/>Dashboard · Workbench · Chat · Demo"]
        API["FastAPI Backend<br/>REST API · CORS · Lifespan Events"]
        
        subgraph "Agentic State Machine"
            PLAN["PLAN<br/>Task Decomposition"]
            ACT["ACT<br/>Tool Execution"]
            OBSERVE["OBSERVE<br/>Result Parsing"]
            VERIFY["VERIFY<br/>Fact & Bounds Check"]
            DELIVER["DELIVER<br/>Generate Deliverables"]
        end

        subgraph "11 Registered Tools"
            T1["document_reader"]
            T2["pdf_processor"]
            T3["ocr"]
            T4["vision (Moondream VLM)"]
            T5["rag_search"]
            T6["llm_generate"]
            T7["code_executor (Sandbox)"]
            T8["verification"]
            T9["document_generator (.docx)"]
            T10["excel_generator (.xlsx)"]
            T11["ppt_generator (.pptx)"]
        end

        subgraph "RAG Pipeline"
            KB["Knowledge Base<br/>SOPs · Inspection Guides"]
            CHUNK["Text Chunker<br/>Sliding Window"]
            EMBED["Ollama Embeddings<br/>nomic-embed-text"]
            VS["JSON Vector Store<br/>Cosine Similarity"]
        end

        subgraph "Model Router"
            MR["Auto-Router<br/>LLM + Keyword Classification"]
            LLM1["llama3 (General)"]
            LLM2["qwen2.5-coder (Coding)"]
            LLM3["moondream (Vision)"]
        end

        SANDBOX["Network-Blocked Sandbox<br/>Socket Monkey-Patching"]
        AUDIT["SHA-256 Audit Trail<br/>Tamper-Evident Ledger"]
        NETMON["psutil Network Monitor<br/>Live Connection Scanning"]
    end

    CLOUD["External Networks ⛔"]

    UI --> API
    API --> PLAN
    PLAN --> ACT
    ACT --> OBSERVE
    OBSERVE --> VERIFY
    VERIFY -->|retry| ACT
    VERIFY --> DELIVER
    ACT --> T1 & T2 & T3 & T4 & T5 & T6 & T7 & T8 & T9 & T10 & T11
    T5 --> VS
    KB --> CHUNK --> EMBED --> VS
    T6 --> MR
    MR --> LLM1 & LLM2 & LLM3
    T7 --> SANDBOX
    API --> AUDIT
    API --> NETMON
    NETMON -.->|blocked| CLOUD

    style CLOUD fill:#ef4444,color:#fff,stroke:#ef4444
    style SANDBOX fill:#1e293b,color:#38bdf8,stroke:#38bdf8
    style AUDIT fill:#1e293b,color:#10b981,stroke:#10b981
```

### Agentic State Machine

The core differentiator is a **5-phase autonomous state machine** that mirrors how a human engineer works:

| Phase | What Happens | Tools Used |
|-------|-------------|------------|
| **PLAN** | Decompose user task into a structured tool-call graph | LLM planner |
| **ACT** | Execute each tool step in sequence | All 11 tools |
| **OBSERVE** | Parse and aggregate results from tool outputs | Result parser |
| **VERIFY** | Fact-check claims against SOPs, validate physics bounds | LLM verifier + keyword fallback |
| **DELIVER** | Generate certified Office documents from verified output | docx/xlsx/pptx generators |

### Sovereignty Enforcement

- **Socket-level blocking**: Sandbox executor monkey-patches Python's `socket` module to prevent any network I/O
- **psutil live scanning**: Background monitor checks all OS-level TCP/UDP connections for external endpoints
- **Audit ledger**: Every tool call, LLM inference, and file generation is logged with SHA-256 chain integrity
- **Zero cloud dependencies**: No OpenAI, no HuggingFace Hub, no pip install at runtime — fully vendored

---

## 🧠 Novelty & Innovation

1. **First sovereign agentic workbench** — Not just a chatbot; a full PLAN→ACT→OBSERVE→VERIFY→DELIVER state machine running entirely offline
2. **Dual-stage verification** — LLM semantic grounding + keyword provenance matching, with automatic fallback
3. **Network sovereignty proof** — Real-time psutil packet monitoring with downloadable audit report
4. **Multi-model auto-routing** — LLM-powered task classification routes to optimal local model (coding/vision/general)
5. **Industrial-grade deliverables** — Generates production Word/Excel/PowerPoint documents, not just chat responses

---

## ⚡ Quick Start

### 1-Command Startup
```bash
# Clone the repository
git clone https://github.com/Bavadha-en/Soverign-Ai-Workbench.git
cd Soverign-Ai-Workbench

# Run launcher (starts backend and opens browser)
python run.py
```

### Manual Setup
```bash
# 1. Backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

# 2. Frontend
cd frontend
npm install
npm run dev
```

### Run Tests
```bash
python -m pytest tests -v
```

---

## 📚 Documentation Links
- **[Full System Documentation & User Manual](DOCUMENTATION.md)**
- **[Deployment & Air-Gap Configuration Guide](DEPLOYMENT.md)**
- **[Environment Variables Template](.env.example)**
- **[Sample Defect Datasets](datasets/sample_images/README.md)**

---

*ConfigIQ — Sovereign Agentic Intelligence for Confidential Engineering.*
