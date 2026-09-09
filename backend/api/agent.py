from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, status

from backend.agents.schemas import AgentRunRequest, AgentRunResponse, ToolDefinition
from backend.agents.agent import agent_orchestrator
from backend.agents.tool_registry import tool_registry

router = APIRouter(prefix="/agent", tags=["Agent"])


def _extract_verification_summary(results: Any) -> Any:
    if not results or not isinstance(results, dict):
        return None
    if "claims" in results or "total_claims" in results:
        return results
    for v in results.values():
        if isinstance(v, dict) and ("claims" in v or "total_claims" in v):
            return v
    return results


@router.post("/run", response_model=AgentRunResponse)
async def run_agent(request: AgentRunRequest):
    """
    Trigger autonomous agent workflow for inspection review, SOP verification, or engineering calculations.
    """
    state = await agent_orchestrator.run(
        task=request.task,
        document_ids=request.document_ids,
        parameters=request.parameters
    )

    verif_summary = _extract_verification_summary(state.verification_results)

    return AgentRunResponse(
        task_id=state.task_id,
        status=state.status.value.lower(),
        plan=state.plan,
        steps_completed=len(state.completed_steps),
        final_output=state.final_output,
        sources=state.retrieved_context,
        generated_files=state.generated_files,
        verification=verif_summary,
        execution_trace=state.execution_trace,
        local=True
    )


@router.get("/tools", response_model=List[ToolDefinition])
async def list_agent_tools():
    """
    List all registered local tools and their parameter schemas.
    """
    return tool_registry.list_tools()


@router.get("/{task_id}", response_model=Dict[str, Any])
async def get_agent_state(task_id: str):
    """
    Retrieve full state, execution trace, and verification log for an agent task.
    """
    state = agent_orchestrator.get_state(task_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent task with ID '{task_id}' not found."
        )
    state_dict = state.to_dict()
    verif_summary = _extract_verification_summary(state.verification_results)
    if verif_summary:
        state_dict["verification_results"] = verif_summary
    return state_dict
