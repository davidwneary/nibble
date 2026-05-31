# Testing Strategy

## Philosophy: Red/Green TDD

Every code change follows strict TDD:

1. **RED** — Write a failing test that describes the desired behavior
2. **GREEN** — Write the minimum code to make the test pass
3. **REFACTOR** — Clean up while keeping tests green

No implementation code is written without a corresponding test first.

## Test Pyramid

```
         ╱╲
        ╱ E2E ╲          Few — critical user flows only (v2+)
       ╱────────╲
      ╱Integration╲      Moderate — component + hook tests
     ╱──────────────╲
    ╱   Unit Tests    ╲   Many — services, utils, pure functions
   ╱────────────────────╲
```

## Web (React/TypeScript)

### Tools

| Tool | Purpose |
|------|---------|
| Vitest | Test runner (fast, Vite-native) |
| React Testing Library | Component testing (behavior-focused) |
| MSW (Mock Service Worker) | API mocking (intercepts fetch) |
| Playwright | E2E tests (v2+) |

### File Convention

Tests are co-located with source:
```
src/features/recipes/
├── RecipeCard.tsx
├── RecipeCard.test.tsx       ← Component test
├── hooks/
│   ├── use-recipes.ts
│   └── use-recipes.test.ts  ← Hook test
```

Shared service tests:
```
src/shared/services/
├── recipe-service.ts
├── recipe-service.test.ts   ← Service unit test
```

### Example: Service Test

```typescript
// src/shared/services/recipe-service.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { recipeService } from './recipe-service';
import { supabase } from './supabase';

vi.mock('./supabase');

describe('recipeService', () => {
  describe('getAll', () => {
    it('returns recipes ordered by creation date', async () => {
      const mockRecipes = [
        { id: '1', title: 'Pasta', created_at: '2026-01-02' },
        { id: '2', title: 'Salad', created_at: '2026-01-01' },
      ];

      vi.mocked(supabase.from).mockReturnValue({
        select: vi.fn().mockReturnValue({
          order: vi.fn().mockResolvedValue({ data: mockRecipes, error: null }),
        }),
      } as any);

      const result = await recipeService.getAll();
      expect(result).toEqual(mockRecipes);
    });

    it('throws ServiceError when fetch fails', async () => {
      vi.mocked(supabase.from).mockReturnValue({
        select: vi.fn().mockReturnValue({
          order: vi.fn().mockResolvedValue({ data: null, error: { message: 'Network error' } }),
        }),
      } as any);

      await expect(recipeService.getAll()).rejects.toThrow('Failed to fetch recipes');
    });
  });
});
```

### Example: Component Test

```typescript
// src/features/recipes/RecipeCard.test.tsx
import { render, screen } from '@testing-library/react';
import { RecipeCard } from './RecipeCard';

describe('RecipeCard', () => {
  it('renders recipe title and cooking time', () => {
    render(<RecipeCard recipe={{ title: 'Pasta', cook_time_minutes: 20 }} />);

    expect(screen.getByText('Pasta')).toBeInTheDocument();
    expect(screen.getByText('20 min')).toBeInTheDocument();
  });

  it('shows placeholder when no image', () => {
    render(<RecipeCard recipe={{ title: 'Pasta', image_url: null }} />);

    expect(screen.getByTestId('image-placeholder')).toBeInTheDocument();
  });
});
```

## Android (Kotlin)

### Tools

| Tool | Purpose |
|------|---------|
| JUnit 5 | Test runner |
| MockK | Mocking library |
| Turbine | Testing Kotlin Flows |
| Compose Testing | UI tests for Composables |

### File Convention

Mirror the main source in `test/`:
```
app/src/test/kotlin/com/nibble/
├── features/recipes/
│   └── RecipeListViewModelTest.kt
├── shared/data/
│   └── RecipeRepositoryTest.kt
```

### Example: ViewModel Test

```kotlin
@Test
fun `loadRecipes emits Success state with recipes`() = runTest {
    val recipes = listOf(Recipe(id = "1", title = "Pasta"))
    coEvery { repository.getAll() } returns recipes

    val viewModel = RecipeListViewModel(repository)

    viewModel.uiState.test {
        assertEquals(RecipeListUiState.Loading, awaitItem())
        assertEquals(RecipeListUiState.Success(recipes), awaitItem())
    }
}

@Test
fun `loadRecipes emits Error state on failure`() = runTest {
    coEvery { repository.getAll() } throws Exception("Network error")

    val viewModel = RecipeListViewModel(repository)

    viewModel.uiState.test {
        assertEquals(RecipeListUiState.Loading, awaitItem())
        val error = awaitItem() as RecipeListUiState.Error
        assertEquals("Network error", error.message)
    }
}
```

## Edge Functions (Deno)

```typescript
// supabase/functions/parse-recipe/parse-recipe.test.ts
import { assertEquals } from 'https://deno.land/std/testing/asserts.ts';
import { parseRecipeFromHtml } from './parser.ts';

Deno.test('extracts recipe from JSON-LD schema.org markup', () => {
  const html = `<script type="application/ld+json">
    {"@type": "Recipe", "name": "Pasta", "recipeIngredient": ["2 cups flour"]}
  </script>`;

  const result = parseRecipeFromHtml(html);
  assertEquals(result.title, 'Pasta');
  assertEquals(result.ingredients[0].text, '2 cups flour');
});
```

## Coverage Targets

| Area | Target | Rationale |
|------|--------|-----------|
| Services/Repositories | 90%+ | Critical data layer, easy to unit test |
| Hooks/ViewModels | 80%+ | Business logic, state management |
| Components/Composables | 70%+ | Test behavior, not pixels |
| Edge Functions | 90%+ | Recipe parsing correctness is critical |
| Overall | 80%+ | Sustainable without slowing development |

## Running Tests

```bash
# Web
cd web && npm test                    # Run all
cd web && npm test -- --watch         # Watch mode
cd web && npm run test:coverage       # With coverage report

# Android
cd android && ./gradlew test          # Run all
cd android && ./gradlew testDebug     # Debug variant only
cd android && ./gradlew jacocoReport  # Coverage report
```

## CI Integration

Tests run automatically on every PR via GitHub Actions. A PR cannot be merged if any test fails or coverage drops below thresholds.
