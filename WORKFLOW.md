# WORKFLOW.md — Symphony Orchestration Config
# This file defines how Symphony dispatches agents for the Nibble project.

workflow:
  name: nibble
  description: "Recipe management app - Android (Kotlin/Compose) + Web (React/TS) + Supabase"

  tracker:
    type: linear
    project_slug: nibble-recipe-app
    poll_interval_seconds: 30
    eligible_states: ["Todo"]
    in_progress_state: "In Progress"
    handoff_states: ["In Review"]
    terminal_states: ["Done", "Cancelled"]
    comment_on_progress: true
    comment_on_blocker: true

  agent:
    type: codex
    model: codex
    max_concurrent: 2
    timeout_minutes: 30
    workspace_root: /workspaces

  repo:
    url: git@github.com:davidwneary/nibble.git
    default_branch: main
    pr_target: main
    branch_format: "feat/{issue_key}-{slug}"

  pr:
    auto_open: true
    title_format: "{issue_title}"
    body_template: |
      ## Summary
      {agent_summary}

      ## Linear Issue
      Resolves: {issue_key} — {issue_title}

      ## Changes
      {file_list}

      ## Testing
      - [ ] All existing tests pass
      - [ ] New tests written (red/green TDD)
      - [ ] Lints pass
    labels: ["agent-authored"]

  hooks:
    on_start: |
      1. Read AGENTS.md in the repo root for full project context and conventions.
      2. Read the Linear issue title and description carefully.
      3. Identify which area of the codebase is affected.
      4. Read relevant docs from /docs/ (architecture, schema, conventions).
      5. PLAN your approach before writing any code.
      6. Follow RED/GREEN TDD: write a failing test first, then implement to make it pass.

    on_complete: |
      1. Run the full lint suite: `npm run lint` (web) or `./gradlew ktlintCheck` (android).
      2. Run all tests: `npm test` (web) or `./gradlew test` (android).
      3. Verify no type errors: `npm run typecheck` (web).
      4. If any check fails, fix it before opening the PR.
      5. Write a clear PR description summarizing what was done and why.
      6. Open the PR and comment on the Linear issue with a link.

    on_failure: |
      1. Read the error output carefully.
      2. If a test fails, check whether the test is wrong or the implementation.
      3. If CI fails, read the logs and attempt a fix (max 3 retries).
      4. After 3 failed attempts, comment on the Linear issue explaining the blocker.
      5. Transition the issue to "In Review" with a note requesting human help.

  constraints:
    # Files agents must NEVER modify
    protected_files:
      - "AGENTS.md"
      - "WORKFLOW.md"
      - "PLAN.md"
      - "AGENT-SETUP.md"
      - ".env"
      - "symphony/**"

    # Agents must not
    prohibited_actions:
      - "Delete test files"
      - "Disable linting rules"
      - "Skip tests"
      - "Add 'any' type annotations in TypeScript"
      - "Commit secrets or API keys"
      - "Modify CI workflow files without explicit instruction"
