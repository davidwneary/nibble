# Nibble

A personal recipe management app for Android and Web, inspired by [Mela](https://mela.recipes/).

## Prerequisites

| Tool | Version | Needed for |
|------|---------|------------|
| Node.js | 20+ | Web app |
| npm | 9+ | Web app |
| JDK | 17+ | Android app |
| Android Studio | Latest | Android app (emulator + SDK) |
| Python | 3.10+ | Orchestrator |
| Docker | 24+ | Orchestrator (containerised) |
| `gh` CLI | 2.x | Orchestrator (PR creation) |
| `copilot` CLI | Latest | Agent (auto-implementation) |

---

## 1. Run the Web App

```bash
cd web
npm install
npm run dev
```

Opens at **http://localhost:5173**.

### Other web commands

```bash
npm run build          # Production build
npm run lint           # ESLint (strict, no-any)
npm run typecheck      # TypeScript type check
npm test               # Run tests once
npm run test:watch     # Tests in watch mode
npm run test:coverage  # Tests with coverage report
```

---

## 2. Run the Android App

### Option A: Android Studio (recommended)

1. Open the `android/` directory in Android Studio
2. Let Gradle sync (first time takes a few minutes)
3. Select a device/emulator and click **Run ▶**

### Option B: Command line

```bash
cd android
./gradlew assembleDebug
```

The APK will be at `android/app/build/outputs/apk/debug/app-debug.apk`.

Install on a connected device:
```bash
adb install app/build/outputs/apk/debug/app-debug.apk
```

### Android tests and lint

```bash
./gradlew test              # Unit tests
./gradlew ktlintCheck       # Kotlin lint
./gradlew assembleDebug     # Build check
```

---

## 3. Run the Orchestrator

The orchestrator polls Linear for "Todo" issues and dispatches them to a Copilot CLI agent which implements the issue, runs tests, and opens a PR.

### Setup

1. Create a `.env` file in the repo root:
   ```env
   LINEAR_API_KEY=lin_api_xxxxx
   GITHUB_TOKEN=ghp_xxxxx
   ```

2. Authenticate `gh` CLI:
   ```bash
   gh auth login
   ```

### Option A: Docker (sandboxed — recommended)

```bash
docker compose up -d          # Start daemon
docker compose logs -f        # Watch logs
docker compose down           # Stop
```

### Option B: Run locally (no Docker)

```bash
cd orchestrator
pip install -r requirements.txt

# Daemon mode (polls continuously)
python3 orchestrator.py --config ../WORKFLOW.md

# Process one specific issue
python3 orchestrator.py --config ../WORKFLOW.md --issue DN-15

# Single poll cycle then exit
python3 orchestrator.py --config ../WORKFLOW.md --once
```

### Switching agent type

Edit `WORKFLOW.md` and change the active agent:

```yaml
agent:
  active: copilot    # or "codex"
```

Then restart the orchestrator.

---

## Project Structure

```
nibble/
├── web/                  ← React + TypeScript + Vite + Tailwind
├── android/              ← Kotlin + Jetpack Compose
├── orchestrator/         ← Python daemon (Linear → Agent → PR)
├── docs/                 ← Architecture, schema, design system specs
├── scripts/              ← CI architecture guard scripts
├── AGENTS.md             ← Context file for AI agents
├── WORKFLOW.md           ← Orchestrator config (agent type, hooks)
├── PLAN.md               ← Roadmap and requirements
├── docker-compose.yml    ← Orchestrator container
└── .github/workflows/    ← CI (web-ci.yml, android-ci.yml)
```

---

## Development Workflow

This project uses **agent-led development**:

1. Write a well-scoped Linear issue with clear acceptance criteria
2. Move it to "Todo"
3. The orchestrator picks it up, dispatches a Copilot agent
4. Agent implements (TDD), runs tests, opens a PR
5. CI validates (lint, tests, architecture guards)
6. You review the PR and merge

For manual development, create a feature branch and follow the same TDD approach:
```bash
git checkout -b feat/my-feature
# Write failing test → implement → verify → push → PR
```
