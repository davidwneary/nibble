# Agent-Led Development Setup Plan

## Goal

Before writing any app code, set up the "harness" — the infrastructure that lets AI coding agents autonomously pick up Linear issues, implement them, run tests, and open PRs. Following the principles from OpenAI's **Harness Engineering** and **Symphony** articles:

- **Humans steer, agents execute** — we design constraints and feedback loops, agents write code
- **Issue tracker is the control plane** — Linear drives all work; Symphony dispatches agents
- **Mechanical enforcement** — linters, CI, and structural tests enforce architecture rules
- **Autonomous feedback loops** — agents see CI results and self-correct
- **Living documentation** — AGENTS.md and /docs/ guide agent context

---

## Architecture Overview

```
┌──────────────┐         ┌─────────────────────┐
│   Linear     │ ◄─poll──│  Symphony (Docker)   │
│  (Issues)    │         │  Elixir/BEAM daemon  │
└──────┬───────┘         └──────────┬──────────┘
       │                            │
       │  issue created/updated     │ spawns workspace
       │                            ▼
       │                 ┌─────────────────────┐
       │                 │  Codex Agent         │
       │                 │  (isolated workspace)│
       │                 │  - reads AGENTS.md   │
       │                 │  - implements issue  │
       │                 │  - runs tests/lint   │
       │                 │  - opens PR          │
       │                 └──────────┬──────────┘
       │                            │
       │                            ▼
       │                 ┌─────────────────────┐
       │                 │  GitHub (nibble)     │
       │                 │  - PR created        │
       │                 │  - CI runs           │
       │                 │  - Human reviews     │
       └─────────────────┤  - Merge & deploy    │
                         └─────────────────────┘
```

---

## Steps (Pre-App Development)

### 1. Create GitHub Remote Repository

- Create `nibble` repo on GitHub (private)
- Push existing local repo (with PLAN.md) to remote
- Configure branch protection on `main` (require PR, require CI pass)

### 2. Create Linear Workspace & Project

- Sign up for Linear (free tier supports up to 250 issues)
- Create a workspace (e.g., "Nibble")
- Create a project matching the GitHub repo
- Set up a basic workflow: Backlog → Todo → In Progress → In Review → Done
- Generate a Linear API key
- Create initial epics matching our version roadmap:
  - Epic: "MVP - Recipe CRUD & Sync"
  - Epic: "v2 - Enhanced Import"
  - Epic: "v3 - Cooking & Planning"
  - Epic: "v4 - Discovery & Polish"

### 3. Install Symphony Prerequisites (Docker)

- Install Docker (if not present)
- Pull/build Symphony Docker image (Elixir + PostgreSQL)
- Alternatively: use `docker-compose` with:
  - Symphony Elixir app container
  - PostgreSQL container (for orchestrator state)
- Verify Elixir/Erlang toolchain is available in container

### 4. Configure Symphony

- Clone `openai/symphony` reference implementation
- Create `docker-compose.yml` for local orchestration
- Configure environment variables:
  ```
  LINEAR_API_KEY=lin_api_xxxxx
  OPENAI_API_KEY=sk-xxxxx
  GITHUB_TOKEN=ghp_xxxxx
  SYMPHONY_REPO=github.com/youruser/nibble
  SYMPHONY_POLL_INTERVAL=30
  SYMPHONY_MAX_CONCURRENCY=2
  ```
- Create `WORKFLOW.md` in the nibble repo (defines agent behavior)

### 5. Write AGENTS.md (Agent Wayfinding Guide)

This is the most critical file — it's the "table of contents" that agents read to understand the project. Must include:

- Project overview and architecture
- Tech stack and conventions
- Directory structure guide
- Pointer to `/docs/` for detailed specs
- Coding standards and constraints
- How to run tests, lint, and build
- What NOT to do (explicit boundaries)

### 6. Create /docs/ Directory Structure

```
docs/
├── architecture.md        # System architecture, data flow
├── database-schema.md     # Supabase schema, RLS policies
├── api-conventions.md     # Supabase client usage patterns
├── testing-strategy.md    # What to test, how, coverage targets
├── ui-conventions.md      # Design system, component patterns
├── android/
│   └── setup.md          # Kotlin/Compose project conventions
└── web/
    └── setup.md          # React/TS project conventions
```

### 7. Set Up CI/CD (GitHub Actions)

Create mechanical enforcement via CI:

- **Linting**: ESLint (web), ktlint (Android)
- **Type checking**: TypeScript strict mode
- **Tests**: Jest (web), JUnit (Android)
- **Architecture checks**: Custom scripts that enforce:
  - No direct Supabase calls outside service layer
  - All DB queries go through typed functions
  - No `any` types in TypeScript
  - Component file naming conventions
- **PR checks**: All must pass before merge

### 8. Create WORKFLOW.md (Symphony Config)

Defines how Symphony dispatches work to agents:

```yaml
workflow:
  name: nibble
  tracker:
    type: linear
    project_slug: nibble
    poll_interval_seconds: 30
    eligible_states: ["Todo"]
    terminal_states: ["Done", "Cancelled"]
    handoff_states: ["In Review"]
  agent:
    type: codex
    model: codex
    max_concurrent: 2
    workspace_root: /tmp/symphony-workspaces
    timeout_minutes: 30
  repo:
    url: github.com/youruser/nibble
    default_branch: main
    pr_target: main
  hooks:
    on_start: |
      Read AGENTS.md for project context.
      Read the Linear issue description carefully.
      Plan your approach before writing code.
    on_complete: |
      Run all lints and tests.
      Open a PR with a clear description linking the Linear issue.
    on_failure: |
      Log the error. If CI failed, read the output and attempt a fix.
      After 3 retries, transition issue to "Blocked" with a comment.
```

### 9. Write Initial Custom Linters / Architecture Guards

Create scripts that mechanically enforce project rules:

- `scripts/check-architecture.sh` — verifies layer boundaries
- `scripts/check-no-any.sh` — no `any` types in TS
- `scripts/check-imports.sh` — enforces import structure
- These run in CI and also locally (agents run them before PR)

### 10. Test the Full Loop (Smoke Test)

- Create a trivial Linear issue (e.g., "Add a README.md with project name")
- Start Symphony daemon
- Verify: Symphony detects issue → spawns agent → agent opens PR → CI runs → human reviews
- Fix any configuration issues
- Document the working setup

---

## Post-Setup: Development Workflow

Once the harness is working, the daily workflow becomes:

1. **You** write well-scoped Linear issues with clear acceptance criteria
2. **Symphony** polls Linear, dispatches Codex agents
3. **Agents** implement, test, and open PRs
4. **CI** validates (lint, tests, architecture checks)
5. **You** review PRs, provide feedback or approve
6. **Merge & deploy** (Cloudflare auto-deploys web on merge)

Your role shifts from writing code to:
- Designing good issues (clear scope, acceptance criteria)
- Maintaining AGENTS.md and /docs/ as the project evolves
- Reviewing PRs and providing architectural feedback
- Tuning linters and CI to catch recurring agent mistakes
- "Garbage collecting" stale docs and configs

---

## Cost Considerations

| Service | Cost | Notes |
|---------|------|-------|
| Linear | Free (up to 250 issues) | Plenty for solo dev |
| GitHub | Free (private repos) | Actions: 2000 min/month free |
| Symphony | Free (open source, self-hosted Docker) | Runs locally |
| OpenAI Codex API | Pay-per-use | Main ongoing cost; ~$0.01-0.10 per agent session |
| Supabase | Free tier | Already planned |
| Cloudflare Pages | Free | Already planned |

**Primary ongoing cost**: OpenAI API usage for Codex agent sessions. For a solo project doing 5-20 issues/week, expect roughly $5-30/month depending on task complexity.

---

## Open Questions

- **GitHub Copilot agent integration**: Symphony's SPEC.md is agent-agnostic. We could add a second agent type (Copilot coding agent via `gh copilot`) as a dispatch target later. Start with Codex for simplicity.
- **Issue granularity**: How small should issues be? Recommendation: each issue should be completable by an agent in <30 minutes. Split larger work into sub-issues.
- **Secrets management**: Use GitHub Secrets for CI, `.env` file locally for Symphony (gitignored).
