# API Conventions

## Supabase Service Layer

All Supabase interactions are wrapped in a service layer. UI components and hooks/ViewModels NEVER import the Supabase client directly.

## Web (TypeScript)

### Client Setup

```typescript
// src/shared/services/supabase.ts
import { createClient } from '@supabase/supabase-js';
import type { Database } from '../types/database';

export const supabase = createClient<Database>(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY
);
```

This file is the ONLY place that imports `createClient`. Everything else imports from service files.

### Service Pattern

```typescript
// src/shared/services/recipe-service.ts
import { supabase } from './supabase';
import type { Recipe, RecipeInsert, RecipeUpdate } from '../types/recipe';

export const recipeService = {
  async getAll(): Promise<Recipe[]> {
    const { data, error } = await supabase
      .from('recipes')
      .select('*, recipe_tags(tag_id, tags(*))')
      .order('created_at', { ascending: false });

    if (error) throw new ServiceError('Failed to fetch recipes', error);
    return data;
  },

  async getById(id: string): Promise<Recipe> {
    const { data, error } = await supabase
      .from('recipes')
      .select('*, recipe_tags(tag_id, tags(*))')
      .eq('id', id)
      .single();

    if (error) throw new ServiceError('Recipe not found', error);
    return data;
  },

  async create(recipe: RecipeInsert): Promise<Recipe> {
    const { data, error } = await supabase
      .from('recipes')
      .insert(recipe)
      .select()
      .single();

    if (error) throw new ServiceError('Failed to create recipe', error);
    return data;
  },

  async update(id: string, updates: RecipeUpdate): Promise<Recipe> {
    const { data, error } = await supabase
      .from('recipes')
      .update(updates)
      .eq('id', id)
      .select()
      .single();

    if (error) throw new ServiceError('Failed to update recipe', error);
    return data;
  },

  async delete(id: string): Promise<void> {
    const { error } = await supabase
      .from('recipes')
      .delete()
      .eq('id', id);

    if (error) throw new ServiceError('Failed to delete recipe', error);
  },

  async search(query: string): Promise<Recipe[]> {
    const { data, error } = await supabase
      .from('recipes')
      .select('*')
      .textSearch('title', query, { type: 'websearch' });

    if (error) throw new ServiceError('Search failed', error);
    return data;
  }
};
```

### Error Handling

```typescript
// src/shared/services/errors.ts
export class ServiceError extends Error {
  constructor(
    message: string,
    public readonly cause?: unknown,
    public readonly code?: string
  ) {
    super(message);
    this.name = 'ServiceError';
  }
}
```

### TanStack Query Integration

```typescript
// src/features/recipes/hooks/use-recipes.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { recipeService } from '@/shared/services/recipe-service';

export function useRecipes() {
  return useQuery({
    queryKey: ['recipes'],
    queryFn: recipeService.getAll,
  });
}

export function useCreateRecipe() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: recipeService.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recipes'] });
    },
  });
}
```

## Android (Kotlin)

### Repository Pattern

```kotlin
// shared/data/RecipeRepository.kt
class RecipeRepository(private val supabase: SupabaseClient) {

    suspend fun getAll(): List<Recipe> {
        return supabase.from("recipes")
            .select()
            .decodeList<RecipeDto>()
            .map { it.toDomain() }
    }

    suspend fun getById(id: String): Recipe {
        return supabase.from("recipes")
            .select { filter { eq("id", id) } }
            .decodeSingle<RecipeDto>()
            .toDomain()
    }

    suspend fun create(recipe: RecipeInsert): Recipe {
        return supabase.from("recipes")
            .insert(recipe.toDto())
            .decodeSingle<RecipeDto>()
            .toDomain()
    }

    suspend fun update(id: String, updates: RecipeUpdate): Recipe {
        return supabase.from("recipes")
            .update(updates.toDto()) { filter { eq("id", id) } }
            .decodeSingle<RecipeDto>()
            .toDomain()
    }

    suspend fun delete(id: String) {
        supabase.from("recipes")
            .delete { filter { eq("id", id) } }
    }
}
```

### ViewModel Pattern

```kotlin
// features/recipes/RecipeListViewModel.kt
class RecipeListViewModel(
    private val recipeRepository: RecipeRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow<RecipeListUiState>(RecipeListUiState.Loading)
    val uiState: StateFlow<RecipeListUiState> = _uiState.asStateFlow()

    init { loadRecipes() }

    fun loadRecipes() {
        viewModelScope.launch {
            _uiState.value = RecipeListUiState.Loading
            try {
                val recipes = recipeRepository.getAll()
                _uiState.value = RecipeListUiState.Success(recipes)
            } catch (e: Exception) {
                _uiState.value = RecipeListUiState.Error(e.message ?: "Unknown error")
            }
        }
    }
}

sealed interface RecipeListUiState {
    data object Loading : RecipeListUiState
    data class Success(val recipes: List<Recipe>) : RecipeListUiState
    data class Error(val message: String) : RecipeListUiState
}
```

## Realtime Subscriptions

### Web

```typescript
// src/shared/services/realtime.ts
import { supabase } from './supabase';

export function subscribeToRecipes(onUpdate: () => void) {
  return supabase
    .channel('recipes-changes')
    .on('postgres_changes', { event: '*', schema: 'public', table: 'recipes' }, onUpdate)
    .subscribe();
}
```

### Android

```kotlin
// shared/data/RealtimeManager.kt
class RealtimeManager(private val supabase: SupabaseClient) {
    fun subscribeToRecipes(onUpdate: () -> Unit): RealtimeChannel {
        return supabase.channel("recipes-changes").apply {
            postgresChangeFlow<PostgresAction>("public") {
                table = "recipes"
            }.onEach { onUpdate() }.launchIn(CoroutineScope(Dispatchers.IO))
            subscribe()
        }
    }
}
```

## Type Generation

Use Supabase CLI to auto-generate types from the database schema:

```bash
# Web (TypeScript)
supabase gen types typescript --local > web/src/shared/types/database.ts

# Android (Kotlin) - manual DTOs matching the schema
```

Regenerate types after every migration.
