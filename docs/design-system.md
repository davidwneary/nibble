# Design System

## Philosophy

Nibble's design is inspired by [Mela](https://mela.recipes/) on iOS — clean, minimal, typography-driven, with generous whitespace. It should feel like a premium native app, not a web app.

**Key Principles:**
- Content-first: recipes are the star, UI gets out of the way
- Soft and warm: rounded corners, subtle shadows, warm accent color
- Readable: large text for ingredients/instructions (especially cook mode later)
- Consistent cross-platform: same visual language on Android and web

## Color Tokens

### Light Theme

| Token | Hex | Usage |
|-------|-----|-------|
| `background` | `#FAFAFA` | Page/screen background |
| `surface` | `#FFFFFF` | Cards, modals, sheets |
| `surfaceHover` | `#F5F5F5` | Interactive card hover |
| `primary` | `#FF6B35` | Accent (buttons, links, active states) |
| `primaryHover` | `#E85A2A` | Button hover state |
| `textPrimary` | `#1A1A1A` | Headlines, body text |
| `textSecondary` | `#6D6D72` | Captions, metadata, timestamps |
| `textTertiary` | `#AEAEB2` | Placeholders, disabled text |
| `divider` | `#EAEAEB` | Separators, borders |
| `success` | `#34C759` | Save confirmations |
| `error` | `#FF3B30` | Validation errors, destructive actions |
| `warning` | `#FF9500` | Warnings |

### Dark Theme

| Token | Hex | Usage |
|-------|-----|-------|
| `background` | `#1C1C1E` | Page/screen background |
| `surface` | `#2C2C2E` | Cards, modals |
| `surfaceHover` | `#3A3A3C` | Interactive card hover |
| `primary` | `#FF8F5E` | Accent (slightly brighter for dark) |
| `primaryHover` | `#FFA070` | Button hover state |
| `textPrimary` | `#F5F5F5` | Headlines, body text |
| `textSecondary` | `#8E8E93` | Captions, metadata |
| `textTertiary` | `#636366` | Placeholders, disabled |
| `divider` | `#38383A` | Separators, borders |
| `success` | `#30D158` | Save confirmations |
| `error` | `#FF453A` | Errors |
| `warning` | `#FFD60A` | Warnings |

## Typography

### Font Stack

- **Web**: `Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif`
- **Android**: System default (Roboto) with custom weight mappings

### Scale

| Name | Web (Tailwind) | Android (sp) | Weight | Usage |
|------|----------------|--------------|--------|-------|
| `display` | `text-3xl` (30px) | 30sp | SemiBold (600) | Recipe title on detail page |
| `title` | `text-2xl` (24px) | 24sp | SemiBold (600) | Section titles, page headers |
| `heading` | `text-lg` (18px) | 18sp | SemiBold (600) | Card titles, sub-headers |
| `body` | `text-base` (16px) | 16sp | Regular (400) | Body text, ingredients, instructions |
| `bodySmall` | `text-sm` (14px) | 14sp | Regular (400) | Secondary body text |
| `caption` | `text-xs` (12px) | 12sp | Medium (500) | Metadata, timestamps, tags |

### Line Height

- Body text: 1.6 (relaxed, for readability)
- Headings: 1.3 (tighter)
- Captions: 1.4

## Spacing

8px base grid:

| Token | Value | Usage |
|-------|-------|-------|
| `xs` | 4px | Inline spacing, icon gaps |
| `sm` | 8px | Tight spacing within components |
| `md` | 16px | Standard padding, gaps |
| `lg` | 24px | Section spacing |
| `xl` | 32px | Large gaps between sections |
| `2xl` | 48px | Page-level vertical rhythm |
| `3xl` | 64px | Hero spacing |

## Border Radius

| Token | Value | Usage |
|-------|-------|-------|
| `sm` | 8px | Inputs, small buttons |
| `md` | 12px | Buttons, chips |
| `lg` | 16px | Cards, modals |
| `xl` | 24px | Large cards, sheets |
| `full` | 9999px | Pills, avatars, tags |

## Shadows

| Token | Value | Usage |
|-------|-------|-------|
| `sm` | `0 1px 3px rgba(0,0,0,0.06)` | Subtle lift (inputs) |
| `md` | `0 4px 12px rgba(0,0,0,0.08)` | Cards |
| `lg` | `0 8px 24px rgba(0,0,0,0.12)` | Modals, floating elements |

## Components

### Recipe Card

```
┌─────────────────────────────┐
│  ┌───────────────────────┐  │
│  │                       │  │  ← Hero image (16:9 aspect ratio)
│  │       [Image]         │  │     Rounded top corners (16px)
│  │                       │  │
│  └───────────────────────┘  │
│                              │
│  Recipe Title                │  ← heading weight
│  30 min · 4 servings        │  ← caption, textSecondary
│                              │
│  [tag] [tag]                 │  ← pill chips, small
│                              │
└─────────────────────────────┘   ← surface background, shadow-md, radius-lg
```

### Recipe Detail

```
┌──────────────────────────────────────┐
│  [← Back]            [Edit] [Delete] │  ← Nav bar
├──────────────────────────────────────┤
│                                      │
│         [Hero Image - full width]    │
│                                      │
├──────────────────────────────────────┤
│                                      │
│  Recipe Title (display)              │
│  Source: example.com                 │  ← textSecondary, linked
│                                      │
│  ┌──────┬──────┬──────┐             │
│  │ Prep │ Cook │Serves│             │  ← Metadata pills
│  │15 min│30 min│  4   │             │
│  └──────┴──────┴──────┘             │
│                                      │
│  ── Ingredients ─────────────        │  ← Section divider
│                                      │
│  • 2 cups flour                      │
│  • 1 tsp salt                        │
│  • 1 cup warm water                  │
│                                      │
│  ── Instructions ────────────        │  ← Section divider
│                                      │
│  1. Preheat oven to 180°C.          │
│  2. Mix flour and salt...            │
│  3. Add water gradually...           │
│                                      │
│  ── Notes ───────────────────        │
│                                      │
│  Great with a side salad.            │
│                                      │
└──────────────────────────────────────┘
```

## Tailwind Config (Web)

```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        background: 'var(--color-background)',
        surface: 'var(--color-surface)',
        'surface-hover': 'var(--color-surface-hover)',
        primary: 'var(--color-primary)',
        'primary-hover': 'var(--color-primary-hover)',
        'text-primary': 'var(--color-text-primary)',
        'text-secondary': 'var(--color-text-secondary)',
        'text-tertiary': 'var(--color-text-tertiary)',
        divider: 'var(--color-divider)',
        success: 'var(--color-success)',
        error: 'var(--color-error)',
        warning: 'var(--color-warning)',
      },
      borderRadius: {
        sm: '8px',
        md: '12px',
        lg: '16px',
        xl: '24px',
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
      },
      boxShadow: {
        sm: '0 1px 3px rgba(0,0,0,0.06)',
        md: '0 4px 12px rgba(0,0,0,0.08)',
        lg: '0 8px 24px rgba(0,0,0,0.12)',
      },
    },
  },
};
```

## Android Theme

Custom Compose theme — see `android/app/src/main/kotlin/com/nibble/shared/ui/theme/` for implementation.

Key: Do NOT use `MaterialTheme`. Use `NibbleTheme` with custom `NibbleColors`, `NibbleTypography`, and `NibbleShapes`.

## Iconography

- Web: Lucide React icons (consistent, clean line icons)
- Android: Custom or Lucide equivalent (NOT Material Icons)
- Icon size: 20px (inline), 24px (navigation), 32px (empty states)
- Icon weight: Regular/Medium (1.5px stroke)

## Animations

- Transitions: 200ms ease-out (default), 300ms for page transitions
- No bouncy or playful animations — smooth and subtle
- Skeleton loaders for async content (not spinners)
