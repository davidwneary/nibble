"""Nibble Orchestrator — Prompt builder.

Constructs the full prompt sent to the agent, combining:
- Issue details (from Linear)
- Project context instructions (from AGENTS.md hooks)
- Constraints and TDD instructions
"""

from linear_client import LinearIssue


PROMPT_TEMPLATE = """You are implementing a Linear issue for the Nibble project.

## Issue
Key: {issue_key}
Title: {issue_title}
Description:
{issue_description}

## Instructions

{on_start_hook}

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

**If changes touch both:**
Run both sets of checks.

## Constraints
- Do NOT modify: AGENTS.md, WORKFLOW.md, PLAN.md, AGENT-SETUP.md, orchestrator/
- Do NOT add 'any' type annotations in TypeScript
- Do NOT skip or disable tests
- Do NOT commit secrets or API keys
- Do NOT modify CI workflow files unless the issue explicitly requires it
- Keep changes focused on THIS issue only — no drive-by refactors

## Git Convention
Commit with: `feat({area}): {short description}`
Where area is one of: web, android, shared, infra
"""


def build_prompt(issue: LinearIssue, on_start_hook: str = "") -> str:
    """Build the full agent prompt from an issue and config hooks."""
    description = issue.description or "(No description provided)"

    if not on_start_hook:
        on_start_hook = (
            "1. Read AGENTS.md in the repo root for full project context.\n"
            "2. Read the issue description carefully.\n"
            "3. Identify which area of the codebase is affected.\n"
            "4. Read relevant docs from /docs/ (architecture, schema, conventions).\n"
            "5. PLAN your approach before writing any code.\n"
            "6. Follow RED/GREEN TDD: write a failing test first, then implement."
        )

    return PROMPT_TEMPLATE.format(
        issue_key=issue.identifier,
        issue_title=issue.title,
        issue_description=description,
        on_start_hook=on_start_hook,
    )
