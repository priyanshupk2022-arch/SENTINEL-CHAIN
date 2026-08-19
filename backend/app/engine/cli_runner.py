import os
import json
import time
import shutil
import asyncio
import logging
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from backend.app.config import get_settings

logger = logging.getLogger("sentinel.cli_runner")

class CliExecutionResult(BaseModel):
    command: List[str]
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: float
    parsed_json: Optional[Any] = None
    timed_out: bool = False
    error: Optional[str] = None
    status_label: str = "unknown"

# Alias for backwards compatibility
CLIExecutionResult = CliExecutionResult

class BrightDataCliRunner:
    def __init__(self, api_key: Optional[str] = None, timeout: int = 120):
        settings = get_settings()
        self.api_key = api_key or settings.BRIGHT_DATA_API_KEY
        self.timeout = timeout
        self.npx_cmd = shutil.which("npx") or "npx"

    def _get_base_cmd(self) -> List[str]:
        return [self.npx_cmd, "-y", "-p", "@brightdata/cli", "bdata"]

    def build_run_command(self, collector_id: str, target_url: str) -> List[str]:
        return self._get_base_cmd() + [
            "scraper", "run", collector_id,
            "--url", target_url,
            "--json"
        ]

    def build_heal_command(self, collector_id: str, target_url: str, repair_prompt: str) -> List[str]:
        return self._get_base_cmd() + [
            "scraper", "heal", collector_id,
            "--url", target_url,
            "--", repair_prompt
        ]

    def build_approve_command(self, collector_id: str, target_url: str) -> List[str]:
        return self._get_base_cmd() + [
            "scraper", "approve", collector_id,
            "--url", target_url
        ]

    async def execute_cmd(self, cmd_args: List[str], timeout_seconds: Optional[int] = None) -> CliExecutionResult:
        timeout = float(timeout_seconds or self.timeout)
        start_time = time.time()
        env = os.environ.copy()
        if self.api_key:
            env["BRIGHT_DATA_API_KEY"] = self.api_key

        proc = None
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd_args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=timeout
                )
                stdout = stdout_bytes.decode("utf-8", errors="replace")
                stderr = stderr_bytes.decode("utf-8", errors="replace")
                duration_ms = (time.time() - start_time) * 1000.0

                parsed_json = None
                trimmed = stdout.strip()
                if (trimmed.startswith("{") and trimmed.endswith("}")) or (trimmed.startswith("[") and trimmed.endswith("]")):
                    try:
                        parsed_json = json.loads(trimmed)
                    except Exception:
                        pass

                status_label = "success" if proc.returncode == 0 else "error"
                if "awaiting_approval" in stdout.lower() or "awaiting_approval" in stderr.lower():
                    status_label = "awaiting_approval"

                return CliExecutionResult(
                    command=cmd_args,
                    exit_code=proc.returncode if proc.returncode is not None else 0,
                    stdout=stdout,
                    stderr=stderr,
                    duration_ms=duration_ms,
                    parsed_json=parsed_json,
                    timed_out=False,
                    status_label=status_label
                )
            except asyncio.TimeoutError:
                if proc:
                    try:
                        proc.kill()
                        await proc.wait()
                    except Exception:
                        pass
                duration_ms = (time.time() - start_time) * 1000.0
                return CliExecutionResult(
                    command=cmd_args,
                    exit_code=-1,
                    stdout="",
                    stderr="Execution timed out",
                    duration_ms=duration_ms,
                    timed_out=True,
                    error="TIMEOUT_EXCEEDED",
                    status_label="timeout"
                )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000.0
            return CliExecutionResult(
                command=cmd_args,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                duration_ms=duration_ms,
                error=f"SUBPROCESS_ERROR: {str(e)}",
                status_label="error"
            )

    async def run_scraper(self, collector_id: str, target_url: str, timeout_seconds: Optional[int] = None) -> CliExecutionResult:
        cmd = self.build_run_command(collector_id, target_url)
        return await self.execute_cmd(cmd, timeout_seconds=timeout_seconds)

    async def heal_scraper(self, collector_id: str, target_url: str, repair_prompt: str, timeout_seconds: Optional[int] = None) -> CliExecutionResult:
        cmd = self.build_heal_command(collector_id, target_url, repair_prompt)
        return await self.execute_cmd(cmd, timeout_seconds=timeout_seconds)

    async def approve_scraper(self, collector_id: str, target_url: str, timeout_seconds: Optional[int] = None) -> CliExecutionResult:
        cmd = self.build_approve_command(collector_id, target_url)
        return await self.execute_cmd(cmd, timeout_seconds=timeout_seconds)

# Alias for backwards compatibility
BrightDataCLIRunner = BrightDataCliRunner
