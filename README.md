# ConfigIQ - Sovereign On-Premise Agentic AI Workbench

ConfigIQ is a sovereign on-premise agentic AI workbench designed for confidential industrial engineering workflows (Problem Statement 26117). Operating in a 100% air-gapped environment with zero external telemetry, ConfigIQ processes technical inspection documents, extracts multimodal anomalies, cross-references local SOP knowledge bases, executes sandboxed engineering calculations, verifies factual and numerical accuracy, and generates certified deliverables.

---

## Phase 4 — Autonomous Agentic Architecture

ConfigIQ's Phase 4 transforms modular AI services into a fully autonomous, explainable state-machine orchestrator.

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
                             +----------------+----------------+
                             |                                 |
                     [Verification Failed]             [Verification Passed]
                     (Retry Count < 3)                         |
                             |                                 v
                             v                    +-------------------------+
                    +-----------------+           |   Document Generator    |
                    | Retry Adjuster  |           | (8-Section Word Report) |
                    +--------+--------+           +------------+------------+
                             |                                 |
                             +----------> [Re-execute]         v
                                                  +-------------------------+
                                                  |   Verified Deliverable  |
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

## Key End-to-End Demonstrations

### 1. Primary Demo: Inspection Report Review & Approval Note

One single prompt triggers autonomous multi-step reasoning:

```bash
curl -X POST http://localhost:8000/agent/run \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Analyze inspection report for control valve CV-102 and prepare an approval note.",
    "document_ids": ["doc_sample_101"]
  }'
```

**Autonomous Execution Trace:**
```text
[1] PLANNING - Created 6-step structured execution plan
[2] DOCUMENT_READER - Extracted document content (1 pages)
[3] VISION - Identified 2 structured inspection observations
[4] RAG_SEARCH - Retrieved 3 relevant SOP chunks from local vector store
[5] LLM_GENERATE - Analyzed findings using llama3:latest
[6] VERIFICATION - 4/6 claims verified against knowledge sources
[7] DOCUMENT_GENERATOR - Generated deliverable Approval_Note_task_xxxx.docx
[8] COMPLETED - Task finished in 2.28s
```

**Generated Deliverable**: `outputs/Approval_Note_<task_id>.docx` with 8 required sections:
1. Reference Document
2. Executive Summary
3. Inspection Findings
4. SOP / Manual References
5. Risk / Severity Assessment
6. Recommended Actions
7. Approval Recommendation
8. Verified Sources & Knowledge Provenance

---

### 2. Secondary Demo: Verified Engineering Calculation

```bash
curl -X POST http://localhost:8000/agent/run \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Calculate pump efficiency using flow rate of 50 m3/h, head of 60 m, and power of 11 kW."
  }'
```

**Workflow:**
1. Planner selects coding specialist model (`qwen2.5-coder:7b`).
2. Script generated and executed in local sandbox.
3. Verifier audits calculation exit code, stdout, and physical bounds ($0\% \le \eta \le 100\%$).
4. Verified result returned with intermediate steps.

---

## REST API Reference

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/health` | `GET` | Health status and local model availability |
| `/network/status` | `GET` | Air-gapped sovereignty status (`LOCAL_ONLY`) |
| `/chat/registry` | `GET` | Active open-weight model registry mappings |
| `/agent/run` | `POST` | Execute autonomous agent workflow |
| `/agent/{task_id}` | `GET` | Retrieve full agent state and execution trace |
| `/agent/tools` | `GET` | List all 9 registered local agent tools |
| `/documents/upload` | `POST` | Upload local PDF/Image document |
| `/knowledge/search` | `POST` | Query local vector store |

---

## Running the Verification Test Suite

```bash
# Run complete test suite (Phase 1, 2, 3, and 4)
pytest -v
```

All 45 automated tests pass with 100% offline local validation.
