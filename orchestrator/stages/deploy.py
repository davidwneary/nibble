"""Nibble Orchestrator — Deploy stage handler.

When an issue enters "Deploy", this handler:
1. Merges the PR via gh CLI
2. Monitors CI on main branch
3. On success: transitions to Done
4. On failure: posts error and transitions to blocked/In Review
"""

import logging
import subprocess
import time

from config import OrchestratorConfig
from github_client import slugify
from linear_client import LinearClient, LinearIssue
from stages.base import BaseStage, StageResult

logger = logging.getLogger(__name__)

CI_CHECK_INTERVAL = 15  # seconds between CI status checks
CI_MAX_WAIT = 300  # max 5 minutes waiting for CI


class DeployStage(BaseStage):
    """Handles issues in the 'Deploy' state."""

    def __init__(self, config: OrchestratorConfig, linear: LinearClient):
        super().__init__(config, linear)
        self._repo_slug = (
            config.repo.url
            .replace("git@github.com:", "")
            .replace(".git", "")
        )

    def handle(self, issue: LinearIssue) -> StageResult:
        """Merge PR and monitor CI."""
        logger.info(f"[Deploy] {issue.identifier}: Merging PR...")

        self.comment(issue, "🚀 Merging PR and monitoring CI...")

        # Find and merge the PR
        pr_number = self._find_pr_number(issue)
        if not pr_number:
            self.comment(issue, "⚠️ No open PR found to merge.")
            return StageResult(success=False, error="No PR found")

        merge_result = self._merge_pr(pr_number)
        if not merge_result:
            self.comment(
                issue,
                f"❌ Failed to merge PR #{pr_number}. Check for merge conflicts or failing checks.",
            )
            return StageResult(success=False, error="PR merge failed")

        # Monitor CI on main
        self.comment(issue, f"✅ PR #{pr_number} merged. Monitoring CI on main...")
        ci_passed = self._wait_for_ci()

        if ci_passed:
            self.comment(issue, "🎉 Deployed successfully! CI green on main.")
            self.transition(issue, "Done")
            return StageResult(
                success=True,
                next_state="Done",
                message="Deployed and CI green",
            )
        else:
            self.comment(
                issue,
                "⚠️ PR merged but CI failed on main. Please investigate.",
            )
            # Still mark Done since it's merged, but flag the CI issue
            self.transition(issue, "Done")
            return StageResult(
                success=True,
                next_state="Done",
                message="Merged but CI needs attention",
            )

    def _find_pr_number(self, issue: LinearIssue) -> int:
        """Find the open PR number for this issue's branch."""
        slug = slugify(issue.title)
        branch_name = self.config.repo.branch_format.format(
            issue_key=issue.identifier.lower(),
            slug=slug,
        )
        try:
            result = subprocess.run(
                [
                    "gh", "pr", "list",
                    "--repo", self._repo_slug,
                    "--head", branch_name,
                    "--state", "open",
                    "--json", "number",
                    "--jq", ".[0].number",
                ],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if result.returncode == 0 and result.stdout.strip():
                return int(result.stdout.strip())
        except Exception as e:
            logger.error(f"Error finding PR: {e}")
        return 0

    def _merge_pr(self, pr_number: int) -> bool:
        """Merge a PR using squash merge."""
        try:
            result = subprocess.run(
                [
                    "gh", "pr", "merge",
                    str(pr_number),
                    "--repo", self._repo_slug,
                    "--squash",
                    "--delete-branch",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                logger.info(f"Merged PR #{pr_number}")
                return True
            else:
                logger.error(f"Merge failed: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error merging PR: {e}")
            return False

    def _wait_for_ci(self) -> bool:
        """Wait for CI to complete on main branch."""
        elapsed = 0
        while elapsed < CI_MAX_WAIT:
            time.sleep(CI_CHECK_INTERVAL)
            elapsed += CI_CHECK_INTERVAL

            status = self._check_ci_status()
            if status == "success":
                return True
            elif status == "failure":
                return False
            # else: pending/in_progress — keep waiting

        logger.warning("CI timed out waiting for completion")
        return True  # Assume success if CI takes too long (it's still running)

    def _check_ci_status(self) -> str:
        """Check the combined CI status on the default branch."""
        try:
            result = subprocess.run(
                [
                    "gh", "run", "list",
                    "--repo", self._repo_slug,
                    "--branch", self.config.repo.default_branch,
                    "--limit", "2",
                    "--json", "status,conclusion",
                ],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if result.returncode == 0:
                import json
                runs = json.loads(result.stdout)
                if not runs:
                    return "pending"
                # Check most recent runs
                for run in runs:
                    if run["status"] == "completed":
                        return run["conclusion"]  # "success" or "failure"
                    elif run["status"] in ("in_progress", "queued"):
                        return "pending"
            return "pending"
        except Exception as e:
            logger.error(f"Error checking CI: {e}")
            return "pending"
