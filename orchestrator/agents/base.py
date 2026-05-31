"""Nibble Orchestrator — Base agent interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AgentResult:
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool = False


class BaseAgent(ABC):
    """Abstract interface for agent dispatch."""

    def __init__(self, command: str, flags: str, model: str, timeout_minutes: int):
        self.command = command
        self.flags = flags
        self.model = model
        self.timeout_seconds = timeout_minutes * 60

    @abstractmethod
    def dispatch(self, prompt: str, workspace: Path) -> AgentResult:
        """Run the agent with the given prompt in the given workspace.

        Returns an AgentResult indicating success/failure.
        """
        ...
