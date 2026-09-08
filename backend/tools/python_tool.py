from typing import Any, Dict, Optional
from backend.sandbox.executor import sandbox_executor


def execute_python(code: str, timeout_sec: Optional[int] = 10) -> Dict[str, Any]:
    """Execute Python calculation code in controlled sandbox environment."""
    return sandbox_executor.execute(code, timeout_sec=timeout_sec)
