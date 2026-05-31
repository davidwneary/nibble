"""Nibble Orchestrator — Plan stage handler.

When an issue enters the "Plan" state, this handler:
1. Invokes the agent with a planning-specific prompt
2. Posts the plan as a Linear comment (acceptance criteria, assumptions, trade-offs)
3. Auto-transitions to "Implement"
"""

import logging

from agents.base import BaseAgent
from config import OrchestratorConfig
from linear_client import LinearClient, LinearIssue
from stages.base import BaseStage, StageResult

logger = logging.getLogger(__name__)

PLAN_PROMPT = """You are a technical planner for the Nibble project.

## Your Task

Create a detailed implementation plan for the following Linear issue.
Do NOT write any code. Only produce a plan.

## Issue
Key: {issue_key}
Title: {issue_title}
Description:
{issue_description}

## Instructions

1. Read AGENTS.md in the repo root for project context and conventions.
2. Read relevant docs from /docs/ (architecture, schema, conventions).
3. Identify which files and modules will be affected.
4. Produce a structured plan with these sections:

### Output Format (write ONLY this, nothing else):

**Acceptance Criteria:**
- (What must be true for this to be considered done?)

**Implementation Steps:**
1. (Ordered steps to implement this feature/fix)

**Files to Modify/Create:**
- (List of file paths)

**Assumptions:**
- (What are you assuming about the codebase, requirements, or environment?)

**Trade-offs:**
- (Any trade-offs being made and why)

**Deliberately Omitted:**
- (What is NOT being done and why)

**Estimated Complexity:** (Low / Medium / High)

## Constraints
- Do NOT write any code — plan only
- Be specific about file paths and function names where possible
- Reference existing patterns in the codebase
"""


class PlanStage(BaseStage):
    """Handles issues in the 'Plan' state."""

    def __init__(
        self,
        config: OrchestratorConfig,
        linear: LinearClient,
        agent: BaseAgent,
    ):
        super().__init__(config, linear)
        self.agent = agent

    def handle(self, issue: LinearIssue) -> StageResult:
        """Generate a plan and post it as a comment, then advance to Implement."""
        logger.info(f"[Plan] {issue.identifier}: Generating plan...")

        self.comment(issue, "📋 Planning agent generating implementation plan...")

        prompt = PLAN_PROMPT.format(
            issue_key=issue.identifier,
            issue_title=issue.title,
            issue_description=issue.description or "(No description provided)",
        )

        # We need a workspace to give the agent codebase access
        from github_client import cleanup_workspace, prepare_workspace

        workspace = prepare_workspace(
            issue=issue,
            repo_url=self.config.repo.url,
            branch_format=self.config.repo.branch_format,
            default_branch=self.config.repo.default_branch,
            workspace_root=self.config.agent.workspace_root,
        )

        try:
            result = self.agent.dispatch(prompt, workspace)

            if result.success and result.stdout.strip():
                plan_text = result.stdout.strip()
                self.comment(
                    issue,
                    f"📋 **Implementation Plan**\n\n{plan_text}",
                )
                self.transition(issue, "Implement")
                return StageResult(
                    success=True,
                    next_state="Implement",
                    message="Plan posted, advancing to Implement",
                )
            elif result.timed_out:
                self.comment(issue, "❌ Planning agent timed out.")
                return StageResult(
                    success=False,
                    error="Planning agent timed out",
                )
            else:
                error_detail = result.stderr[:500] if result.stderr else "No output"
                self.comment(
                    issue,
                    f"❌ Planning agent failed: {error_detail}",
                )
                return StageResult(success=False, error=error_detail)
        finally:
            cleanup_workspace(workspace)
