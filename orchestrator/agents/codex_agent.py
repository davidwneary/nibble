"""Nibble Orchestrator — Codex CLI agent dispatch (stub).

Invokes the OpenAI Codex CLI:
  codex --full-auto "prompt"

This is a stub for future use. Switch to it by setting
`agent.active: codex` in WORKFLOW.md.
"""

import logging
import shlex
import subprocess
from pathlib import Path

from agents.base import AgentResult, BaseAgent

logger = logging.getLogger(__name__)


class CodexAgent(BaseAgent):
    """Dispatches work to the OpenAI Codex CLI."""

    def dispatch(self, prompt: str, workspace: Path) -> AgentResult:
        """Run codex in full-auto mode with the given prompt."""
        cmd = [self.command]

        # Add flags from config (e.g. "--full-auto")
        if self.flags:
            cmd.extend(shlex.split(self.flags))

        # Add the prompt as the final argument
        cmd.append(prompt)

        logger.info(
            f"Dispatching Codex agent in {workspace} "
            f"(model={self.model}, timeout={self.timeout_seconds}s)"
        )

        try:
            result = subprocess.run(
                cmd,
                cwd=workspace,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )
            return AgentResult(
                success=result.returncode == 0,
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
            )
        except subprocess.TimeoutExpired:
            logger.error(f"Codex agent timed out after {self.timeout_seconds}s")
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
                stderr=f"Command not found: {self.command}. Install with: npm install -g @openai/codex",
            )
