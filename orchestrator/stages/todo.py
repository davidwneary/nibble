"""Nibble Orchestrator — Todo stage handler.

When the orchestrator picks up an issue in "Todo" state,
it simply transitions it to "Plan" to begin the pipeline.
"""

import logging

from config import OrchestratorConfig
from linear_client import LinearClient, LinearIssue
from stages.base import BaseStage, StageResult

logger = logging.getLogger(__name__)


class TodoStage(BaseStage):
    """Advances issues from Todo to Plan."""

    def __init__(self, config: OrchestratorConfig, linear: LinearClient):
        super().__init__(config, linear)

    def handle(self, issue: LinearIssue) -> StageResult:
        """Transition issue from Todo → Plan."""
        logger.info(f"[Todo] {issue.identifier}: Advancing to Plan stage")
        self.transition(issue, "Plan")
        return StageResult(
            success=True,
            next_state="Plan",
            message="Advanced to Plan",
        )
