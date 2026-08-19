import os
import json
import time
import shutil
import asyncio
import logging
import re
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
    def __init__(self, api_key: Optional[str] = None, timeout: int = 45):
        settings = get_settings()
        self.api_key = api_key or settings.BRIGHT_DATA_API_KEY
        self.timeout = timeout
        self.npx_cmd = shutil.which("npx") or "npx"

    def _sanitize_collector_id(self, collector_id: str) -> str:
        # Validate collector ID allows alphanumeric and underscore/hyphens only
        clean_id = re.sub(r'[^a-zA-Z0-9_-]', '', collector_id)
        return clean_id or "c_sentinel_cve_threats"

    def _get_base_cmd(self) -> List[str]:
        return [self.npx_cmd, "-y", "-p", "@brightdata/cli", "bdata"]

    def build_run_command(self, collector_id: str, target_url: str) -> List[str]:
        safe_id = self._sanitize_collector_id(collector_id)
        return self._get_base_cmd() + [
            "scraper", "run", safe_id,
            "--url", target_url,
            "--json"
        ]

    def build_heal_command(self, collector_id: str, target_url: str, repair_prompt: str) -> List[str]:
        safe_id = self._sanitize_collector_id(collector_id)
        return self._get_base_cmd() + [
            "scraper", "heal", safe_id,
            "--url", target_url,
            "--",
            repair_prompt
        ]

    def build_approve_command(self, collector_id: str, target_url: Optional[str] = None) -> List[str]:
        safe_id = self._sanitize_collector_id(collector_id)
        cmd = self._get_base_cmd() + ["scraper", "approve", safe_id]
        if target_url:
            cmd.extend(["--url", target_url])
        return cmd

    async def execute_cmd(self, cmd_args: List[str], timeout_seconds: Optional[int] = None) -> CliExecutionResult:
        start_time = time.time()
        timeout = timeout_seconds or self.timeout
        env = os.environ.copy()
        if self.api_key:
            env["BRIGHTDATA_API_KEY"] = self.api_key
            env["API_TOKEN"] = self.api_key

        logger.info(f"Executing CLI command: {' '.join(cmd_args)}")

        try:
            # Use safe non-shell subprocess execution
            proc = await asyncio.create_subprocess_exec(
                cmd_args[0],
                *cmd_args[1:],
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=float(timeout)
                )
                stdout = stdout_bytes.decode("utf-8", errors="replace")
                stderr = stderr_bytes.decode("utf-8", errors="replace")
                duration_ms = (time.time() - start_time) * 1000.0
                exit_code = proc.returncode if proc.returncode is not None else 0

                # Extract JSON using robust block regex search
                parsed_json = None
                json_match = re.search(r'(\[.*\]|\{.*\})', stdout, re.DOTALL)
                if json_match:
                    try:
                        parsed_json = json.loads(json_match.group(0))
                    except Exception:
                        pass

                status_label = "success" if exit_code == 0 else "failed"
                if parsed_json and isinstance(parsed_json, dict) and "status" in parsed_json:
                    status_label = parsed_json["status"]

                return CliExecutionResult(
                    command=cmd_args,
                    exit_code=exit_code,
                    stdout=stdout,
                    stderr=stderr,
                    duration_ms=duration_ms,
                    parsed_json=parsed_json,
                    status_label=status_label
                )

            except asyncio.TimeoutError:
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
