"""Nibble Orchestrator — Main daemon.

Stage-based workflow dispatcher. Polls Linear for issues and routes
them to the appropriate stage handler based on their current state:

    Todo → Plan → Implement → In Review ↔ Implement → Deploy → Done

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
from typing import Optional

from agents.base import BaseAgent
from agents.codex_agent import CodexAgent
from agents.copilot_agent import CopilotAgent
from config import OrchestratorConfig, load_config
from linear_client import LinearClient, LinearIssue
from stages.base import StageResult
from stages.deploy import DeployStage
from stages.implement import ImplementStage
from stages.plan import PlanStage
from stages.review import ReviewStage
from stages.todo import TodoStage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("orchestrator")

# Track issues currently being processed (to avoid double-dispatch)
_active_issues: set[str] = set()

# Map Linear state names to stage handler names
STAGE_MAP = {
    "Todo": "todo",
    "Plan": "plan",
    "Implement": "implement",
    "In Review": "review",
    "Deploy": "deploy",
}

# States that the orchestrator should pick up
ELIGIBLE_STATES = list(STAGE_MAP.keys())


def create_agent(config: OrchestratorConfig, profile_name: Optional[str] = None) -> BaseAgent:
    """Create an agent based on config. Optionally override the profile."""
    active = profile_name or config.agent.active
    profile = config.agent.profiles.get(active, config.agent.current_profile)

    if active in ("copilot", "copilot_reviewer"):
        return CopilotAgent(
            command=profile.command,
            flags=profile.flags,
            model=profile.model,
            timeout_minutes=profile.timeout_minutes,
        )
    elif active in ("codex", "codex_reviewer"):
        return CodexAgent(
            command=profile.command,
            flags=profile.flags,
            model=profile.model,
            timeout_minutes=profile.timeout_minutes,
        )
    else:
        raise ValueError(f"Unknown agent type: {active}")


class StageDispatcher:
    """Routes issues to the correct stage handler based on their Linear state."""

    def __init__(self, config: OrchestratorConfig, linear: LinearClient):
        self.config = config
        self.linear = linear

        # Create agents
        self.impl_agent = create_agent(config)
        self.review_agent = create_agent(config)  # Same model, different prompt in ReviewStage

        # Create stage handlers
        self.stages = {
            "todo": TodoStage(config, linear),
            "plan": PlanStage(config, linear, self.impl_agent),
            "implement": ImplementStage(config, linear, self.impl_agent),
            "review": ReviewStage(config, linear, self.review_agent),
            "deploy": DeployStage(config, linear),
        }

    def dispatch(self, issue: LinearIssue) -> StageResult:
        """Route an issue to its stage handler."""
        stage_name = STAGE_MAP.get(issue.state_name)
        if not stage_name:
            logger.warning(
                f"Issue {issue.identifier} in state '{issue.state_name}' "
                f"has no mapped stage handler"
            )
            return StageResult(success=False, error=f"No handler for state: {issue.state_name}")

        handler = self.stages[stage_name]
        logger.info(
            f"Dispatching {issue.identifier} to [{stage_name}] stage "
            f"(state: {issue.state_name})"
        )

        try:
            return handler.handle(issue)
        except Exception as e:
            logger.error(f"Stage [{stage_name}] failed for {issue.identifier}: {e}", exc_info=True)
            return StageResult(success=False, error=str(e))


def poll_cycle(
    config: OrchestratorConfig,
    linear: LinearClient,
    dispatcher: StageDispatcher,
) -> int:
    """Run one poll cycle. Returns number of issues processed."""
    issues = linear.poll_issues(ELIGIBLE_STATES)

    # Filter out already-active issues
    available = [i for i in issues if i.identifier not in _active_issues]

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
        try:
            dispatcher.dispatch(issue)
        finally:
            _active_issues.discard(issue.identifier)
        processed += 1

    return processed


def run_daemon(config: OrchestratorConfig) -> None:
    """Run the orchestrator as a continuous daemon."""
    logger.info("=" * 60)
    logger.info("Nibble Orchestrator starting (multi-stage)")
    logger.info(f"  Agent: {config.agent.active}")
    logger.info(f"  Model: {config.agent.current_profile.model}")
    logger.info(f"  Poll interval: {config.tracker.poll_interval_seconds}s")
    logger.info(f"  Max concurrent: {config.agent.max_concurrent}")
    logger.info(f"  Stages: {' → '.join(ELIGIBLE_STATES)}")
    logger.info(f"  Repo: {config.repo.url}")
    logger.info("=" * 60)

    linear = LinearClient(api_key=config.linear_api_key)
    dispatcher = StageDispatcher(config, linear)

    while True:
        try:
            poll_cycle(config, linear, dispatcher)
        except KeyboardInterrupt:
            logger.info("Shutting down (keyboard interrupt)")
            break
        except Exception as e:
            logger.error(f"Error in poll cycle: {e}", exc_info=True)

        time.sleep(config.tracker.poll_interval_seconds)


def run_single_issue(config: OrchestratorConfig, issue_key: str) -> None:
    """Process a single issue by key (for testing)."""
    linear = LinearClient(api_key=config.linear_api_key)
    dispatcher = StageDispatcher(config, linear)

    # Fetch issue in any active state
    issues = linear.poll_issues(ELIGIBLE_STATES)
    target = next((i for i in issues if i.identifier == issue_key), None)

    if not target:
        logger.error(f"Issue {issue_key} not found in eligible states: {ELIGIBLE_STATES}")
        sys.exit(1)

    dispatcher.dispatch(target)


def main() -> None:
    parser = argparse.ArgumentParser(description="Nibble Orchestrator (multi-stage)")
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
        dispatcher = StageDispatcher(config, linear)
        poll_cycle(config, linear, dispatcher)
    else:
        run_daemon(config)


if __name__ == "__main__":
    main()
