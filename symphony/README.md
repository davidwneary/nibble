# Symphony Orchestrator (Local Docker Setup)

This directory contains the Docker configuration for running the Symphony orchestrator locally.

## Prerequisites

- Docker & Docker Compose installed
- `.env` file in the repo root with required API keys

## Quick Start

```bash
cd symphony
docker compose up -d
```

## Checking Status

```bash
docker compose logs -f symphony
```

## Stopping

```bash
docker compose down
```

## Environment Variables (set in ../.env)

| Variable | Description |
|----------|-------------|
| `LINEAR_API_KEY` | Linear API key for polling issues |
| `OPENAI_API_KEY` | OpenAI API key for Codex agent sessions |
| `GITHUB_TOKEN` | GitHub PAT for opening PRs |

## Architecture

- **db**: PostgreSQL 16 for Symphony orchestrator state
- **symphony**: Elixir daemon that polls Linear and dispatches Codex agents

## Notes

- The daemon polls Linear every 30 seconds by default
- Max 2 concurrent agent sessions (configurable)
- Workspaces are isolated per-issue in the `workspaces` Docker volume
- SSH keys are mounted read-only for git operations
