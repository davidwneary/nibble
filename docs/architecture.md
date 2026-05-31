# Architecture

## System Overview

Nibble is a recipe management app with three components that communicate through Supabase:

```
┌─────────────────┐     ┌─────────────────┐
│  Android App    │     │   Web App        │
│  Kotlin/Compose │     │  React/TS        │
│                 │     │  (Cloudflare)    │
└────────┬────────┘     └────────┬─────────┘
         │                       │
         │  Supabase SDK         │  Supabase SDK
         │  (REST + Realtime)    │  (REST + Realtime)
         │                       │
         └───────────┬───────────┘
                     │
         ┌───────────▼───────────┐
         │      Supabase         │
         │                       │
         │  ┌─────────────────┐  │
         │  │ PostgREST (API) │  │
         │  │ Realtime (WS)   │  │
         │  │ Auth (JWT)      │  │
         │  │ Storage (S3)    │  │
         │  │ Edge Functions  │  │
         │  │ PostgreSQL (DB) │  │
         │  └─────────────────┘  │
         └───────────────────────┘
```

## Data Flow

### Recipe Creation (Manual)
1. User fills form → UI component
2. UI calls hook/ViewModel → validates data
3. Hook calls `recipeService.create(recipe)` → service layer
4. Service calls `supabase.from('recipes').insert(...)` → Supabase SDK
5. Supabase Realtime pushes change → other connected clients update

### Recipe Import (URL)
1. User pastes URL → UI component
2. UI calls hook → `importService.parseUrl(url)`
3. Service invokes Supabase Edge Function → `POST /functions/v1/parse-recipe`
4. Edge Function fetches URL, extracts schema.org/Recipe JSON-LD
5. Returns structured recipe data → UI shows preview
6. User confirms → normal recipe creation flow

### Sync
- Supabase Realtime subscribes to `recipes` and `tags` table changes
- On INSERT/UPDATE/DELETE, all connected clients receive the change
- No conflict resolution needed (single user) — last write wins
- **Multi-user note**: Would need vector clocks or CRDT for true multi-user sync

## Layer Responsibilities

| Layer | Web | Android | Responsibility |
|-------|-----|---------|----------------|
| UI | React components | Composables | Render, user input, navigation |
| State | TanStack Query + Zustand | ViewModel + StateFlow | Cache, optimistic updates, UI state |
| Service | `src/shared/services/` | `shared/data/` repos | API calls, data transformation, error mapping |
| Domain | TypeScript types | Kotlin data classes | Business entities, validation rules |

## Edge Functions

Located in `supabase/functions/`:

| Function | Purpose | Trigger |
|----------|---------|---------|
| `parse-recipe` | Extract recipe from URL (schema.org) | HTTP POST |
| `parse-social` | Extract from social media (v2) | HTTP POST |
| `ocr-recipe` | Image → text → recipe (v2) | HTTP POST |
