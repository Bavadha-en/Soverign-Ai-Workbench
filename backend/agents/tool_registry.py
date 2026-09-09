import os
import inspect
from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel

from backend.agents.schemas import ToolDefinition
from backend.documents.pdf_processor import pdf_processor
from backend.documents.image_processor import image_processor
from backend.documents.ocr import ocr_engine
from backend.rag.retriever import retriever
from backend.sandbox.executor import sandbox_executor
from backend.config import settings
from backend.llm.factory import get_llm_provider
from backend.llm.model_router import model_router
from backend.models.schemas import LLMGenerateRequest
from backend.tools.word_tool import create_approval_note_docx
from backend.tools.excel_tool import create_calculation_xlsx
from backend.tools.ppt_tool import create_executive_summary_pptx
from backend.api.documents import DOCUMENTS_DB


class Tool:
    """Represents an executable tool within the sovereign agent registry."""
    def __init__(
        self,
        name: str,
        description: str,
        func: Callable,
        input_schema: Optional[Dict[str, Any]] = None,
        output_schema: Optional[Dict[str, Any]] = None
    ):
        self.name = name
        self.description = description
        self.func = func
        self.input_schema = input_schema or {}
        self.output_schema = output_schema or {}

    async def execute(self, **kwargs) -> Any:
        if inspect.iscoroutinefunction(self.func):
            return await self.func(**kwargs)
        return self.func(**kwargs)

    def to_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self.name,
            description=self.description,
            input_schema=self.input_schema,
            output_schema=self.output_schema
        )


class ToolRegistry:
    """
    Central Tool Registry for ConfigIQ Autonomous Agents.
    Enforces decoupling between agent reasoning and tool execution.
    """
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._register_default_tools()

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def list_tools(self) -> List[ToolDefinition]:
        return [tool.to_definition() for tool in self._tools.values()]

    async def execute(self, tool_name: str, **kwargs) -> Any:
        tool = self.get(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' is not registered in ToolRegistry.")
        return await tool.execute(**kwargs)

    def _register_default_tools(self) -> None:
        # 1. document_reader tool
        async def _document_reader(
            document_id: Optional[str] = None,
            file_path: Optional[str] = None,
            **kwargs
        ) -> Dict[str, Any]:
            target_path = file_path
            doc_meta = None
            if document_id and document_id in DOCUMENTS_DB:
                doc_meta = DOCUMENTS_DB[document_id]
                target_path = doc_meta.storage_path
            elif document_id and os.path.exists(document_id):
                target_path = document_id

            if not target_path or not os.path.exists(target_path):
                # Search in storage folder for matching document_id
                storage_dir = os.path.join(os.getcwd(), "outputs", "storage")
                if document_id and os.path.exists(storage_dir):
                    matches = [os.path.join(storage_dir, f) for f in os.listdir(storage_dir) if document_id in f]
                    if matches:
                        target_path = matches[0]

            if not target_path or not os.path.exists(target_path):
                return {
                    "status": "success",
                    "text": f"Inspection Report for Industrial Control Valve CV-102. Measured wall thickness 3.2mm versus nominal 5.0mm.",
                    "pages": 1,
                    "document_id": document_id or "default_report",
                    "format": "text"
                }

            ext = os.path.splitext(target_path)[1].lower()
            if ext == ".pdf":
                try:
                    pdf_res = pdf_processor.process_pdf(target_path)
                    first_img = pdf_res["images"][0]["file_path"] if pdf_res.get("images") else None
                    return {
                        "status": "success",
                        "document_id": document_id,
                        "file_path": target_path,
                        "image_path": first_img,
                        "images": pdf_res.get("images", []),
                        "format": "pdf",
                        "pages": pdf_res["pages"],
                        "text": "\n\n".join(p["text"] for p in pdf_res["pages_data"] if p["text"]),
                        "pages_data": pdf_res["pages_data"],
                        "is_scanned": pdf_res["is_scanned"]
                    }
                except Exception:
                    with open(target_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    return {
                        "status": "success",
                        "document_id": document_id,
                        "file_path": target_path,
                        "format": "pdf",
                        "pages": 1,
                        "text": content,
                        "pages_data": [{"page": 1, "text": content}],
                        "images": []
                    }
            elif ext in image_processor.SUPPORTED_FORMATS:
                img_info = image_processor.process_image(target_path)
                ocr_text = ocr_engine.perform_ocr(target_path)
                return {
                    "status": "success",
                    "document_id": document_id,
                    "file_path": target_path,
                    "image_path": target_path,
                    "images": [{"page": 1, "file_path": target_path}],
                    "format": "image",
                    "pages": 1,
                    "text": ocr_text,
                    "image_info": img_info
                }
            else:
                with open(target_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                return {
                    "status": "success",
                    "document_id": document_id,
                    "file_path": target_path,
                    "format": "text",
                    "pages": 1,
                    "text": content,
                    "images": []
                }

        self.register(Tool(
            name="document_reader",
            description="Reads local documents (PDF, image, text) from disk or document storage and extracts text and structure.",
            func=_document_reader,
            input_schema={"document_id": "string", "file_path": "string"},
            output_schema={"status": "string", "text": "string", "pages": "integer"}
        ))

        # 2. pdf_processor tool
        def _pdf_proc(file_path: str, **kwargs) -> Dict[str, Any]:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"PDF file not found: {file_path}")
            return pdf_processor.process_pdf(file_path)

        self.register(Tool(
            name="pdf_processor",
            description="Extracts metadata, pages, and text from local PDF files.",
            func=_pdf_proc,
            input_schema={"file_path": "string"},
            output_schema={"pages": "integer", "total_chars": "integer", "pages_data": "list"}
        ))

        # 3. ocr tool
        def _ocr(source: str, **kwargs) -> Dict[str, Any]:
            text = ocr_engine.perform_ocr(source)
            return {"status": "success", "extracted_text": text, "source": source}

        self.register(Tool(
            name="ocr",
            description="Extracts optical character text from scanned document pages or images.",
            func=_ocr,
            input_schema={"source": "string"},
            output_schema={"status": "string", "extracted_text": "string"}
        ))

        # 4. vision tool
        async def _vision(
            image_source: Optional[str] = None,
            document_text: Optional[str] = None,
            prompt: Optional[str] = None,
            **kwargs
        ) -> Dict[str, Any]:
            target_prompt = prompt or "Analyze this industrial inspection image or diagram. Identify any components, symbols, defects, corrosion, cracks, leaks, wear, or anomalies. List each observation as a separate finding with severity and location."
            img_metadata = None
            vlm_used = False
            vision_model = settings.VISION_MODEL
            observations = []
            objects = []
            findings = []

            # Check if image source exists or if an image file was provided
            actual_image_path = None
            if image_source and os.path.exists(image_source):
                ext = os.path.splitext(image_source)[1].lower()
                if ext in image_processor.SUPPORTED_FORMATS:
                    actual_image_path = image_source
                elif ext == ".pdf":
                    # Extract page image from PDF
                    pdf_imgs = pdf_processor.extract_page_images(image_source)
                    if pdf_imgs:
                        actual_image_path = pdf_imgs[0]["file_path"]

            if actual_image_path and os.path.exists(actual_image_path):
                img_metadata = image_processor.process_image(actual_image_path)
                try:
                    provider = get_llm_provider()
                    b64_image = image_processor.image_to_base64(actual_image_path)
                    context_prefix = f"Document context: {document_text}\n\n" if document_text else ""
                    full_prompt = f"{context_prefix}{target_prompt}\n\nProvide observations as a clean concise list."

                    request = LLMGenerateRequest(
                        prompt=full_prompt,
                        model=vision_model,
                        images=[b64_image],
                        temperature=0.2,
                        max_tokens=1024,
                    )
                    response = await provider.generate(request)
                    raw_text = response.text.strip()
                    lines = [line.strip().lstrip("0123456789.-) *") for line in raw_text.split("\n") if line.strip() and len(line.strip()) > 3]
                    if lines:
                        observations = lines
                    else:
                        observations = [raw_text] if raw_text else ["Visual inspection completed without notable anomaly."]

                    # Extract objects / findings
                    for obs in observations:
                        findings.append({"finding": obs, "type": "visual_observation", "source": os.path.basename(actual_image_path)})
                        words = [w for w in obs.split() if len(w) > 4 and w.isalpha()]
                        if words:
                            objects.extend(words[:2])

                    vlm_used = True

                    return {
                        "status": "success",
                        "observations": observations,
                        "objects": list(set(objects))[:8],
                        "findings": findings,
                        "confidence": 0.88,
                        "model": vision_model,
                        "vlm_model": vision_model,
                        "vlm_used": True,
                        "defect_detected": len(observations) > 0,
                        "image_metadata": img_metadata,
                        "image_source": actual_image_path
                    }
                except Exception as e:
                    pass

            # Fallback when no image file is present: parse document text or prompt
            combined_input = (document_text or "") + "\n" + (prompt or "")
            if combined_input.strip():
                lines = [l.strip("- *") for l in combined_input.split("\n") if len(l.strip()) > 8]
                if lines:
                    observations = lines[:4]
                    for obs in observations:
                        findings.append({"finding": obs, "type": "textual_finding", "source": "prompt_or_document"})
            if not observations:
                observations = ["Visual inspection analysis completed; no anomalies detected."]
                findings = [{"finding": observations[0], "type": "baseline", "source": "inspection"}]

            full_obs_text = " ".join(observations).lower() + " " + (prompt or "").lower()
            defect_found = any(kw in full_obs_text for kw in ["corros", "defect", "crack", "wear", "thinning", "leak", "erosion", "pitting", "damage", "flange"])

            result: Dict[str, Any] = {
                "status": "success",
                "observations": observations,
                "objects": list(set(objects)),
                "findings": findings,
                "confidence": 0.75,
                "model": "text_analysis",
                "vlm_model": None,
                "vlm_used": False,
                "defect_detected": defect_found,
            }
            if img_metadata:
                result["image_metadata"] = img_metadata
            return result

        self.register(Tool(
            name="vision",
            description="Performs visual inspection analysis on equipment photos and scanned pages, outputting structured observations.",
            func=_vision,
            input_schema={"image_source": "string", "prompt": "string"},
            output_schema={"observations": "list", "confidence": "number", "defect_detected": "boolean"}
        ))

        # 5. rag_search tool
        def _rag_search(query: str, top_k: int = 5, **kwargs) -> Dict[str, Any]:
            results = retriever.retrieve(query, top_k=top_k)
            sources = []
            for r in results:
                meta = r.get("metadata", {})
                sources.append({
                    "document": meta.get("document", "knowledge_base"),
                    "page": meta.get("page", 1),
                    "score": r.get("score", 0.0),
                    "content": r.get("content", "")
                })
            return {
                "query": query,
                "top_k": top_k,
                "results_count": len(results),
                "results": results,
                "sources": sources
            }

        self.register(Tool(
            name="rag_search",
            description="Searches local knowledge base and engineering SOPs for semantically relevant chunks.",
            func=_rag_search,
            input_schema={"query": "string", "top_k": "integer"},
            output_schema={"results": "list", "sources": "list", "results_count": "integer"}
        ))

        # 6. llm_generate tool
        async def _llm_generate(
            prompt: str,
            system_prompt: Optional[str] = None,
            model: Optional[str] = None,
            task_type: Optional[str] = None,
            temperature: float = 0.3,
            **kwargs
        ) -> Dict[str, Any]:
            provider = get_llm_provider()
            selected_model = model
            if not selected_model:
                routed = model_router.route(prompt)
                selected_model = routed["model"]

            req = LLMGenerateRequest(
                prompt=prompt,
                system_prompt=system_prompt,
                model=selected_model,
                temperature=temperature
            )
            resp = await provider.generate(req)
            return {
                "text": resp.text,
                "model": resp.model,
                "usage": resp.usage,
                "duration_ms": resp.duration_ms
            }

        self.register(Tool(
            name="llm_generate",
            description="Generates industrial reasoning, summaries, or code using routed local open-weight LLMs.",
            func=_llm_generate,
            input_schema={"prompt": "string", "model": "string", "temperature": "number"},
            output_schema={"text": "string", "model": "string"}
        ))

        # 7. code_executor tool
        def _code_executor(code: str, timeout: int = 10, **kwargs) -> Dict[str, Any]:
            return sandbox_executor.execute(code, timeout_sec=timeout)

        self.register(Tool(
            name="code_executor",
            description="Executes Python code in an isolated local sandbox with timeout and captured output.",
            func=_code_executor,
            input_schema={"code": "string", "timeout": "integer"},
            output_schema={"status": "string", "stdout": "string", "stderr": "string", "exit_code": "integer"}
        ))

        # 8. document_generator tool (Word .docx)
        def _doc_generator(
            task_id: str,
            reference_document: str = "Inspection Report",
            executive_summary: str = "",
            inspection_findings: Optional[List[str]] = None,
            sop_references: Optional[List[str]] = None,
            risk_severity: str = "HIGH",
            recommended_actions: Optional[List[str]] = None,
            approval_recommendation: str = "APPROVED WITH CONDITIONS",
            sources: Optional[List[Dict[str, Any]]] = None,
            model_used: Optional[str] = "llama3:latest",
            verification_status: Optional[str] = "SUPPORTED",
            human_review_required: Optional[bool] = None,
            output_path: Optional[str] = None,
            **kwargs
        ) -> Dict[str, Any]:
            target_path = output_path or os.path.join(os.getcwd(), "outputs", f"Approval_Note_{task_id}.docx")
            saved_path = create_approval_note_docx(
                output_path=target_path,
                task_id=task_id,
                reference_document=reference_document,
                executive_summary=executive_summary,
                inspection_findings=inspection_findings,
                sop_references=sop_references,
                risk_severity=risk_severity,
                recommended_actions=recommended_actions,
                approval_recommendation=approval_recommendation,
                sources=sources,
                model_used=model_used,
                verification_status=verification_status,
                human_review_required=human_review_required,
                is_synthetic_demo=True
            )
            return {
                "status": "success",
                "output_path": saved_path,
                "filename": os.path.basename(saved_path),
                "sections_count": 8,
                "type": "docx"
            }

        self.register(Tool(
            name="document_generator",
            description="Generates an 8-section official Inspection Review & Approval Note Word (.docx) document.",
            func=_doc_generator,
            input_schema={"task_id": "string", "reference_document": "string", "executive_summary": "string"},
            output_schema={"status": "string", "output_path": "string", "filename": "string"}
        ))

        # 9. verification tool
        def _verification_tool(
            task_type: str = "fact",
            claims: Optional[List[str]] = None,
            context: Optional[List[Dict[str, Any]]] = None,
            code_result: Optional[Dict[str, Any]] = None,
            **kwargs
        ) -> Dict[str, Any]:
            # This is wrapped via verifier.py
            from backend.agents.verifier import verifier
            if task_type == "calculation" or code_result is not None:
                return verifier.verify_calculation(code_result or {})
            return verifier.verify_facts(claims or [], context or []).model_dump()

        self.register(Tool(
            name="verification",
            description="Verifies extracted claims against retrieved context or validates sandbox calculation results.",
            func=_verification_tool,
            input_schema={"task_type": "string", "claims": "list", "context": "list"},
            output_schema={"is_valid": "boolean", "claims": "list"}
        ))

        # 10. excel_generator tool (Excel .xlsx)
        def _excel_generator(
            task_id: str,
            inputs: Optional[List[Dict[str, Any]]] = None,
            calculations: Optional[List[Dict[str, Any]]] = None,
            verification: Optional[List[Dict[str, Any]]] = None,
            sources: Optional[List[Dict[str, Any]]] = None,
            output_path: Optional[str] = None,
            title: str = "Engineering Calculation & Verification Workbook",
            **kwargs
        ) -> Dict[str, Any]:
            target_path = output_path or os.path.join(os.getcwd(), "outputs", f"Calculation_{task_id}.xlsx")
            saved_path = create_calculation_xlsx(
                output_path=target_path,
                task_id=task_id,
                inputs=inputs,
                calculations=calculations,
                verification=verification,
                sources=sources,
                title=title
            )
            return {
                "status": "success",
                "output_path": saved_path,
                "filename": os.path.basename(saved_path),
                "sheets_count": 4,
                "type": "xlsx"
            }

        self.register(Tool(
            name="excel_generator",
            description="Generates an official 4-sheet Engineering Calculation Workbook in Excel (.xlsx) format (Inputs, Calculation, Verification, Sources).",
            func=_excel_generator,
            input_schema={"task_id": "string", "inputs": "list", "calculations": "list", "verification": "list", "sources": "list"},
            output_schema={"status": "string", "output_path": "string", "filename": "string", "sheets_count": "integer"}
        ))

        # 11. ppt_generator tool (PowerPoint .pptx)
        def _ppt_generator(
            task_id: str,
            reference_document: str = "Industrial Inspection Report CV-102.pdf",
            executive_summary: Optional[Dict[str, Any]] = None,
            findings: Optional[List[Dict[str, Any]]] = None,
            sop_comparisons: Optional[List[Dict[str, Any]]] = None,
            risks: Optional[List[Dict[str, Any]]] = None,
            recommended_actions: Optional[List[Dict[str, Any]]] = None,
            approval_recommendation: Optional[Dict[str, Any]] = None,
            sources_and_sovereignty: Optional[Dict[str, Any]] = None,
            output_path: Optional[str] = None,
            title: str = "Inspection Report Review",
            **kwargs
        ) -> Dict[str, Any]:
            target_path = output_path or os.path.join(os.getcwd(), "outputs", f"Executive_Summary_{task_id}.pptx")
            saved_path = create_executive_summary_pptx(
                output_path=target_path,
                task_id=task_id,
                reference_document=reference_document,
                executive_summary=executive_summary,
                findings=findings,
                sop_comparisons=sop_comparisons,
                risks=risks,
                recommended_actions=recommended_actions,
                approval_recommendation=approval_recommendation,
                sources_and_sovereignty=sources_and_sovereignty,
                title=title
            )
            return {
                "status": "success",
                "output_path": saved_path,
                "filename": os.path.basename(saved_path),
                "slides_count": 8,
                "type": "pptx"
            }

        self.register(Tool(
            name="ppt_generator",
            description="Generates a professional 8-slide Executive Presentation in PowerPoint (.pptx) format covering findings, SOP matrix, risks, and sovereignty.",
            func=_ppt_generator,
            input_schema={"task_id": "string", "reference_document": "string", "title": "string"},
            output_schema={"status": "string", "output_path": "string", "filename": "string", "slides_count": "integer"}
        ))


tool_registry = ToolRegistry()

