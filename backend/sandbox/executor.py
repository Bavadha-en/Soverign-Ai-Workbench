import os
import sys
import shutil
import tempfile
import time
import subprocess
from typing import Dict, Any, Optional

class SandboxExecutor:
    """
    Docker Sandbox Executor providing isolated Python code execution for industrial agent tasks.
    Enforces network isolation (--network none), memory/CPU resource caps, execution timeouts,
    and temporary volume isolation. Includes fallback process isolation when Docker CLI/daemon is offline.
    """

    def __init__(
        self,
        timeout_sec: int = 30,
        memory_limit: str = "512m",
        cpu_limit: str = "1.0",
        docker_image: str = "python:3.11-slim"
    ):
        self.timeout_sec = timeout_sec
        self.memory_limit = memory_limit
        self.cpu_limit = cpu_limit
        self.docker_image = docker_image
        self._docker_available: Optional[bool] = None

    def is_docker_available(self) -> bool:
        """
        Check if Docker command line interface and daemon are accessible.
        """
        if self._docker_available is not None:
            return self._docker_available

        if not shutil.which("docker"):
            self._docker_available = False
            return False

        try:
            res = subprocess.run(
                ["docker", "info"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=3
            )
            self._docker_available = (res.returncode == 0)
        except Exception:
            self._docker_available = False

        return self._docker_available

    def execute(self, code: str, input_files: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Executes Python code in an isolated sandbox.

        Returns:
            {
                "success": bool,
                "stdout": str,
                "stderr": str,
                "exit_code": int,
                "duration_ms": float,
                "isolation_mode": str
            }
        """
        start_time = time.time()
        if self.is_docker_available():
            return self._execute_docker(code, input_files, start_time)
        else:
            return self._execute_subprocess(code, input_files, start_time)

    def _execute_docker(self, code: str, input_files: Optional[Dict[str, str]], start_time: float) -> Dict[str, Any]:
        with tempfile.TemporaryDirectory() as temp_dir:
            script_path = os.path.join(temp_dir, "script.py")
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(code)

            if input_files:
                for fname, content in input_files.items():
                    target_path = os.path.join(temp_dir, fname)
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    with open(target_path, "w", encoding="utf-8") as f:
                        f.write(content)

            cmd = [
                "docker", "run", "--rm",
                "--network", "none",
                "-m", self.memory_limit,
                "--cpus", self.cpu_limit,
                "-v", f"{temp_dir}:/sandbox:rw",
                "-w", "/sandbox",
                self.docker_image,
                "python", "script.py"
            ]

            try:
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_sec
                )
                duration = round((time.time() - start_time) * 1000, 2)
                return {
                    "success": proc.returncode == 0,
                    "stdout": proc.stdout,
                    "stderr": proc.stderr,
                    "exit_code": proc.returncode,
                    "duration_ms": duration,
                    "isolation_mode": "docker"
                }
            except subprocess.TimeoutExpired:
                duration = round((time.time() - start_time) * 1000, 2)
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": f"Execution timed out after {self.timeout_sec} seconds.",
                    "exit_code": -1,
                    "duration_ms": duration,
                    "isolation_mode": "docker"
                }
            except Exception:
                return self._execute_subprocess(code, input_files, start_time)

    def _execute_subprocess(self, code: str, input_files: Optional[Dict[str, str]], start_time: float) -> Dict[str, Any]:
        with tempfile.TemporaryDirectory() as temp_dir:
            script_path = os.path.join(temp_dir, "script.py")
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(code)

            if input_files:
                for fname, content in input_files.items():
                    target_path = os.path.join(temp_dir, fname)
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    with open(target_path, "w", encoding="utf-8") as f:
                        f.write(content)

            clean_env = {
                "PATH": os.environ.get("PATH", ""),
                "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
                "PYTHONUNBUFFERED": "1"
            }

            try:
                proc = subprocess.run(
                    [sys.executable, "script.py"],
                    cwd=temp_dir,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_sec,
                    env=clean_env
                )
                duration = round((time.time() - start_time) * 1000, 2)
                return {
                    "success": proc.returncode == 0,
                    "stdout": proc.stdout,
                    "stderr": proc.stderr,
                    "exit_code": proc.returncode,
                    "duration_ms": duration,
                    "isolation_mode": "subprocess_fallback"
                }
            except subprocess.TimeoutExpired:
                duration = round((time.time() - start_time) * 1000, 2)
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": f"Execution timed out after {self.timeout_sec} seconds.",
                    "exit_code": -1,
                    "duration_ms": duration,
                    "isolation_mode": "subprocess_fallback"
                }
            except Exception as e:
                duration = round((time.time() - start_time) * 1000, 2)
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": str(e),
                    "exit_code": -1,
                    "duration_ms": duration,
                    "isolation_mode": "subprocess_fallback"
                }
