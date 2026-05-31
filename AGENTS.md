# AGENTS.md — Project Context & Conventions

> **This file is the entry point for all AI coding agents working on this repository.**
> Read this FIRST before doing any work. It tells you what this project is, how it's structured, and what rules to follow.

---

## Project Overview

**Nibble** is a personal recipe management app for Android and Web, inspired by [Mela](https://mela.recipes/). It allows collecting recipes from URLs, organizing them with tags, and syncing across devices.

- **Android**: Kotlin + Jetpack Compose (custom design, NOT Material Design)
- **Web**: React + TypeScript + Tailwind CSS
- **Backend**: Supabase (PostgreSQL, Auth, Storage, Edge Functions, Realtime)
- **Hosting**: Cloudflare Pages (web), sideloaded APK (Android)

---

## Directory Structure

```
nibble/
├── AGENTS.md              ← You are here. Read this first.
├── WORKFLOW.md            ← Symphony orchestration config (DO NOT MODIFY)
├── PLAN.md                ← High-level roadmap and requirements
├── AGENT-SETUP.md         ← Harness setup documentation
├── docs/                  ← Detailed specifications
│   ├── architecture.md
│   ├── database-schema.md
│   ├── api-conventions.md
│   ├── testing-strategy.md
│   ├── design-system.md
│   ├── android/
│   │   └── setup.md
│   └── web/
│       └── setup.md
├── web/                   ← React + TypeScript web app
│   ├── src/
│   │   ├── features/     ← Feature-based modules
│   │   │   ├── recipes/
│   │   │   ├── tags/
│   │   │   └── auth/
│   │   ├── shared/       ← Shared utilities, hooks, components
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   ├── services/ ← Supabase service layer
│   │   │   └── types/
│   │   └── app/          ← App shell, routing, providers
│   ├── tests/
│   └── package.json
├── android/               ← Kotlin + Compose app
│   ├── app/src/main/
│   │   └── kotlin/com/nibble/
│   │       ├── features/
│   │       │   ├── recipes/
│   │       │   ├── tags/
│   │       │   └── auth/
│   │       ├── shared/
│   │       │   ├── data/       ← Repository layer
│   │       │   ├── domain/     ← Use cases
│   │       │   └── ui/         ← Shared composables
│   │       └── app/            ← App entry, navigation, DI
│   └── build.gradle.kts
├── supabase/              ← Supabase config and edge functions
│   ├── migrations/
│   └── functions/
└── symphony/              ← Docker orchestration (DO NOT MODIFY)
```

---

## Architecture Rules (STRICTLY ENFORCED)

These rules are checked by CI. Violating them will fail the build.

### Layer Boundaries

```
UI (Components/Composables)
        │ calls
        ▼
   Hooks / ViewModels
        │ calls
        ▼
   Services / Repositories
        │ calls
        ▼
   Supabase SDK
```

1. **UI components NEVER call Supabase directly.** All data access goes through the service/repository layer.
2. **Services are the only layer that imports Supabase client.** This keeps the rest of the app testable and backend-agnostic.
3. **Features are self-contained.** A feature folder contains its own components, hooks/viewmodels, and tests. Shared code goes in `shared/`.

### Web (React/TypeScript)

- **State management**: TanStack Query for server state (recipes, tags). Zustand for UI state (search filters, modals).
- **Styling**: Tailwind CSS. No CSS-in-JS, no CSS modules.
- **Components**: Functional components only. No class components.
- **Types**: Strict TypeScript. NEVER use `any`. Use `unknown` + type guards if needed.
- **Exports**: Named exports only. No default exports (except pages if Next.js is used).

### Android (Kotlin/Compose)

- **Architecture**: MVVM with repositories. ViewModels expose StateFlow, UI observes with collectAsState.
- **DI**: Koin (lightweight, sufficient for single-user app).
- **Design**: Custom theme inspired by Mela/iOS — NOT Material Design 3.
- **Async**: Kotlin Coroutines + Flow. No RxJava.
- **Navigation**: Compose Navigation with type-safe routes.

---

## Design System (Mela-Inspired)

The app should look and feel like a premium iOS app. Key principles:

- **Clean, spacious, minimal** — generous whitespace, no clutter
- **Typography-driven** — hierarchy through font weight and size, not color
- **Soft cards** — 16px radius, subtle shadows
- **Muted palette** — off-white backgrounds, dark text, single accent color

### Color Tokens

| Token | Light | Dark |
|-------|-------|------|
| `background` | `#FAFAFA` | `#1C1C1E` |
| `surface` | `#FFFFFF` | `#2C2C2E` |
| `primary` | `#FF6B35` (warm orange) | `#FF8F5E` |
| `textPrimary` | `#1A1A1A` | `#F5F5F5` |
| `textSecondary` | `#6D6D72` | `#8E8E93` |
| `divider` | `#EAEAEB` | `#38383A` |
| `success` | `#34C759` | `#30D158` |
| `error` | `#FF3B30` | `#FF453A` |

### Typography Scale

| Use | Web (Tailwind) | Android (sp) |
|-----|----------------|--------------|
| Display/Title | `text-2xl font-semibold` | 28sp SemiBold |
| Section Heading | `text-lg font-semibold` | 20sp SemiBold |
| Body | `text-base` | 16sp Regular |
| Caption/Meta | `text-sm text-secondary` | 13sp Regular |

### Spacing

8px grid: `8, 16, 24, 32, 48, 64`

### Radius

- Cards: 16px
- Buttons: 12px
- Inputs: 8px
- Chips/Tags: 99px (pill)

---

## Testing Strategy (RED/GREEN TDD)

**Every code change follows Red/Green TDD:**

1. **RED**: Write a failing test that describes the desired behavior
2. **GREEN**: Write the minimum code to make the test pass
3. **REFACTOR**: Clean up while keeping tests green

### What to Test

| Layer | What | How |
|-------|------|-----|
| Services/Repos | Data fetching, transformations, error handling | Unit tests with mocked Supabase client |
| Hooks/ViewModels | State logic, side effects | Unit tests (React Testing Library / JUnit) |
| Components/Composables | Rendering, user interactions | Integration tests |
| URL Parser (Edge Fn) | Recipe extraction from various sites | Unit tests with fixture HTML |
| E2E (later) | Critical user flows | Playwright (web) |

### Coverage Targets

- Service layer: 90%+
- Hooks/ViewModels: 80%+
- Components: 70%+ (test behavior, not implementation)
- Overall: 80%+

### Test File Location

- Web: Co-located. `recipes/RecipeCard.tsx` → `recipes/RecipeCard.test.tsx`
- Android: Mirror structure. `features/recipes/RecipeListViewModel.kt` → `test/.../RecipeListViewModelTest.kt`

---

## Git Conventions

### Commit Messages (Conventional Commits)

```
<type>(<scope>): <description>

[optional body]

[optional footer]
Resolves: DN-<number>

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
```

**Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `infra`, `chore`
**Scopes**: `web`, `android`, `supabase`, `ci`, `docs`

### Branch Naming

```
feat/DN-123-short-description
fix/DN-456-bug-name
```

Always include the Linear issue key.

---

## Commands Reference

### Web

```bash
cd web
npm install          # Install dependencies
npm run dev          # Start dev server
npm run build        # Production build
npm run lint         # ESLint
npm run typecheck    # TypeScript strict check
npm test             # Jest + React Testing Library
npm run test:watch   # Watch mode
```

### Android

```bash
cd android
./gradlew build              # Full build
./gradlew test               # Run unit tests
./gradlew ktlintCheck        # Lint check
./gradlew ktlintFormat       # Auto-format
./gradlew assembleDebug      # Build debug APK
```

### Supabase

```bash
cd supabase
supabase start              # Local dev instance
supabase db push            # Apply migrations
supabase functions serve    # Test edge functions locally
```

---

## What NOT To Do

- ❌ Never use `any` in TypeScript
- ❌ Never call Supabase directly from UI components
- ❌ Never skip writing tests
- ❌ Never disable lint rules (fix the code instead)
- ❌ Never commit secrets, API keys, or `.env` files
- ❌ Never modify AGENTS.md, WORKFLOW.md, or symphony/ directory
- ❌ Never use Material Design components on Android (custom Mela-inspired design)
- ❌ Never add dependencies without justification in the PR description
- ❌ Never write implementation before a failing test (TDD is mandatory)

---

## For More Detail

- `docs/architecture.md` — System architecture, data flow diagrams
- `docs/database-schema.md` — Full Supabase schema with RLS policies
- `docs/api-conventions.md` — How to use the Supabase service layer
- `docs/testing-strategy.md` — Detailed testing patterns and examples
- `docs/design-system.md` — Full design tokens, component specs
- `docs/android/setup.md` — Android project setup and conventions
- `docs/web/setup.md` — Web project setup and conventions
