"""Nibble Orchestrator — Main daemon.

Continuously polls Linear for issues in "Todo" state,
dispatches them to the configured agent (Copilot CLI or Codex),
and opens PRs with the results.

Usage:
    python3 orchestrator.py                    # Normal daemon mode
    python3 orchestrator.py --once             # Single poll cycle (for testing)
    python3 orchestrator.py --issue DN-15      # Process a specific issue
"""

import argparse
import logging
import sys
import time
from pathlib import Path

from agents.base import BaseAgent
from agents.codex_agent import CodexAgent
from agents.copilot_agent import CopilotAgent
from config import OrchestratorConfig, load_config
from github_client import (
    cleanup_workspace,
    commit_and_push,
    has_changes,
    open_pr,
    prepare_workspace,
)
from linear_client import LinearClient, LinearIssue
from prompt_builder import build_prompt

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("orchestrator")

# Track issues currently being processed (to avoid double-dispatch)
_active_issues: set[str] = set()


def create_agent(config: OrchestratorConfig) -> BaseAgent:
    """Create the appropriate agent based on config."""
    profile = config.agent.current_profile
    if config.agent.active == "copilot":
        return CopilotAgent(
            command=profile.command,
            flags=profile.flags,
            model=profile.model,
            timeout_minutes=profile.timeout_minutes,
        )
    elif config.agent.active == "codex":
        return CodexAgent(
            command=profile.command,
            flags=profile.flags,
            model=profile.model,
            timeout_minutes=profile.timeout_minutes,
        )
    else:
        raise ValueError(f"Unknown agent type: {config.agent.active}")


def process_issue(
    issue: LinearIssue,
    config: OrchestratorConfig,
    linear: LinearClient,
    agent: BaseAgent,
) -> bool:
    """Process a single issue end-to-end. Returns True if PR was opened."""
    logger.info(f"Processing {issue.identifier}: {issue.title}")

    # Transition to In Progress
    linear.transition_issue(issue.id, config.tracker.in_progress_state)
    if config.tracker.comment_on_progress:
        linear.comment_on_issue(
            issue.id,
            f"🤖 Agent ({config.agent.active}) picking up this issue...",
        )

    # Prepare workspace
    workspace = prepare_workspace(
        issue=issue,
        repo_url=config.repo.url,
        branch_format=config.repo.branch_format,
        default_branch=config.repo.default_branch,
        workspace_root=config.agent.workspace_root,
    )

    try:
        # Build prompt and dispatch agent
        prompt = build_prompt(issue, on_start_hook=config.hooks.on_start)
        result = agent.dispatch(prompt, workspace)

        if result.success and has_changes(workspace):
            # Agent produced changes — commit, push, open PR
            pushed = commit_and_push(workspace, issue)
            if pushed:
                pr_result = open_pr(
                    workspace=workspace,
                    issue=issue,
                    title_format=config.pr.title_format,
                    body_template=config.pr.body_template,
                    pr_target=config.pr.pr_target,
                    labels=config.pr.labels,
                )
                if pr_result.success:
                    linear.comment_on_issue(
                        issue.id,
                        f"✅ PR opened: {pr_result.url}",
                    )
                    linear.transition_issue(
                        issue.id,
                        config.tracker.handoff_states[0],
                    )
                    return True
                else:
                    _handle_failure(
                        issue, linear, config,
                        f"Failed to open PR: {pr_result.error}",
                    )
            else:
                _handle_failure(
                    issue, linear, config,
                    "Agent ran but produced no committable changes.",
                )
        elif result.timed_out:
            _handle_failure(
                issue, linear, config,
                f"Agent timed out after {agent.timeout_seconds}s.",
            )
        else:
            error_detail = result.stderr[:500] if result.stderr else "No output"
            _handle_failure(
                issue, linear, config,
                f"Agent failed (exit code {result.exit_code}): {error_detail}",
            )
        return False

    finally:
        cleanup_workspace(workspace)
        _active_issues.discard(issue.identifier)


def _handle_failure(
    issue: LinearIssue,
    linear: LinearClient,
    config: OrchestratorConfig,
    message: str,
) -> None:
    """Handle agent failure — comment and transition."""
    logger.error(f"{issue.identifier}: {message}")
    if config.tracker.comment_on_blocker:
        linear.comment_on_issue(issue.id, f"❌ {message}")
    linear.transition_issue(issue.id, config.tracker.handoff_states[0])


def poll_cycle(
    config: OrchestratorConfig,
    linear: LinearClient,
    agent: BaseAgent,
) -> int:
    """Run one poll cycle. Returns number of issues processed."""
    issues = linear.poll_issues(config.tracker.eligible_states)

    # Filter out already-active issues
    available = [
        i for i in issues
        if i.identifier not in _active_issues
    ]

    # Respect concurrency limit
    slots = config.agent.max_concurrent - len(_active_issues)
    to_process = available[:slots]

    if to_process:
        logger.info(
            f"Found {len(available)} eligible issues, "
            f"processing {len(to_process)} (slots={slots})"
        )

    processed = 0
    for issue in to_process:
        _active_issues.add(issue.identifier)
        process_issue(issue, config, linear, agent)
        processed += 1

    return processed


def run_daemon(config: OrchestratorConfig) -> None:
    """Run the orchestrator as a continuous daemon."""
    logger.info("=" * 60)
    logger.info("Nibble Orchestrator starting")
    logger.info(f"  Agent: {config.agent.active}")
    logger.info(f"  Model: {config.agent.current_profile.model}")
    logger.info(f"  Poll interval: {config.tracker.poll_interval_seconds}s")
    logger.info(f"  Max concurrent: {config.agent.max_concurrent}")
    logger.info(f"  Repo: {config.repo.url}")
    logger.info("=" * 60)

    linear = LinearClient(api_key=config.linear_api_key)
    agent = create_agent(config)

    while True:
        try:
            poll_cycle(config, linear, agent)
        except KeyboardInterrupt:
            logger.info("Shutting down (keyboard interrupt)")
            break
        except Exception as e:
            logger.error(f"Error in poll cycle: {e}", exc_info=True)

        time.sleep(config.tracker.poll_interval_seconds)


def run_single_issue(config: OrchestratorConfig, issue_key: str) -> None:
    """Process a single issue by key (for testing)."""
    linear = LinearClient(api_key=config.linear_api_key)
    agent = create_agent(config)

    # Fetch all eligible issues and find the one we want
    all_states = (
        config.tracker.eligible_states
        + [config.tracker.in_progress_state]
    )
    issues = linear.poll_issues(all_states)
    target = next((i for i in issues if i.identifier == issue_key), None)

    if not target:
        logger.error(f"Issue {issue_key} not found in states: {all_states}")
        sys.exit(1)

    process_issue(target, config, linear, agent)


def main() -> None:
    parser = argparse.ArgumentParser(description="Nibble Orchestrator")
    parser.add_argument(
        "--once", action="store_true",
        help="Run a single poll cycle and exit",
    )
    parser.add_argument(
        "--issue", type=str,
        help="Process a specific issue by key (e.g. DN-15)",
    )
    parser.add_argument(
        "--config", type=str, default=None,
        help="Path to WORKFLOW.md (default: auto-detect from repo)",
    )
    args = parser.parse_args()

    config_path = Path(args.config) if args.config else None
    config = load_config(config_path)

    if not config.linear_api_key:
        logger.error("LINEAR_API_KEY not set. Add it to .env or environment.")
        sys.exit(1)

    if args.issue:
        run_single_issue(config, args.issue)
    elif args.once:
        linear = LinearClient(api_key=config.linear_api_key)
        agent = create_agent(config)
        poll_cycle(config, linear, agent)
    else:
        run_daemon(config)


if __name__ == "__main__":
    main()
