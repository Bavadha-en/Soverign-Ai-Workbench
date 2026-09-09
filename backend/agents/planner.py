from typing import Any, Dict, List, Optional
from backend.agents.schemas import PlanStep


class Planner:
    """
    Autonomous Multi-Step Task Planner for ConfigIQ.
    Analyzes incoming user tasks and constructs a deterministic, verified step execution graph.
    """

    def plan(
        self,
        task: str,
        document_ids: Optional[List[str]] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate structured execution plan for given task.
        """
        task_lower = task.lower().strip()
        doc_ids = document_ids or []
        primary_doc_id = doc_ids[0] if doc_ids else None

        # 1. Engineering Calculation Workflow
        calc_keywords = [
            "calculate", "pump efficiency", "pressure drop", "pipe friction",
            "finite element", "equation", "formula", "computation", "flow rate", "head and power"
        ]
        if any(kw in task_lower for kw in calc_keywords):
            return self._plan_engineering_calculation(task, parameters)

        # 2. Dedicated P&ID Topological & Engineering Analysis Workflow
        pid_eng_keywords = [
            "topology", "piping connection", "extract topology", "engineering report",
            "engineering workbook", "diagram analysis", "symbol extraction"
        ]
        is_pid_eng = any(kw in task_lower for kw in pid_eng_keywords) or (
            ("p&id" in task_lower or "pid" in task_lower) and not any(k in task_lower for k in ["sop", "approval note", "pressure vessel sop"])
        )
        if is_pid_eng:
            return self._plan_pid_engineering_analysis(task, primary_doc_id, parameters)

        # 3. Document Inspection & Approval Note Workflow (Primary SIH Demo)
        doc_keywords = [
            "inspection", "approval note", "report", "sop", "valve", "corrosion",
            "review", "document", "scanned", "pdf", "generate approval"
        ]
        if any(kw in task_lower for kw in doc_keywords) or doc_ids:
            return self._plan_inspection_and_approval(task, primary_doc_id, parameters)

        # 4. General Knowledge Base & Technical Reasoning Workflow
        return self._plan_general_reasoning(task, parameters)

    def _plan_pid_engineering_analysis(
        self,
        task: str,
        document_id: Optional[str],
        parameters: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Construct verified workflow for P&ID engineering diagrams:
        1. document_reader -> 2. pid_analyzer -> 3. rag_search -> 4. llm_generate -> 5. verification -> 6. engineering_report_generator -> 7. engineering_excel_generator
        """
        drw_name = parameters.get("drawing_name", "P&ID Diagram") if parameters else "P&ID Diagram"
        plan = [
            {
                "step": 1,
                "action": "extract_document",
                "tool": "document_reader",
                "description": "Load and inspect high-resolution P&ID engineering drawing",
                "params": {"document_id": document_id, "file_path": parameters.get("file_path") if parameters else None}
            },
            {
                "step": 2,
                "action": "analyze_pid_diagram",
                "tool": "pid_analyzer",
                "description": "Execute deterministic hybrid P&ID extraction (rapid OCR tags, symbols, line topology tracing)",
                "params": {"query": task}
            },
            {
                "step": 3,
                "action": "retrieve_governing_standards",
                "tool": "rag_search",
                "description": "Retrieve governing ASME B31.3 & ISA-5.1 standards from local vector store",
                "params": {"query": f"ISA-5.1 instrument tags, piping connections, and equipment standards for {task}", "top_k": 3}
            },
            {
                "step": 4,
                "action": "grounded_engineering_reasoning",
                "tool": "llm_generate",
                "description": "Perform tripartite grounded engineering reasoning using local open-weight model",
                "params": {"prompt": task}
            },
            {
                "step": 5,
                "action": "verify_engineering_claims",
                "tool": "verification",
                "description": "Verify extracted claims against diagram visual ground facts and local SOPs",
                "params": {"task_type": "fact"}
            },
            {
                "step": 6,
                "action": "generate_engineering_report",
                "tool": "engineering_report_generator",
                "description": "Generate official 15-section verified Engineering Analysis Word (.docx) Report",
                "params": {"drawing_name": drw_name}
            },
            {
                "step": 7,
                "action": "generate_engineering_workbook",
                "tool": "engineering_excel_generator",
                "description": "Generate official 5-sheet Engineering Analysis Workbook (.xlsx)",
                "params": {"title": "P&ID Engineering Analysis Workbook"}
            }
        ]
        return plan


    def _plan_inspection_and_approval(
        self,
        task: str,
        document_id: Optional[str],
        parameters: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Construct verified workflow for industrial inspection reports:
        1. document_reader -> 2. vision -> 3. rag_search -> 4. llm_generate -> 5. verification -> 6+. deliverable generator(s)
        """
        task_lower = task.lower()
        plan = [
            {
                "step": 1,
                "action": "extract_document",
                "tool": "document_reader",
                "description": "Extract text, layout, and pages from inspection report PDF/images",
                "params": {"document_id": document_id, "file_path": parameters.get("file_path") if parameters else None}
            },
            {
                "step": 2,
                "action": "analyze_scanned_pages",
                "tool": "vision",
                "description": "Perform visual and multimodal defect analysis on inspection report",
                "params": {"prompt": task}
            },
            {
                "step": 3,
                "action": "search_maintenance_sop",
                "tool": "rag_search",
                "description": "Retrieve governing engineering SOPs and replacement procedures from local vector store",
                "params": {"query": f"standard operating procedure for {task}", "top_k": 3}
            },
            {
                "step": 4,
                "action": "analyze_findings",
                "tool": "llm_generate",
                "description": "Synthesize inspection findings with SOP guidelines to evaluate operational risk",
                "params": {"prompt": f"Analyze inspection report findings and SOP requirements for: {task}"}
            },
            {
                "step": 5,
                "action": "verify_findings",
                "tool": "verification",
                "description": "Verify extracted claims and severity ratings against retrieved SOP knowledge sources",
                "params": {"task_type": "fact"}
            }
        ]

        current_step = 6
        include_docx = True
        include_pptx = False
        include_xlsx = False

        if "all" in task_lower and ("deliverable" in task_lower or "management" in task_lower):
            include_docx = True
            include_pptx = True
            include_xlsx = True
        elif "presentation" in task_lower or "executive summary" in task_lower or "slide" in task_lower or "pptx" in task_lower or "powerpoint" in task_lower:
            include_pptx = True
            if "approval" in task_lower or "note" in task_lower or "docx" in task_lower or "word" in task_lower or "report" in task_lower:
                include_docx = True
            elif "only presentation" in task_lower or "only ppt" in task_lower:
                include_docx = False

        if "excel" in task_lower or "xlsx" in task_lower or "calculation" in task_lower or "workbook" in task_lower:
            include_xlsx = True

        if include_docx:
            plan.append({
                "step": current_step,
                "action": "generate_approval_note",
                "tool": "document_generator",
                "description": "Generate official 8-section Word (.docx) Inspection Review & Approval Note",
                "params": {
                    "reference_document": parameters.get("reference_document", "Industrial Inspection Report") if parameters else "Industrial Inspection Report",
                    "risk_severity": "HIGH",
                    "approval_recommendation": "APPROVED WITH MANDATORY REPLACEMENT UNDER SOP-M-402"
                }
            })
            current_step += 1

        if include_pptx:
            plan.append({
                "step": current_step,
                "action": "generate_presentation",
                "tool": "ppt_generator",
                "description": "Generate official 8-slide PowerPoint (.pptx) Executive Presentation",
                "params": {
                    "reference_document": parameters.get("reference_document", "Industrial Inspection Report") if parameters else "Industrial Inspection Report",
                    "title": "Inspection Report Review"
                }
            })
            current_step += 1

        if include_xlsx:
            plan.append({
                "step": current_step,
                "action": "generate_calculation_workbook",
                "tool": "excel_generator",
                "description": "Generate official 4-sheet Excel (.xlsx) Calculation & Verification Workbook",
                "params": {
                    "title": "Inspection Findings & Engineering Calculation Workbook"
                }
            })
            current_step += 1

        return plan

    def _plan_engineering_calculation(
        self,
        task: str,
        parameters: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Construct verified workflow for engineering calculation:
        1. code_generator (llm) -> 2. code_executor (sandbox) -> 3. verification -> 4. excel_generator (if requested) -> 5. synthesize_result (llm)
        """
        task_lower = task.lower()
        plan = [
            {
                "step": 1,
                "action": "generate_calculation_code",
                "tool": "llm_generate",
                "description": "Generate precise Python calculation script using local coding specialist model",
                "params": {
                    "prompt": (
                        f"Write a Python script to perform the following engineering calculation: {task}. "
                        "The script must print the results and intermediate steps cleanly."
                    ),
                    "task_type": "coding"
                }
            },
            {
                "step": 2,
                "action": "execute_in_sandbox",
                "tool": "code_executor",
                "description": "Run generated Python script inside isolated local sandbox with timeout enforcement",
                "params": {"timeout": 10}
            },
            {
                "step": 3,
                "action": "verify_calculation",
                "tool": "verification",
                "description": "Verify calculation execution exit status, numerical outputs, and physical bounds",
                "params": {"task_type": "calculation"}
            }
        ]

        current_step = 4
        # Check if workbook or deliverable requested
        calc_deliverable_keywords = ["workbook", "excel", "xlsx", "sheet", "report", "deliverable", "spreadsheet", "create"]
        if any(kw in task_lower for kw in calc_deliverable_keywords) or "calculate" in task_lower:
            plan.append({
                "step": current_step,
                "action": "generate_calculation_workbook",
                "tool": "excel_generator",
                "description": "Generate official 4-sheet Excel (.xlsx) Engineering Calculation Workbook",
                "params": {
                    "title": "Engineering Calculation & Verification Workbook"
                }
            })
            current_step += 1

        if "approval" in task_lower or "docx" in task_lower or "word" in task_lower:
            plan.append({
                "step": current_step,
                "action": "generate_approval_note",
                "tool": "document_generator",
                "description": "Generate official Word (.docx) Calculation Summary Note",
                "params": {}
            })
            current_step += 1

        plan.append({
            "step": current_step,
            "action": "synthesize_results",
            "tool": "llm_generate",
            "description": "Format engineering calculation steps and verified final answer for user",
            "params": {"prompt": f"Summarize the calculated engineering result for: {task}"}
        })

        return plan


    def _plan_general_reasoning(
        self,
        task: str,
        parameters: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Construct standard 3-step RAG and reasoning workflow.
        """
        plan = [
            {
                "step": 1,
                "action": "retrieve_context",
                "tool": "rag_search",
                "description": "Search local knowledge base for relevant engineering context",
                "params": {"query": task, "top_k": 3}
            },
            {
                "step": 2,
                "action": "generate_response",
                "tool": "llm_generate",
                "description": "Generate comprehensive response using local open-weight model",
                "params": {"prompt": task}
            },
            {
                "step": 3,
                "action": "verify_response",
                "tool": "verification",
                "description": "Verify generated statements against retrieved knowledge base context",
                "params": {"task_type": "fact"}
            }
        ]
        return plan


# Backward compatibility wrapper
class TaskPlanner(Planner):
    def plan(self, description: str):
        # Support string-only calls from legacy tests if any
        raw_plan = super().plan(task=description)
        return [step.get("description", step.get("action")) for step in raw_plan]


planner = Planner()
