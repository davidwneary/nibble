# Web App Setup

## Tech Stack

| Library | Version | Purpose |
|---------|---------|---------|
| React | 18+ | UI framework |
| TypeScript | 5+ | Type safety (strict mode) |
| Vite | 5+ | Build tool, dev server |
| Tailwind CSS | 3+ | Utility-first styling |
| TanStack Query | 5+ | Server state management |
| Zustand | 4+ | Client UI state |
| React Router | 6+ | Client-side routing |
| Supabase JS | 2+ | Backend SDK |
| Vitest | 1+ | Test runner |
| React Testing Library | 14+ | Component testing |
| MSW | 2+ | API mocking in tests |
| Lucide React | latest | Icons |

## Project Initialization

```bash
npm create vite@latest web -- --template react-ts
cd web
npm install @supabase/supabase-js @tanstack/react-query zustand react-router-dom lucide-react
npm install -D tailwindcss postcss autoprefixer vitest @testing-library/react @testing-library/jest-dom msw happy-dom
npx tailwindcss init -p
```

## Folder Structure

```
web/src/
├── app/                    # App shell
│   ├── App.tsx            # Root component, providers
│   ├── Router.tsx         # Route definitions
│   └── providers.tsx      # QueryClient, Auth, Theme providers
├── features/              # Feature modules (self-contained)
│   ├── auth/
│   │   ├── LoginPage.tsx
│   │   ├── hooks/
│   │   └── components/
│   ├── recipes/
│   │   ├── RecipeListPage.tsx
│   │   ├── RecipeDetailPage.tsx
│   │   ├── RecipeFormPage.tsx
│   │   ├── components/
│   │   │   ├── RecipeCard.tsx
│   │   │   ├── RecipeCard.test.tsx
│   │   │   ├── IngredientList.tsx
│   │   │   └── InstructionList.tsx
│   │   └── hooks/
│   │       ├── use-recipes.ts
│   │       └── use-recipes.test.ts
│   ├── tags/
│   │   ├── components/
│   │   └── hooks/
│   └── import/
│       ├── ImportPage.tsx
│       ├── components/
│       └── hooks/
├── shared/                # Shared across features
│   ├── components/        # Generic UI components
│   │   ├── Button.tsx
│   │   ├── Input.tsx
│   │   ├── Card.tsx
│   │   ├── Modal.tsx
│   │   └── Skeleton.tsx
│   ├── hooks/            # Generic hooks
│   │   └── use-debounce.ts
│   ├── services/         # Supabase service layer
│   │   ├── supabase.ts   # Client initialization (ONLY import point)
│   │   ├── recipe-service.ts
│   │   ├── tag-service.ts
│   │   ├── auth-service.ts
│   │   ├── image-service.ts
│   │   └── errors.ts
│   ├── types/            # TypeScript types
│   │   ├── database.ts   # Auto-generated from Supabase
│   │   ├── recipe.ts
│   │   └── tag.ts
│   └── utils/            # Pure utility functions
│       ├── format-time.ts
│       └── format-time.test.ts
├── styles/
│   ├── globals.css       # Tailwind directives + CSS variables
│   └── tokens.css        # Design token CSS custom properties
├── main.tsx              # Entry point
└── vite-env.d.ts
```

## Key Rules

1. **No default exports** (except route-level pages if using lazy loading)
2. **No `any` types** — use `unknown` + type guards
3. **No CSS-in-JS** — Tailwind only
4. **No direct Supabase imports** outside `shared/services/`
5. **Tests co-located** with source files
6. **Feature folders are self-contained** — cross-feature imports go through `shared/`

## Environment Variables

```bash
# .env.local (gitignored)
VITE_SUPABASE_URL=https://xxxxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJ...
```

## Scripts (package.json)

```json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint src/ --ext .ts,.tsx --max-warnings 0",
    "typecheck": "tsc --noEmit",
    "test": "vitest run",
    "test:watch": "vitest",
    "test:coverage": "vitest run --coverage"
  }
}
```

## Deployment

Push to `main` → Cloudflare Pages auto-builds → live at `nibble.pages.dev`

Build command: `npm run build`
Output directory: `dist`
