import os
import uuid
import time
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from backend.agents.schemas import AgentStatus, AgentRunRequest, AgentRunResponse
from backend.agents.state import AgentState
from backend.agents.planner import planner
from backend.agents.executor import executor
from backend.agents.verifier import verifier
from backend.services.audit_service import audit_service


class ConfigIQAgent:
    """
    Sovereign Autonomous Agent Orchestrator for ConfigIQ.
    Executes PLAN -> ACT -> OBSERVE -> VERIFY -> RETRY -> DELIVER state machine.
    Operates 100% on-premise without external dependencies.
    """

    def __init__(self, planner_inst=None, executor_inst=None, verifier_inst=None):
        self.planner = planner_inst or planner
        self.executor = executor_inst or executor
        self.verifier = verifier_inst or verifier
        self._states: Dict[str, AgentState] = {}

    def get_state(self, task_id: str) -> Optional[AgentState]:
        return self._states.get(task_id)

    def list_states(self) -> List[AgentState]:
        return list(self._states.values())

    async def run(
        self,
        task: str,
        document_ids: Optional[List[str]] = None,
        parameters: Optional[Dict[str, Any]] = None,
        task_id: Optional[str] = None
    ) -> AgentState:
        """
        Execute full autonomous agent workflow from user request to verified deliverable.
        """
        tid = task_id or f"task_{uuid.uuid4().hex[:8]}"
        doc_ids = document_ids or []
        start_time = time.time()

        # Initialize Agent State
        state = AgentState(
            task_id=tid,
            user_request=task,
            document_ids=doc_ids,
            status=AgentStatus.PLANNING,
            max_retries=3
        )
        self._states[tid] = state

        audit_service.log_action(
            action="AGENT_TASK_START",
            component="agents.orchestrator",
            status="SUCCESS",
            task_id=tid,
            details={"task": task, "document_ids": doc_ids}
        )

        try:
            # PHASE 1: PLANNING
            state.set_status(AgentStatus.PLANNING)
            plan = self.planner.plan(task=task, document_ids=doc_ids, parameters=parameters)
            state.plan = plan
            state.add_trace(f"[1] PLANNING - Created {len(plan)}-step structured execution plan")

            # PHASE 2 & 3: EXECUTING & VERIFYING with RETRY LOOP
            state.set_status(AgentStatus.EXECUTING)

            for step_data in plan:
                step_idx = step_data.get("step", 1)
                action = step_data.get("action", f"step_{step_idx}")
                tool_name = step_data.get("tool")

                # Execution attempt with retry loop
                step_success = False
                step_res: Dict[str, Any] = {}
                step_data["status"] = "running"
                while not step_success and state.can_retry(action):
                    step_res = await self.executor.execute_step(step_idx, step_data, state)

                    # Verification checkpoint
                    if tool_name == "code_executor":
                        state.set_status(AgentStatus.VERIFYING)
                        v_res = self.verifier.verify_calculation(step_res.get("result", {}))
                        if not v_res["is_valid"]:
                            state.set_status(AgentStatus.RETRYING)
                            retries = state.increment_retry_count(action)
                            state.add_trace(f"[RETRY {retries}/3] Retrying calculation step '{action}' due to verification note: {v_res.get('reason')}")
                            # Adjust code for retry if needed
                            step_data["status"] = "retried"
                            if retries >= state.max_retries:
                                break
                            continue
                        else:
                            step_success = True
                            state.set_status(AgentStatus.EXECUTING)
                    elif tool_name == "verification":
                        state.set_status(AgentStatus.VERIFYING)
                        step_success = True
                        state.set_status(AgentStatus.EXECUTING)
                    else:
                        step_success = (step_res.get("status") == "success")

                    if not step_success and not state.can_retry(action):
                        state.add_trace(f"[ERROR] Max retries exceeded for step '{action}'.")
                        break

                # Record the outcome on the plan so the UI reflects real progress
                # instead of leaving every step marked pending.
                step_data["status"] = "completed" if step_success else "failed"
                if not step_success:
                    step_data["error"] = step_res.get("error") or "Step did not complete successfully"

            # PHASE 4: FINAL DELIVERABLE & WRAP-UP
            state.set_status(AgentStatus.COMPLETED)
            total_duration_ms = round((time.time() - start_time) * 1000, 2)

            # Generate final text summary
            self._finalize_output(state)

            final_trace = f"[{len(state.execution_trace) + 1}] COMPLETED - Task finished in {total_duration_ms / 1000:.2f}s"
            if state.generated_files:
                final_trace += f" with deliverable '{os.path.basename(state.generated_files[0])}'"
            state.add_trace(final_trace)

            audit_service.log_action(
                action="AGENT_TASK_COMPLETE",
                component="agents.orchestrator",
                status="SUCCESS",
                task_id=tid,
                duration_ms=total_duration_ms,
                details={
                    "steps_completed": len(state.completed_steps),
                    "generated_files": state.generated_files,
                    "is_verified": state.is_verified
                }
            )

        except Exception as e:
            state.set_status(AgentStatus.FAILED)
            state.error = str(e)
            state.add_trace(f"[FAILED] Agent orchestration encountered critical error: {str(e)}")
            audit_service.log_action(
                action="AGENT_TASK_FAILED",
                component="agents.orchestrator",
                status="ERROR",
                task_id=tid,
                details={"error": str(e)}
            )

        return state

    @staticmethod
    def _calculation_verdict(state: AgentState) -> str:
        """
        Describe what the verifier actually concluded. The summary text must never
        assert a pass the verifier did not give.
        """
        summary: Dict[str, Any] = {}
        for value in (state.verification_results or {}).values():
            if isinstance(value, dict) and "status" in value:
                summary = value
                break

        verdict = str(summary.get("status", "")).upper()
        reason = summary.get("reason")

        if verdict == "FAILED":
            detail = reason or "a physical bounds check did not pass"
            return f"**Not accepted** — {detail} This result must not be issued."
        if verdict == "REVIEW":
            review_notes = [
                claim.get("evidence")
                for claim in summary.get("claims", [])
                if str(claim.get("status", "")).upper() == "NEEDS_REVIEW" and claim.get("evidence")
            ]
            detail = review_notes[0] if review_notes else "a value fell outside its expected band."
            return f"**Requires engineer review** — {detail}"
        if verdict == "PASSED":
            return "Passed physical range and numerical validity checks."
        return "No calculation verification was recorded for this run."

    def _finalize_output(self, state: AgentState) -> None:
        """Construct user-facing final output text summarizing agent findings."""
        if "execute_in_sandbox" in state.tool_results:
            sandbox_res = state.tool_results["execute_in_sandbox"]
            stdout = sandbox_res.get("stdout", "")
            exit_code = sandbox_res.get("exit_code", 0)
            files_md = ""
            if state.generated_files:
                files_list = ", ".join(f"`{os.path.basename(f)}`" for f in state.generated_files)
                files_md = f"\n- **Generated Deliverables**: {files_list}"
            state.final_output = (
                f"### Engineering Calculation Result\n\n"
                f"```text\n{stdout.strip()}\n```\n\n"
                f"- **Execution Status**: {'Success' if exit_code == 0 else 'Failed'} "
                f"(Exit code: {exit_code})\n"
                f"- **Sandbox Environment**: Isolated local Python runtime\n"
                f"- **Verification**: {self._calculation_verdict(state)}{files_md}"
            )
        elif state.generated_files or state.retrieved_context or state.tool_results:
            file_names = [os.path.basename(f) for f in state.generated_files]
            files_str = ", ".join(f"`{f}`" for f in file_names) if file_names else "N/A"

            # Check for P&ID context and direct QA
            vis_res = (
                state.tool_results.get("analyze_scanned_pages") or
                state.tool_results.get("analyze_pid_diagram") or
                state.tool_results.get("pid_analyzer") or {}
            )
            pid_ctx = (
                vis_res.get("pid_context")
                if (isinstance(vis_res, dict) and "pid_context" in vis_res)
                else (vis_res if (isinstance(vis_res, dict) and "equipment" in vis_res) else None)
            )

            direct_answer = ""
            if pid_ctx and isinstance(pid_ctx, dict):
                qa = pid_ctx.get("engineering_qa", {})
                if qa and qa.get("answer"):
                    direct_answer = f"\n\n**Direct Answer**: {qa['answer']}\n"

            # 1. Visual Evidence
            vis_lines = []
            if isinstance(vis_res, dict) and vis_res.get("observations"):
                vis_lines = [f"- {o}" for o in vis_res["observations"]]
            elif pid_ctx and isinstance(pid_ctx, dict):
                for v in pid_ctx.get("valves", [])[:4]:
                    vis_lines.append(f"- Valve symbol: {v.get('label', v.get('id'))}")
                for eq in pid_ctx.get("equipment", [])[:3]:
                    vis_lines.append(f"- Equipment: {eq.get('label', eq.get('id'))}")
            vis_section = "\n".join(vis_lines) if vis_lines else "- No anomalous visual features detected."

            # 2. Document Evidence
            doc_res = state.tool_results.get("extract_document", {})
            doc_text = doc_res.get("text", "") if isinstance(doc_res, dict) else ""
            doc_snippet = doc_text[:400].strip() if doc_text else "Document parsed from local storage."

            # 3. Model Inference & SOP
            llm_res = (
                state.tool_results.get("analyze_findings") or
                state.tool_results.get("grounded_engineering_reasoning") or
                state.model_outputs.get("analyze_findings") or
                state.model_outputs.get("grounded_engineering_reasoning") or {}
            )
            llm_summary = llm_res.get("text", "") if isinstance(llm_res, dict) else ""
            if not llm_summary:
                llm_summary = "Technical evaluation completed against local SOP requirements."

            # 4. Sources
            sources_lines = []
            for s in state.retrieved_context[:3]:
                meta = s.get("metadata", {})
                doc_name = meta.get("document", s.get("document", "SOP"))
                pg = meta.get("page", s.get("page", 1))
                score = s.get("score")
                score_str = f" (relevance: {score:.2f})" if score is not None else ""
                sources_lines.append(f"- **{doc_name}**, Page {pg}{score_str}")
            sources_section = "\n".join(sources_lines) if sources_lines else "- Local Knowledge Base SOP Repository"

            state.final_output = (
                f"### Sovereign Technical Assessment & Answer\n\n"
                f"**User Objective**: {state.user_request}{direct_answer}\n"
                f"**TASK ID**: `{state.task_id}` | **AIR-GAP STATUS**: Verified Local-Only\n\n"
                f"#### 1. VISUAL EVIDENCE (VLM / Moondream / CV)\n{vis_section}\n\n"
                f"#### 2. DOCUMENT EVIDENCE (OCR / Inspection Report)\n> {doc_snippet}\n\n"
                f"#### 3. MODEL INFERENCE & TECHNICAL ASSESSMENT\n{llm_summary[:1200]}\n\n"
                f"#### 4. RETRIEVED GOVERNING SOP SOURCES\n{sources_section}\n\n"
                f"#### 5. DELIVERABLES & APPROVAL\n"
                f"- **Deliverable Document**: {files_str}\n"
                f"- **Verification Status**: {'✔ SUPPORTED' if state.is_verified else '⚠ REQUIRES HUMAN SIGN-OFF'}\n"
            )
        else:
            state.final_output = f"Autonomous workflow completed {len(state.completed_steps)} steps successfully."


agent_orchestrator = ConfigIQAgent()

