# ConfigIQ - Sovereign On-Premise Agentic AI Workbench

ConfigIQ is an air-gapped, sovereign agentic AI workbench built for confidential industrial work. It processes local documents, extracts insights, searches local knowledge bases, executes agentic multi-step workflows, runs sandboxed code, and generates Word/Excel reports without external cloud dependencies.

## Key Features

- **100% Air-Gapped**: Zero external cloud API calls or telemetry.
- **Local Document Pipeline**: PyMuPDF & Tesseract local OCR for scanned PDFs.
- **Local RAG**: Vector search with ChromaDB & Sentence Transformers.
- **Agentic Workflows**: Multi-step task planning and execution via LangGraph.
- **Local LLM Abstraction**: Plug-and-play local LLM API integration with Mock fallback.
- **Docker Sandbox**: Secure execution environment for generated code.
- **Report Generation**: Automated Word (`.docx`) and Excel (`.xlsx`) creation.
- **Audit Trace**: Full step-by-step task logging and network sovereignty tracking.

## Getting Started

### Prerequisites
- Python 3.11+
- Tesseract OCR (local installation for scanned document OCR)
- Docker (for Python sandbox execution)

### Installation

1. Navigate to the project root:
   ```bash
   cd ConfigIQ
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run backend server:
   ```bash
   uvicorn backend.main:app --reload
   ```

4. Access API Documentation:
   - Interactive Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
   - ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Running Tests

Run test suite:
```bash
pytest tests/
```
