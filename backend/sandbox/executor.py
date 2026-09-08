import os
import sys
import tempfile
import subprocess
import time
from typing import Any, Dict, Optional


class SandboxExecutor:
    """
    Controlled Local Python Sandbox Executor for ConfigIQ.
    Provides safe, isolated execution for engineering calculations and code generation tasks.
    Enforces timeout limits, directory isolation, captured stdout/stderr, and network blocking.
    """

    # Python pre-script to disable socket/network access inside the sandboxed process
    NETWORK_GUARD_PREAMBLE = (
        "import socket\n"
        "class _BlockedSocket:\n"
        "    def __init__(self, *args, **kwargs):\n"
        "        raise PermissionError('Network access is strictly forbidden inside sovereign sandbox.')\n"
        "def _blocked_func(*args, **kwargs):\n"
        "    raise PermissionError('Network access is strictly forbidden inside sovereign sandbox.')\n"
        "socket.socket = _BlockedSocket\n"
        "socket.create_connection = _blocked_func\n"
        "socket.getaddrinfo = _blocked_func\n"
    )

    def __init__(self, workspace_dir: Optional[str] = None, default_timeout_sec: int = 10):
        self.workspace_dir = workspace_dir or os.path.join(os.getcwd(), "sandbox", "workspace")
        self.default_timeout_sec = default_timeout_sec
        os.makedirs(self.workspace_dir, exist_ok=True)

    def execute(self, code: str, timeout_sec: Optional[int] = None) -> Dict[str, Any]:
        """
        Execute python code in an isolated subprocess within the sandbox workspace.

        Args:
            code: Python code string to execute
            timeout_sec: Maximum execution time in seconds (defaults to self.default_timeout_sec)

        Returns:
            Dict containing:
                - status: "success" | "error" | "timeout"
                - stdout: str
                - stderr: str
                - exit_code: int
                - execution_time_ms: float
        """
        timeout = timeout_sec if timeout_sec is not None else self.default_timeout_sec
        start_time = time.time()

        # Guard against empty code
        if not code or not code.strip():
            return {
                "status": "error",
                "stdout": "",
                "stderr": "No code provided for execution.",
                "exit_code": -1,
                "execution_time_ms": 0.0
            }

        # Combine network guard with user code
        full_code = f"{self.NETWORK_GUARD_PREAMBLE}\n# --- User Code ---\n{code}"

        # Write to a temporary file inside the sandbox workspace
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".py",
            dir=self.workspace_dir,
            delete=False,
            encoding="utf-8"
        ) as script_file:
            script_path = script_file.name
            script_file.write(full_code)

        try:
            # Execute python interpreter in isolated subprocess
            # Set isolated environment variables to prevent leaking credentials
            env = {
                "PYTHONPATH": os.getcwd(),
                "PYTHONUNBUFFERED": "1",
                "SYSTEMROOT": os.environ.get("SYSTEMROOT", "C:\\Windows"),
                "PATH": os.environ.get("PATH", "")
            }

            process = subprocess.run(
                [sys.executable, script_path],
                cwd=self.workspace_dir,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env
            )

            duration_ms = round((time.time() - start_time) * 1000, 2)

            if process.returncode == 0:
                return {
                    "status": "success",
                    "stdout": process.stdout,
                    "stderr": process.stderr,
                    "exit_code": process.returncode,
                    "execution_time_ms": duration_ms
                }
            else:
                return {
                    "status": "error",
                    "stdout": process.stdout,
                    "stderr": process.stderr,
                    "exit_code": process.returncode,
                    "execution_time_ms": duration_ms
                }

        except subprocess.TimeoutExpired:
            duration_ms = round((time.time() - start_time) * 1000, 2)
            return {
                "status": "timeout",
                "stdout": "",
                "stderr": f"Execution timed out after {timeout} seconds.",
                "exit_code": -1,
                "execution_time_ms": duration_ms
            }
        except Exception as e:
            duration_ms = round((time.time() - start_time) * 1000, 2)
            return {
                "status": "error",
                "stdout": "",
                "stderr": f"Sandbox execution failure: {str(e)}",
                "exit_code": -1,
                "execution_time_ms": duration_ms
            }
        finally:
            # Clean up temporary script file
            if os.path.exists(script_path):
                try:
                    os.remove(script_path)
                except Exception:
                    pass


sandbox_executor = SandboxExecutor()
