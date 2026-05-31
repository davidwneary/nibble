"""Nibble Orchestrator — Copilot CLI agent dispatch.

Invokes the GitHub Copilot CLI in non-interactive mode:
  copilot -p "prompt" --allow-all --autopilot -C /workspace --model X
"""

import logging
import shlex
import subprocess
from pathlib import Path

from agents.base import AgentResult, BaseAgent

logger = logging.getLogger(__name__)


class CopilotAgent(BaseAgent):
    """Dispatches work to the GitHub Copilot CLI."""

    def dispatch(self, prompt: str, workspace: Path) -> AgentResult:
        """Run copilot in non-interactive mode with the given prompt."""
        cmd = [
            self.command,
            "-p", prompt,
            "-C", str(workspace),
        ]

        # Add flags from config (e.g. "--allow-all --autopilot")
        if self.flags:
            cmd.extend(shlex.split(self.flags))

        # Add model if specified
        if self.model:
            cmd.extend(["--model", self.model])

        logger.info(
            f"Dispatching Copilot agent in {workspace} "
            f"(model={self.model}, timeout={self.timeout_seconds}s)"
        )
        logger.debug(f"Command: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                cwd=workspace,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )
            success = result.returncode == 0
            if success:
                logger.info("Copilot agent completed successfully")
            else:
                logger.warning(
                    f"Copilot agent exited with code {result.returncode}"
                )
                if result.stderr:
                    logger.warning(f"stderr: {result.stderr[:500]}")

            return AgentResult(
                success=success,
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
            )
        except subprocess.TimeoutExpired:
            logger.error(
                f"Copilot agent timed out after {self.timeout_seconds}s"
            )
            return AgentResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=f"Timed out after {self.timeout_seconds}s",
                timed_out=True,
            )
        except FileNotFoundError:
            logger.error(f"Command not found: {self.command}")
            return AgentResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=f"Command not found: {self.command}",
            )
