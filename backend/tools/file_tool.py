import os
import time
from typing import Optional, Dict, Any
from backend.models.schemas import ReadFileOutput, WriteFileOutput
from backend.services.audit_service import audit_service


def read_file(path: str, task_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Safely reads content from a local file.
    Logs action to audit_service.
    """
    start_time = time.time()
    try:
        if not os.path.exists(path):
            raise FileNotFoundError(f"File not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        duration = round((time.time() - start_time) * 1000, 2)
        audit_service.log_action(
            action="READ_FILE",
            component="tools.file_tool",
            status="SUCCESS",
            task_id=task_id,
            duration_ms=duration,
            details={"path": path, "size": len(content)}
        )
        return ReadFileOutput(
            success=True,
            path=path,
            content=content,
            file_size=len(content),
            error=None
        ).model_dump()
    except Exception as e:
        duration = round((time.time() - start_time) * 1000, 2)
        audit_service.log_action(
            action="READ_FILE",
            component="tools.file_tool",
            status="FAILURE",
            task_id=task_id,
            duration_ms=duration,
            details={"path": path, "error": str(e)}
        )
        return ReadFileOutput(
            success=False,
            path=path,
            content=None,
            file_size=None,
            error=str(e)
        ).model_dump()


def write_file(path: str, content: str, task_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Safely writes content to a local file, creating parent directories if needed.
    Logs action to audit_service.
    """
    start_time = time.time()
    try:
        dir_name = os.path.dirname(path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        bytes_written = len(content.encode("utf-8"))
        duration = round((time.time() - start_time) * 1000, 2)
        audit_service.log_action(
            action="WRITE_FILE",
            component="tools.file_tool",
            status="SUCCESS",
            task_id=task_id,
            duration_ms=duration,
            details={"path": path, "bytes_written": bytes_written}
        )
        return WriteFileOutput(
            success=True,
            path=path,
            bytes_written=bytes_written,
            error=None
        ).model_dump()
    except Exception as e:
        duration = round((time.time() - start_time) * 1000, 2)
        audit_service.log_action(
            action="WRITE_FILE",
            component="tools.file_tool",
            status="FAILURE",
            task_id=task_id,
            duration_ms=duration,
            details={"path": path, "error": str(e)}
        )
        return WriteFileOutput(
            success=False,
            path=path,
            bytes_written=0,
            error=str(e)
        ).model_dump()
