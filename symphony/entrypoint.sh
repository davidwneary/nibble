#!/bin/bash
set -e

echo "=== Symphony Orchestrator ==="
echo "Repo: ${SYMPHONY_REPO_URL}"
echo "Branch: ${SYMPHONY_REPO_BRANCH}"
echo "Poll interval: ${SYMPHONY_POLL_INTERVAL}s"
echo "Max concurrency: ${SYMPHONY_MAX_CONCURRENCY}"

# Run database migrations
echo "Running migrations..."
MIX_ENV=prod mix ecto.setup 2>/dev/null || MIX_ENV=prod mix ecto.migrate

# Start Symphony daemon
echo "Starting Symphony daemon..."
exec MIX_ENV=prod mix run --no-halt
