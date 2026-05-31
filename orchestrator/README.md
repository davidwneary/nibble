# Nibble Orchestrator

A lightweight Python daemon that polls Linear for "Todo" issues and dispatches them to an AI coding agent (GitHub Copilot CLI or OpenAI Codex) running in a Docker sandbox.

## Architecture

```
Linear (Todo issues) → Orchestrator (Python daemon) → Agent (copilot -p / codex)
                                                     → GitHub (branch + PR)
                                                     → Linear (state update + comment)
```

## Quick Start

```bash
# From the repo root:
docker compose up -d
docker compose logs -f orchestrator
```

## Configuration

The orchestrator reads from two sources:

1. **WORKFLOW.md** (in repo root) — agent type, model, hooks, constraints
2. **`.env`** (in repo root) — secrets and runtime overrides

### Required environment variables (.env)

```env
LINEAR_API_KEY=lin_api_xxxxx
GITHUB_TOKEN=ghp_xxxxx
```

### Optional environment overrides

```env
SYMPHONY_POLL_INTERVAL=30        # Seconds between Linear polls
SYMPHONY_MAX_CONCURRENCY=2       # Max parallel agent sessions
SYMPHONY_WORKSPACE_ROOT=/workspaces
```

## Switching Agents

Edit `WORKFLOW.md`:

```yaml
agent:
  active: copilot    # ← change to "codex" to switch
```

Then restart: `docker compose restart`

## Running Locally (without Docker)

```bash
cd orchestrator
pip install -r requirements.txt
export LINEAR_API_KEY=lin_api_xxxxx
export GITHUB_TOKEN=ghp_xxxxx

# Daemon mode (continuous polling)
python3 orchestrator.py --config ../WORKFLOW.md

# Single poll cycle (for testing)
python3 orchestrator.py --config ../WORKFLOW.md --once

# Process a specific issue
python3 orchestrator.py --config ../WORKFLOW.md --issue DN-15
```

## Agent Sandbox

The Docker container provides:
- ✅ Full dev environment (Node.js 20, JDK 17, Gradle 8.7, Python 3.11)
- ✅ Network access (npm, Maven, Copilot API, GitHub, Linear)
- ✅ Git push via SSH (keys mounted read-only)
- ✅ PR creation via `gh` CLI

The container does NOT have:
- ❌ Host filesystem access (Docker isolation)
- ❌ Docker socket access
- ❌ Ability to push directly to `main` (branch protection)

## File Structure

```
orchestrator/
├── Dockerfile              # Ubuntu + all toolchains
├── requirements.txt        # Python deps (requests, pyyaml)
├── orchestrator.py         # Main daemon loop
├── config.py               # WORKFLOW.md parser
├── linear_client.py        # Linear GraphQL API
├── github_client.py        # Git + gh CLI wrapper
├── prompt_builder.py       # Agent prompt construction
├── agents/
│   ├── __init__.py
│   ├── base.py            # Abstract agent interface
│   ├── copilot_agent.py   # Copilot CLI dispatch
│   └── codex_agent.py     # Codex CLI dispatch (stub)
└── README.md              # This file
```

## Troubleshooting

### Copilot CLI auth in Docker
The `GITHUB_TOKEN` env var should authenticate Copilot CLI automatically.
If not, you may need to run `copilot --login` interactively once to cache credentials.

### Agent timeout
Default is 30 minutes. Increase in WORKFLOW.md:
```yaml
copilot:
  timeout_minutes: 60
```

### No issues being picked up
- Check that issues are in "Todo" state (not "Backlog")
- Check `LINEAR_API_KEY` is valid
- Check orchestrator logs: `docker compose logs orchestrator`
