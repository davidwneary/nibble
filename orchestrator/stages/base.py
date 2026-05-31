"""Nibble Orchestrator — Base stage interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from config import OrchestratorConfig
from linear_client import LinearClient, LinearIssue


@dataclass
class StageResult:
    """Result of a stage handler execution."""

    success: bool
    next_state: Optional[str] = None  # State to transition to (None = no transition)
    message: str = ""  # Comment to post on the issue
    error: str = ""


class BaseStage(ABC):
    """Abstract interface for stage handlers."""

    def __init__(self, config: OrchestratorConfig, linear: LinearClient):
        self.config = config
        self.linear = linear

    @abstractmethod
    def handle(self, issue: LinearIssue) -> StageResult:
        """Process an issue in this stage. Returns a StageResult."""
        ...

    def comment(self, issue: LinearIssue, body: str) -> None:
        """Post a comment on the issue."""
        self.linear.comment_on_issue(issue.id, body)

    def transition(self, issue: LinearIssue, state: str) -> None:
        """Transition the issue to a new state."""
        self.linear.transition_issue(issue.id, state)
