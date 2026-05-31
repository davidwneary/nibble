"""Nibble Orchestrator — GitHub client.

Handles workspace preparation (clone, branch), committing agent changes,
pushing, and opening PRs via the `gh` CLI.
"""

import logging
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from linear_client import LinearIssue

logger = logging.getLogger(__name__)


@dataclass
class PrResult:
    url: str
    number: int
    success: bool
    error: str = ""


def slugify(text: str) -> str:
    """Convert text to a URL-safe slug for branch names."""
    slug = text.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug[:50]


def prepare_workspace(
    issue: LinearIssue,
    repo_url: str,
    branch_format: str,
    default_branch: str,
    workspace_root: str,
) -> Path:
    """Clone the repo and create a feature branch for the issue."""
    slug = slugify(issue.title)
    branch_name = branch_format.format(
        issue_key=issue.identifier.lower(),
        slug=slug,
    )
    workspace = Path(workspace_root) / issue.identifier.lower()

    # Clean up any existing workspace
    if workspace.exists():
        subprocess.run(["rm", "-rf", str(workspace)], check=True)

    # Clone
    logger.info(f"Cloning {repo_url} → {workspace}")
    subprocess.run(
        ["git", "clone", "--depth=1", "--branch", default_branch, repo_url, str(workspace)],
        check=True,
        capture_output=True,
    )

    # Create feature branch
    subprocess.run(
        ["git", "checkout", "-b", branch_name],
        cwd=workspace,
        check=True,
        capture_output=True,
    )

    logger.info(f"Workspace ready: {workspace} (branch: {branch_name})")
    return workspace


def get_branch_name(workspace: Path) -> str:
    """Get the current branch name in a workspace."""
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=workspace,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def has_changes(workspace: Path) -> bool:
    """Check if the workspace has uncommitted changes."""
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=workspace,
        capture_output=True,
        text=True,
    )
    return bool(result.stdout.strip())


def commit_and_push(
    workspace: Path,
    issue: LinearIssue,
    commit_message: str = "",
) -> bool:
    """Stage all changes, commit, and push the branch."""
    if not has_changes(workspace):
        logger.warning(f"No changes in workspace for {issue.identifier}")
        return False

    # Stage all changes
    subprocess.run(["git", "add", "-A"], cwd=workspace, check=True)

    # Commit
    if not commit_message:
        commit_message = f"feat: {issue.title}\n\nImplements: {issue.identifier}"
    subprocess.run(
        ["git", "commit", "-m", commit_message],
        cwd=workspace,
        check=True,
        capture_output=True,
    )

    # Push
    branch = get_branch_name(workspace)
    subprocess.run(
        ["git", "push", "origin", branch],
        cwd=workspace,
        check=True,
        capture_output=True,
    )

    logger.info(f"Pushed branch {branch} for {issue.identifier}")
    return True


def open_pr(
    workspace: Path,
    issue: LinearIssue,
    title_format: str,
    body_template: str,
    pr_target: str,
    labels: list[str],
) -> PrResult:
    """Open a pull request using the gh CLI."""
    title = title_format.format(issue_title=issue.title)

    body = body_template.format(
        agent_summary=f"Automated implementation of {issue.identifier}",
        issue_key=issue.identifier,
        issue_title=issue.title,
        file_list="(see Files Changed tab)",
    ) if body_template else f"Resolves: {issue.identifier} — {issue.title}"

    cmd = [
        "gh", "pr", "create",
        "--title", title,
        "--body", body,
        "--base", pr_target,
    ]
    for label in labels:
        cmd.extend(["--label", label])

    result = subprocess.run(
        cmd,
        cwd=workspace,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        logger.error(f"Failed to open PR: {result.stderr}")
        return PrResult(url="", number=0, success=False, error=result.stderr)

    pr_url = result.stdout.strip()
    # Extract PR number from URL
    pr_number = 0
    match = re.search(r"/pull/(\d+)", pr_url)
    if match:
        pr_number = int(match.group(1))

    logger.info(f"Opened PR: {pr_url}")
    return PrResult(url=pr_url, number=pr_number, success=True)


def cleanup_workspace(workspace: Path) -> None:
    """Remove a workspace directory after PR is opened."""
    if workspace.exists():
        subprocess.run(["rm", "-rf", str(workspace)], check=True)
        logger.info(f"Cleaned up workspace: {workspace}")
