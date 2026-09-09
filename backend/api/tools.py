from fastapi import APIRouter, status
from backend.models.schemas import (
    ReadFileInput, ReadFileOutput,
    WriteFileInput, WriteFileOutput,
    ExtractPDFInput, ExtractPDFOutput,
    PerformOCRInput, PerformOCROutput,
    SearchKnowledgeInput, SearchKnowledgeOutput,
    ExecutePythonInput, ExecutePythonOutput,
    CreateWordInput, CreateWordOutput,
    ApprovalNoteInput,
    CreateExcelInput, CreateExcelOutput
)
from backend.tools import (
    read_file,
    write_file,
    extract_pdf,
    perform_ocr,
    search_knowledge,
    execute_python,
    create_word,
    generate_approval_note,
    create_excel
)

router = APIRouter(prefix="/tools", tags=["Tools & Execution"])


@router.post("/file/read", response_model=ReadFileOutput)
async def api_read_file(input_data: ReadFileInput):
    """Safely read content from a local file."""
    return read_file(path=input_data.path)


@router.post("/file/write", response_model=WriteFileOutput)
async def api_write_file(input_data: WriteFileInput):
    """Safely write text content to a local file."""
    return write_file(path=input_data.path, content=input_data.content)


@router.post("/pdf/extract", response_model=ExtractPDFOutput)
async def api_extract_pdf(input_data: ExtractPDFInput):
    """Extract text and metadata from a local PDF file."""
    return extract_pdf(file_path=input_data.file_path)


@router.post("/ocr/perform", response_model=PerformOCROutput)
async def api_perform_ocr(input_data: PerformOCRInput):
    """Perform local OCR on an image file."""
    return perform_ocr(image_path=input_data.image_path)


@router.post("/rag/search", response_model=SearchKnowledgeOutput)
async def api_search_knowledge(input_data: SearchKnowledgeInput):
    """Search local vector database knowledge base."""
    return search_knowledge(query=input_data.query, top_k=input_data.top_k)


@router.post("/python/execute", response_model=ExecutePythonOutput)
async def api_execute_python(input_data: ExecutePythonInput):
    """Execute Python code in an isolated Docker sandbox (or process sandbox fallback)."""
    return execute_python(code=input_data.code, timeout_sec=input_data.timeout_sec)


@router.post("/word/create", response_model=CreateWordOutput)
async def api_create_word(input_data: CreateWordInput):
    """Generate a Word (.docx) document."""
    return create_word(
        output_path=input_data.output_path,
        title=input_data.title,
        sections=input_data.sections,
        subject=input_data.subject
    )


@router.post("/word/approval-note", response_model=CreateWordOutput)
async def api_generate_approval_note(input_data: ApprovalNoteInput):
    """Generate an official Phase 8 Approval Note Word document."""
    return generate_approval_note(
        output_path=input_data.output_path,
        title=input_data.title,
        subject=input_data.subject,
        background=input_data.background,
        inspection_findings=input_data.inspection_findings,
        technical_assessment=input_data.technical_assessment,
        applicable_sop=input_data.applicable_sop,
        recommended_action=input_data.recommended_action,
        approval_requested=input_data.approval_requested
    )


@router.post("/excel/create", response_model=CreateExcelOutput)
async def api_create_excel(input_data: CreateExcelInput):
    """Generate a styled Excel (.xlsx) spreadsheet."""
    return create_excel(
        output_path=input_data.output_path,
        data=input_data.data,
        sheet_name=input_data.sheet_name
    )
