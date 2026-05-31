# Recipe Management App - Requirements & Implementation Plan

> **Development Methodology**: Agent-led development using OpenAI Symphony + Linear.
> See [AGENT-SETUP.md](./AGENT-SETUP.md) for the harness setup plan that must be completed before app development begins.

## Overview

A personal recipe management app (Android + Web) inspired by [Mela](https://mela.recipes/), focused on collecting, organizing, and viewing recipes from various sources. Single-user initially, with a path to multi-user support.

## Tech Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Android | Kotlin + Jetpack Compose | Modern Android-native, excellent performance |
| Web | React + TypeScript | Widely supported, large ecosystem |
| Backend/DB | Supabase (PostgreSQL + Auth + Storage) | Free tier, zero maintenance, real-time sync built-in |
| Recipe Parsing | Server-side function (Supabase Edge Functions) | Extracts structured data from recipe URLs |
| Shared | Supabase client SDKs | Consistent API for both platforms |

## Architecture

```
┌─────────────┐    ┌─────────────┐
│  Android    │    │   Web App   │
│  (Kotlin)   │    │  (React/TS) │
└──────┬──────┘    └──────┬──────┘
       │                   │
       └───────┬───────────┘
               │ HTTPS (REST API + JWT)
       ┌───────▼───────┐
       │   Supabase    │
       │  ┌──────────┐ │
       │  │ Auth     │ │  ← Single user (email/password)
       │  │ PostgREST│ │  ← Secure API layer (NOT raw SQL)
       │  │ Postgres │ │  ← Recipe data, tags (behind RLS)
       │  │ Storage  │ │  ← Recipe images
       │  │ Edge Fn  │ │  ← URL parsing, (later: OCR)
       │  │ Realtime │ │  ← Cross-device sync
       │  └──────────┘ │
       └───────────────┘
```

## Security Model

**Q: Is it secure for the web app to talk directly to the database?**

**A: It doesn't.** The clients (Android/Web) talk to Supabase's **REST API (PostgREST)**, not raw PostgreSQL. Here's the security chain:

```
Browser/App → HTTPS → Supabase API Gateway → PostgREST → PostgreSQL
                         │                        │
                    Validates JWT            Enforces RLS policies
                    (rejects invalid)        (users see only own data)
```

**Security layers:**

1. **No raw SQL access** — Clients use the Supabase SDK which makes REST API calls (e.g., `GET /rest/v1/recipes?user_id=eq.abc`). No way to run arbitrary SQL.
2. **API keys** — The public `anon` key only allows access that RLS policies permit. The private `service_role` key is NEVER exposed to the frontend.
3. **JWT authentication** — After login, every request carries a signed JWT. Supabase validates the signature server-side before processing.
4. **Row-Level Security (RLS)** — PostgreSQL itself enforces that `auth.uid() = user_id` on every query. Even if someone crafts a malicious API request, RLS blocks access to other users' data.
5. **HTTPS everywhere** — All communication is encrypted in transit.

**What this means in practice:**
- An attacker who finds your Supabase URL + anon key still can't access your data without a valid JWT
- Even with a valid JWT, RLS ensures they only see data tagged with their own `user_id`
- This is the same security model used by thousands of production apps on Supabase

**Scalability note:** This architecture is already multi-user safe. Adding more users requires no security changes — RLS handles isolation automatically.

---

## What's NOT Needed (Explicitly Out of Scope)

- ❌ iOS support (Mela already covers this)
- ❌ Multi-user / sharing / social features (initially)
- ❌ Payment processing
- ❌ Email notifications
- ❌ Complex analytics / recommendation engine
- ❌ Offline-first architecture (nice-to-have later, not MVP)
- ❌ Native desktop app (web covers this)
- ❌ Internationalization / localization (English only)

---

## MVP (Version 1.0)

**Goal**: A working recipe collection app that syncs across Android and web.

### Core Features

1. **Recipe CRUD**
   - Create recipes manually (title, ingredients, instructions, prep/cook time, servings, notes)
   - Edit and delete recipes
   - View recipe in a clean, readable format

2. **URL Import**
   - Paste a URL → extract recipe using structured data (JSON-LD, Microdata, schema.org/Recipe)
   - Handle common recipe sites (most use schema.org markup)
   - Fallback: manual entry if parsing fails
   - Show a preview before saving

3. **Organization**
   - Tag recipes with custom tags (e.g., "quick", "italian", "weeknight")
   - Full-text search across title, ingredients, and instructions
   - Filter by tags

4. **Sync**
   - Real-time sync via Supabase Realtime (automatic, no user action needed)
   - Works across Android app and web app simultaneously

5. **Image Support**
   - Store one hero image per recipe (from URL import or manual upload)
   - Images stored in Supabase Storage (1GB free)

6. **Authentication**
   - Single-user email/password login via Supabase Auth
   - Row-level security (RLS) on all tables — future-proofs for multi-user

### Scalability Trade-offs in MVP

| Decision | Single-user shortcut | Multi-user change needed |
|----------|---------------------|--------------------------|
| Auth | Hardcoded single user, simple email/password | Add registration flow, email verification, password reset |
| RLS policies | `auth.uid() = user_id` (already multi-user safe) | No change needed ✓ |
| Search | PostgreSQL full-text search (pg_trgm) | Move to dedicated search (Meilisearch/Typesense) at ~10K+ recipes |
| Storage | Single bucket, no quotas | Per-user quotas, CDN for images |
| Edge Functions | No rate limiting | Add rate limiting, queue for heavy operations |
| Database | Single Supabase project | Connection pooling, read replicas at scale |

---

## Version 2.0 - Enhanced Import

1. **Social Media Import**
   - Parse recipe content from Instagram posts/reels (captions + images)
   - Parse TikTok video descriptions
   - YouTube video description parsing
   - Likely requires: screenshot/transcript → LLM extraction

2. **Image/OCR Import**
   - Take a photo of a recipe book page
   - OCR via Google Cloud Vision or Tesseract
   - Structured extraction (ingredients vs. instructions) via LLM
   - ⚠️ This is the most complex feature — may need a paid API (Google Vision, OpenAI)

3. **In-App Browser**
   - Browse recipe sites within the app
   - Auto-detect recipes on current page (like Mela)
   - One-tap save

---

## Version 3.0 - Cooking & Planning

1. **Cook Mode**
   - Full-screen step-by-step view
   - Larger font, dimmed inactive steps
   - Ingredient check-off
   - Built-in timers (per step)
   - Keep screen awake

2. **Grocery List**
   - Generate shopping list from selected recipes
   - Combine duplicate ingredients (e.g., 2 recipes needing onions)
   - Check off items while shopping
   - Optional: export to a reminders/todo app

3. **Meal Planning Calendar**
   - Assign recipes to dates
   - Weekly/monthly view
   - Generate grocery list from planned meals

---

## Version 4.0 - Discovery & Polish

1. **RSS Feed Subscriptions**
   - Subscribe to recipe blog feeds
   - Auto-detect recipes in feed items
   - "Feed inbox" — save to collection with one tap

2. **Offline Support**
   - Cache recently viewed recipes locally
   - Queue changes when offline, sync when back online
   - Android: Room database as local cache
   - Web: IndexedDB + service worker

3. **Collections/Categories**
   - Group recipes into named collections
   - Smart collections (auto-filter by criteria)

4. **Serving Size Adjustment**
   - Scale ingredient quantities up/down
   - Fraction/decimal smart formatting

---

## Database Schema (MVP)

```sql
-- Recipes table
CREATE TABLE recipes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  ingredients JSONB NOT NULL DEFAULT '[]',
  instructions JSONB NOT NULL DEFAULT '[]',
  prep_time_minutes INTEGER,
  cook_time_minutes INTEGER,
  total_time_minutes INTEGER,
  servings INTEGER,
  source_url TEXT,
  image_url TEXT,
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Tags table
CREATE TABLE tags (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) NOT NULL,
  name TEXT NOT NULL,
  UNIQUE(user_id, name)
);

-- Recipe-tag junction
CREATE TABLE recipe_tags (
  recipe_id UUID REFERENCES recipes(id) ON DELETE CASCADE,
  tag_id UUID REFERENCES tags(id) ON DELETE CASCADE,
  PRIMARY KEY (recipe_id, tag_id)
);

-- Full-text search index
CREATE INDEX recipes_search_idx ON recipes
  USING GIN (to_tsvector('english', title || ' ' || notes));

-- RLS policies (future-proof for multi-user)
ALTER TABLE recipes ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can CRUD own recipes"
  ON recipes FOR ALL
  USING (auth.uid() = user_id);
```

---

## Implementation Order (MVP Todos)

1. **Project setup** — Initialize Supabase project, Kotlin Android project, React web project
2. **Database schema** — Create tables, RLS policies, indexes in Supabase
3. **Auth flow** — Login/logout on both platforms
4. **Recipe CRUD (web)** — Create, read, update, delete recipes via React UI
5. **Recipe CRUD (Android)** — Same functionality in Kotlin/Compose
6. **URL import** — Edge Function to parse recipe URLs (schema.org/Recipe extraction)
7. **Tags & search** — Tag management, full-text search
8. **Image upload** — Hero image storage and display
9. **Real-time sync** — Verify changes propagate between platforms
10. **Polish & deploy** — Error handling, loading states, responsive design

---

## Supabase Free Tier Limits (relevant)

| Resource | Limit | Sufficient for single user? |
|----------|-------|-----------------------------|
| Database | 500 MB | ✅ ~50K+ recipes with metadata |
| Storage | 1 GB | ✅ ~2000-5000 recipe images |
| Edge Function invocations | 500K/month | ✅ Way more than needed |
| Realtime connections | 200 concurrent | ✅ Only need 2-3 devices |
| Auth users | 50K MAU | ✅ Just 1 user |
| Bandwidth | 5 GB/month | ✅ Comfortable for personal use |

---

## Web Hosting Decision

**Recommendation: Cloudflare Pages (free tier)** ✅

| Provider | Bandwidth | Builds | Why/Why Not |
|----------|-----------|--------|-------------|
| **Cloudflare Pages** | ♾️ Unlimited | ♾️ Unlimited | Best free tier, global CDN, fast |
| Vercel | 100 GB/mo | Unlimited (public) | Great for Next.js, slightly more restrictive |
| Netlify | 100 GB/mo | 300 min/mo | Build minute limit is annoying |

**Why not the Raspberry Pi?**
- The React web app is a **static site** (HTML/JS/CSS) — it talks to Supabase directly from the browser
- No server-side rendering needed, so no reason to run your own server
- Cloudflare Pages gives you: free HTTPS, custom domain support, global CDN, instant deploys from Git, zero maintenance
- Pi downsides: need dynamic DNS, port forwarding, SSL setup, slow on Pi 1, unavailable during ISP outages

**Deployment workflow**: Push to GitHub → Cloudflare auto-builds and deploys → live in ~30 seconds.

**Custom domain**: Optional. Cloudflare gives you `your-app.pages.dev` for free, or you can attach a custom domain (domain registration costs ~$10/year separately).

---

## Open Questions / Decisions for Later

- **Android distribution**: Play Store ($25 one-time) vs. direct APK sideload?
- **OCR provider** (v2): Google Cloud Vision vs. Apple Vision vs. local Tesseract?
- **LLM for extraction** (v2): OpenAI API vs. local model vs. Supabase AI?
