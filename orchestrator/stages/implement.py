"""Nibble Orchestrator — Implement stage handler.

When an issue enters the "Implement" state, this handler:
1. Reads any prior plan from Linear comments
2. Reads any review feedback (if this is a revision cycle)
3. Invokes the implementing agent
4. If UI changes: captures screenshots via Playwright
5. Commits, pushes, opens a PR
6. Transitions to "In Review"
"""

import logging
import re
from pathlib import Path

from agents.base import BaseAgent
from config import OrchestratorConfig
from github_client import (
    cleanup_workspace,
    commit_and_push,
    has_changes,
    open_pr,
    prepare_workspace,
)
from linear_client import LinearClient, LinearIssue
from stages.base import BaseStage, StageResult

logger = logging.getLogger(__name__)

IMPLEMENT_PROMPT = """You are implementing a Linear issue for the Nibble project.

## Issue
Key: {issue_key}
Title: {issue_title}
Description:
{issue_description}

## Plan
{plan_section}

## Review Feedback (Revision #{revision_number})
{review_feedback}

## Instructions

1. Read AGENTS.md in the repo root for full project context and conventions.
2. Read relevant docs from /docs/ (architecture, schema, conventions).
3. Follow RED/GREEN TDD: write a failing test first, then implement to make it pass.
4. Ensure all existing tests continue to pass.

## Verification

Before you finish, run these checks and fix any failures:

**If changes touch `web/`:**
```bash
cd web && npm run lint && npm run typecheck && npm test
```

**If changes touch `android/`:**
```bash
cd android && ./gradlew ktlintCheck test
```

## Constraints
- Do NOT modify: AGENTS.md, WORKFLOW.md, PLAN.md, AGENT-SETUP.md, orchestrator/
- Do NOT add 'any' type annotations in TypeScript
- Do NOT skip or disable tests
- Do NOT commit secrets or API keys
- Do NOT modify CI workflow files unless the issue explicitly requires it
- Keep changes focused on THIS issue only — no drive-by refactors

## Git Convention
Commit with: `feat({{area}}): {{short description}}`
Where area is one of: web, android, shared, infra
"""


class ImplementStage(BaseStage):
    """Handles issues in the 'Implement' state."""

    def __init__(
        self,
        config: OrchestratorConfig,
        linear: LinearClient,
        agent: BaseAgent,
    ):
        super().__init__(config, linear)
        self.agent = agent

    def handle(self, issue: LinearIssue) -> StageResult:
        """Implement the issue: code, test, commit, push, open PR."""
        logger.info(f"[Implement] {issue.identifier}: Starting implementation...")

        # Determine revision number from comments
        revision_number = self._get_revision_number(issue)
        plan_text = self._get_plan_from_comments(issue)
        review_feedback = self._get_review_feedback(issue) if revision_number > 0 else ""

        if revision_number > 0:
            self.comment(
                issue,
                f"🔄 Implementing revision #{revision_number} based on review feedback...",
            )
        else:
            self.comment(issue, "🛠️ Implementing...")

        prompt = IMPLEMENT_PROMPT.format(
            issue_key=issue.identifier,
            issue_title=issue.title,
            issue_description=issue.description or "(No description provided)",
            plan_section=plan_text or "(No plan available — use your best judgment)",
            revision_number=revision_number,
            review_feedback=review_feedback or "(First implementation — no prior feedback)",
        )

        workspace = prepare_workspace(
            issue=issue,
            repo_url=self.config.repo.url,
            branch_format=self.config.repo.branch_format,
            default_branch=self.config.repo.default_branch,
            workspace_root=self.config.agent.workspace_root,
        )

        try:
            result = self.agent.dispatch(prompt, workspace)

            if result.success and has_changes(workspace):
                # Capture screenshots if this is a UI issue
                self._capture_screenshots_if_needed(issue, workspace)

                pushed = commit_and_push(workspace, issue)
                if pushed:
                    pr_result = open_pr(
                        workspace=workspace,
                        issue=issue,
                        title_format=self.config.pr.title_format,
                        body_template=self.config.pr.body_template,
                        pr_target=self.config.pr.pr_target,
                        labels=self.config.pr.labels,
                    )
                    if pr_result.success:
                        self.comment(issue, f"✅ PR opened: {pr_result.url}")
                        self.transition(issue, "In Review")
                        return StageResult(
                            success=True,
                            next_state="In Review",
                            message=f"PR #{pr_result.number} opened",
                        )
                    else:
                        self.comment(
                            issue,
                            f"❌ Failed to open PR: {pr_result.error}",
                        )
                        return StageResult(
                            success=False,
                            error=f"PR creation failed: {pr_result.error}",
                        )
                else:
                    self.comment(issue, "❌ No committable changes produced.")
                    return StageResult(
                        success=False,
                        error="No committable changes",
                    )
            elif result.timed_out:
                self.comment(issue, "❌ Implementation agent timed out.")
                return StageResult(success=False, error="Agent timed out")
            else:
                error_detail = result.stderr[:500] if result.stderr else "No output"
                self.comment(issue, f"❌ Agent failed: {error_detail}")
                return StageResult(success=False, error=error_detail)
        finally:
            cleanup_workspace(workspace)

    def _get_revision_number(self, issue: LinearIssue) -> int:
        """Count how many review cycles have occurred (from comments)."""
        comments = self.linear.get_issue_comments(issue.id)
        revision_count = 0
        for comment in comments:
            if "🔄 Implementing revision" in comment or "Changes requested" in comment:
                revision_count += 1
        return revision_count

    def _get_plan_from_comments(self, issue: LinearIssue) -> str:
        """Extract the plan from issue comments (posted by PlanStage)."""
        comments = self.linear.get_issue_comments(issue.id)
        for comment in comments:
            if "📋 **Implementation Plan**" in comment:
                # Strip the emoji prefix
                return comment.replace("📋 **Implementation Plan**\n\n", "")
        return ""

    def _get_review_feedback(self, issue: LinearIssue) -> str:
        """Extract the most recent review feedback from comments."""
        comments = self.linear.get_issue_comments(issue.id)
        # Find the last review comment
        for comment in reversed(comments):
            if "🔍 **Code Review" in comment:
                return comment
        return ""

    def _capture_screenshots_if_needed(self, issue: LinearIssue, workspace: Path) -> None:
        """Capture and upload screenshots if issue has UI labels."""
        from screenshot import capture_screenshots, should_capture_screenshots

        if not should_capture_screenshots(issue.labels):
            return

        logger.info(f"[Implement] {issue.identifier}: Capturing UI screenshots...")
        screenshots = capture_screenshots(workspace)
        if screenshots:
            # Post screenshot paths as a comment (images will be in the PR)
            paths_str = "\n".join(f"- `{s.name}`" for s in screenshots)
            self.comment(
                issue,
                f"📸 **UI Screenshots captured:**\n{paths_str}\n\n"
                f"(See PR files for full images)",
            )
        else:
            logger.info("No screenshots captured (Playwright not available or no web/ dir)")
