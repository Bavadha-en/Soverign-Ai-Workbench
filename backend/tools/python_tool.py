import time
from typing import Optional, Dict, Any
from backend.models.schemas import ExecutePythonOutput
from backend.services.audit_service import audit_service
from backend.sandbox.executor import SandboxExecutor


def execute_python(code: str, task_id: Optional[str] = None, timeout_sec: int = 30) -> Dict[str, Any]:
    """
    Executes Python code inside the Docker sandbox (with fallback process isolation).
    Logs action to audit_service.
    """
    start_time = time.time()
    try:
        executor = SandboxExecutor(timeout_sec=timeout_sec)
        result = executor.execute(code)

        duration = round((time.time() - start_time) * 1000, 2)
        status_str = "SUCCESS" if result.get("success") else "FAILURE"

        audit_service.log_action(
            action="EXECUTE_PYTHON",
            component="tools.python_tool",
            status=status_str,
            task_id=task_id,
            duration_ms=duration,
            details={
                "exit_code": result.get("exit_code"),
                "isolation_mode": result.get("isolation_mode")
            }
        )

        return ExecutePythonOutput(
            success=result.get("success", False),
            stdout=result.get("stdout", ""),
            stderr=result.get("stderr", ""),
            exit_code=result.get("exit_code", -1),
            duration_ms=result.get("duration_ms", duration),
            isolation_mode=result.get("isolation_mode", "unknown"),
            error=result.get("stderr") if not result.get("success") else None
        ).model_dump()
    except Exception as e:
        duration = round((time.time() - start_time) * 1000, 2)
        audit_service.log_action(
            action="EXECUTE_PYTHON",
            component="tools.python_tool",
            status="FAILURE",
            task_id=task_id,
            duration_ms=duration,
            details={"error": str(e)}
        )
        return ExecutePythonOutput(
            success=False,
            stdout="",
            stderr=str(e),
            exit_code=-1,
            duration_ms=duration,
            isolation_mode="error",
            error=str(e)
        ).model_dump()
