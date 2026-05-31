"""Nibble Orchestrator — Review stage handler.

When an issue enters "In Review", this handler:
1. Fetches the PR diff
2. Reads the original plan and issue context
3. Invokes a reviewer agent (different prompt, same model)
4. Parses the review: APPROVED or CHANGES_REQUESTED
5. If approved: transitions to Deploy
6. If changes requested: posts feedback, transitions back to Implement
7. After 3 failed cycles: escalates to human
"""

import logging
import re

from agents.base import BaseAgent
from config import OrchestratorConfig
from linear_client import LinearClient, LinearIssue
from stages.base import BaseStage, StageResult

logger = logging.getLogger(__name__)

MAX_REVIEW_CYCLES = 3

REVIEW_PROMPT = """You are a senior code reviewer for the Nibble project.

## Your Task

Review the pull request for the following Linear issue. Be thorough but pragmatic.
Focus on correctness, security, maintainability, and adherence to project conventions.

## Issue Context
Key: {issue_key}
Title: {issue_title}
Description:
{issue_description}

## Implementation Plan (from planning stage)
{plan_section}

## Pull Request Diff
{pr_diff}

## Review Criteria

1. **Correctness**: Does the code do what the issue requires?
2. **Tests**: Are there adequate tests? Do they follow red/green TDD?
3. **Security**: No secrets, no SQL injection, no XSS, proper auth checks
4. **Conventions**: Follows project conventions from AGENTS.md (no `any`, proper naming, etc.)
5. **Completeness**: Does it fully address the acceptance criteria from the plan?
6. **No Scope Creep**: Only changes related to this issue

## Output Format

You MUST end your review with EXACTLY one of these verdicts on its own line:

VERDICT: APPROVED
or
VERDICT: CHANGES_REQUESTED

If CHANGES_REQUESTED, list specific, actionable feedback above the verdict:

**Required Changes:**
1. (specific change needed with file path and line reference)
2. ...

VERDICT: CHANGES_REQUESTED

If APPROVED, you may include optional praise or minor suggestions (that don't block merge):

**Looks good!** (optional summary of what was done well)

VERDICT: APPROVED
"""


class ReviewStage(BaseStage):
    """Handles issues in the 'In Review' state."""

    def __init__(
        self,
        config: OrchestratorConfig,
        linear: LinearClient,
        agent: BaseAgent,
    ):
        super().__init__(config, linear)
        self.agent = agent

    def handle(self, issue: LinearIssue) -> StageResult:
        """Review the PR and approve or request changes."""
        logger.info(f"[Review] {issue.identifier}: Starting code review...")

        # Check review cycle count
        cycle_count = self._get_review_cycle_count(issue)
        if cycle_count >= MAX_REVIEW_CYCLES:
            return self._escalate_to_human(issue, cycle_count)

        # Get PR diff
        pr_diff = self._get_pr_diff(issue)
        if not pr_diff:
            self.comment(issue, "⚠️ No open PR found for review. Skipping.")
            return StageResult(success=False, error="No PR found")

        # Get plan from comments
        plan_text = self._get_plan_from_comments(issue)

        self.comment(
            issue,
            f"🔍 Review agent examining PR (cycle {cycle_count + 1}/{MAX_REVIEW_CYCLES})...",
        )

        prompt = REVIEW_PROMPT.format(
            issue_key=issue.identifier,
            issue_title=issue.title,
            issue_description=issue.description or "(No description)",
            plan_section=plan_text or "(No plan available)",
            pr_diff=pr_diff[:15000],  # Truncate large diffs
        )

        # Review agent runs in a workspace clone (read-only, just for context)
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

            if not result.success:
                error_detail = result.stderr[:500] if result.stderr else "No output"
                self.comment(issue, f"❌ Review agent failed: {error_detail}")
                return StageResult(success=False, error=error_detail)

            review_output = result.stdout.strip()
            verdict = self._parse_verdict(review_output)

            if verdict == "APPROVED":
                self.comment(
                    issue,
                    f"🔍 **Code Review — APPROVED** ✅\n\n{review_output}",
                )
                self.transition(issue, "Deploy")
                return StageResult(
                    success=True,
                    next_state="Deploy",
                    message="Review approved, advancing to Deploy",
                )
            else:
                self.comment(
                    issue,
                    f"🔍 **Code Review — Changes Requested** (cycle {cycle_count + 1}/{MAX_REVIEW_CYCLES})\n\n{review_output}",
                )
                self.transition(issue, "Implement")
                return StageResult(
                    success=True,
                    next_state="Implement",
                    message=f"Changes requested (cycle {cycle_count + 1})",
                )
        finally:
            cleanup_workspace(workspace)

    def _parse_verdict(self, output: str) -> str:
        """Parse VERDICT: APPROVED or VERDICT: CHANGES_REQUESTED from output."""
        # Look for the verdict line
        match = re.search(r"VERDICT:\s*(APPROVED|CHANGES_REQUESTED)", output)
        if match:
            return match.group(1)
        # Default to changes requested if can't parse
        logger.warning("Could not parse verdict from review output, defaulting to CHANGES_REQUESTED")
        return "CHANGES_REQUESTED"

    def _get_review_cycle_count(self, issue: LinearIssue) -> int:
        """Count how many review cycles have completed."""
        comments = self.linear.get_issue_comments(issue.id)
        count = 0
        for comment in comments:
            if "🔍 **Code Review" in comment:
                count += 1
        return count

    def _get_pr_diff(self, issue: LinearIssue) -> str:
        """Fetch the PR diff for this issue's branch."""
        import subprocess

        from github_client import slugify

        slug = slugify(issue.title)
        branch_name = self.config.repo.branch_format.format(
            issue_key=issue.identifier.lower(),
            slug=slug,
        )

        # Use gh CLI to get the diff
        try:
            result = subprocess.run(
                [
                    "gh", "pr", "diff",
                    "--repo", self.config.repo.url.replace("git@github.com:", "").replace(".git", ""),
                    branch_name,
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                return result.stdout
            else:
                logger.warning(f"Could not fetch PR diff: {result.stderr}")
                return ""
        except Exception as e:
            logger.error(f"Error fetching PR diff: {e}")
            return ""

    def _get_plan_from_comments(self, issue: LinearIssue) -> str:
        """Extract the plan from issue comments."""
        comments = self.linear.get_issue_comments(issue.id)
        for comment in comments:
            if "📋 **Implementation Plan**" in comment:
                return comment.replace("📋 **Implementation Plan**\n\n", "")
        return ""

    def _escalate_to_human(self, issue: LinearIssue, cycle_count: int) -> StageResult:
        """Escalate to human after max review cycles."""
        logger.warning(
            f"[Review] {issue.identifier}: Escalating after {cycle_count} review cycles"
        )
        self.comment(
            issue,
            f"🚨 **Escalation Required**\n\n"
            f"This issue has been through {cycle_count} review cycles without approval. "
            f"Human intervention needed.\n\n"
            f"Please review the PR and either:\n"
            f"- Merge it manually if acceptable\n"
            f"- Add comments and move back to Implement for another attempt\n"
            f"- Close/cancel if the approach is wrong",
        )
        # Don't transition — leave in Review for human attention
        return StageResult(
            success=False,
            error=f"Escalated after {cycle_count} review cycles",
        )
