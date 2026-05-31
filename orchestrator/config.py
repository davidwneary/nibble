"""Nibble Orchestrator — Configuration reader.

Reads WORKFLOW.md (YAML front-matter style) and environment variables
to produce a typed config object.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class TrackerConfig:
    type: str = "linear"
    project_slug: str = ""
    poll_interval_seconds: int = 30
    eligible_states: list[str] = field(default_factory=lambda: ["Todo"])
    in_progress_state: str = "In Progress"
    handoff_states: list[str] = field(default_factory=lambda: ["In Review"])
    terminal_states: list[str] = field(default_factory=lambda: ["Done", "Cancelled"])
    comment_on_progress: bool = True
    comment_on_blocker: bool = True


@dataclass
class AgentProfile:
    command: str = ""
    flags: str = ""
    model: str = ""
    timeout_minutes: int = 30


@dataclass
class AgentConfig:
    active: str = "copilot"
    max_concurrent: int = 2
    workspace_root: str = "/workspaces"
    profiles: dict[str, AgentProfile] = field(default_factory=dict)

    @property
    def current_profile(self) -> AgentProfile:
        return self.profiles.get(self.active, AgentProfile())


@dataclass
class RepoConfig:
    url: str = ""
    default_branch: str = "main"
    pr_target: str = "main"
    branch_format: str = "feat/{issue_key}-{slug}"


@dataclass
class PrConfig:
    auto_open: bool = True
    title_format: str = "{issue_title}"
    body_template: str = ""
    labels: list[str] = field(default_factory=lambda: ["agent-authored"])


@dataclass
class HooksConfig:
    on_start: str = ""
    on_complete: str = ""
    on_failure: str = ""


@dataclass
class OrchestratorConfig:
    tracker: TrackerConfig = field(default_factory=TrackerConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)
    repo: RepoConfig = field(default_factory=RepoConfig)
    pr: PrConfig = field(default_factory=PrConfig)
    hooks: HooksConfig = field(default_factory=HooksConfig)

    # Environment-sourced
    linear_api_key: str = ""
    github_token: str = ""


def load_config(workflow_path: Optional[Path] = None) -> OrchestratorConfig:
    """Load config from WORKFLOW.md and environment variables."""
    if workflow_path is None:
        # Check common locations in order
        candidates = [
            Path("/app/WORKFLOW.md"),           # Docker mount
            Path("/workspaces/nibble/WORKFLOW.md"),  # Cloned workspace
            Path("../WORKFLOW.md"),             # Local development
        ]
        workflow_path = next((p for p in candidates if p.exists()), candidates[0])

    config = OrchestratorConfig()

    # Read WORKFLOW.md
    if workflow_path.exists():
        raw = workflow_path.read_text()
        # Strip markdown comment lines (lines starting with #)
        yaml_lines = [
            line for line in raw.splitlines()
            if not line.strip().startswith("#")
        ]
        data = yaml.safe_load("\n".join(yaml_lines))
        if data and "workflow" in data:
            _apply_workflow(config, data["workflow"])

    # Environment overrides
    config.linear_api_key = os.environ.get("LINEAR_API_KEY", "")
    config.github_token = os.environ.get("GITHUB_TOKEN", "")

    poll_override = os.environ.get("SYMPHONY_POLL_INTERVAL")
    if poll_override:
        config.tracker.poll_interval_seconds = int(poll_override)

    concurrency_override = os.environ.get("SYMPHONY_MAX_CONCURRENCY")
    if concurrency_override:
        config.agent.max_concurrent = int(concurrency_override)

    workspace_override = os.environ.get("SYMPHONY_WORKSPACE_ROOT")
    if workspace_override:
        config.agent.workspace_root = workspace_override

    repo_url_override = os.environ.get("REPO_URL")
    if repo_url_override:
        config.repo.url = repo_url_override

    return config


def _apply_workflow(config: OrchestratorConfig, wf: dict) -> None:
    """Apply parsed YAML workflow data to config object."""
    # Tracker
    if "tracker" in wf:
        t = wf["tracker"]
        config.tracker = TrackerConfig(
            type=t.get("type", "linear"),
            project_slug=t.get("project_slug", ""),
            poll_interval_seconds=t.get("poll_interval_seconds", 30),
            eligible_states=t.get("eligible_states", ["Todo"]),
            in_progress_state=t.get("in_progress_state", "In Progress"),
            handoff_states=t.get("handoff_states", ["In Review"]),
            terminal_states=t.get("terminal_states", ["Done", "Cancelled"]),
            comment_on_progress=t.get("comment_on_progress", True),
            comment_on_blocker=t.get("comment_on_blocker", True),
        )

    # Agent
    if "agent" in wf:
        a = wf["agent"]
        profiles: dict[str, AgentProfile] = {}
        for key in ("copilot", "codex"):
            if key in a:
                p = a[key]
                profiles[key] = AgentProfile(
                    command=p.get("command", key),
                    flags=p.get("flags", ""),
                    model=p.get("model", ""),
                    timeout_minutes=p.get("timeout_minutes", 30),
                )
        config.agent = AgentConfig(
            active=a.get("active", "copilot"),
            max_concurrent=a.get("max_concurrent", 2),
            workspace_root=a.get("workspace_root", "/workspaces"),
            profiles=profiles,
        )

    # Repo
    if "repo" in wf:
        r = wf["repo"]
        config.repo = RepoConfig(
            url=r.get("url", ""),
            default_branch=r.get("default_branch", "main"),
            pr_target=r.get("pr_target", "main"),
            branch_format=r.get("branch_format", "feat/{issue_key}-{slug}"),
        )

    # PR
    if "pr" in wf:
        p = wf["pr"]
        config.pr = PrConfig(
            auto_open=p.get("auto_open", True),
            title_format=p.get("title_format", "{issue_title}"),
            body_template=p.get("body_template", ""),
            labels=p.get("labels", ["agent-authored"]),
        )

    # Hooks
    if "hooks" in wf:
        h = wf["hooks"]
        config.hooks = HooksConfig(
            on_start=h.get("on_start", ""),
            on_complete=h.get("on_complete", ""),
            on_failure=h.get("on_failure", ""),
        )
