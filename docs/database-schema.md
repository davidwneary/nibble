# Database Schema

## Overview

All tables live in Supabase PostgreSQL with Row-Level Security (RLS) enabled. The schema is designed to be multi-user safe from day one.

## Tables

### `recipes`

The core table storing all recipe data.

```sql
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
  image_path TEXT,  -- Supabase Storage path (if uploaded)
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER recipes_updated_at
  BEFORE UPDATE ON recipes
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();
```

#### `ingredients` JSONB Structure

```json
[
  { "text": "2 cups flour", "group": "Dough" },
  { "text": "1 tsp salt", "group": "Dough" },
  { "text": "1 cup warm water", "group": "Dough" },
  { "text": "2 tbsp olive oil", "group": "Filling" }
]
```

- `text`: The ingredient as written (human-readable)
- `group`: Optional grouping (e.g., "Dough", "Sauce", "Garnish")

#### `instructions` JSONB Structure

```json
[
  { "step": 1, "text": "Preheat oven to 180°C.", "group": null },
  { "step": 2, "text": "Mix flour and salt in a bowl.", "group": "Dough" },
  { "step": 3, "text": "Add water gradually...", "group": "Dough" }
]
```

### `tags`

User-created tags for organizing recipes.

```sql
CREATE TABLE tags (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) NOT NULL,
  name TEXT NOT NULL,
  color TEXT,  -- Optional hex color for display
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(user_id, name)
);
```

### `recipe_tags`

Many-to-many junction table.

```sql
CREATE TABLE recipe_tags (
  recipe_id UUID REFERENCES recipes(id) ON DELETE CASCADE,
  tag_id UUID REFERENCES tags(id) ON DELETE CASCADE,
  PRIMARY KEY (recipe_id, tag_id)
);
```

## Indexes

```sql
-- Full-text search on recipes
CREATE INDEX recipes_fts_idx ON recipes
  USING GIN (to_tsvector('english', coalesce(title, '') || ' ' || coalesce(notes, '') || ' ' || coalesce(description, '')));

-- Fast lookup by user
CREATE INDEX recipes_user_id_idx ON recipes(user_id);
CREATE INDEX tags_user_id_idx ON tags(user_id);

-- Fast tag filtering
CREATE INDEX recipe_tags_recipe_idx ON recipe_tags(recipe_id);
CREATE INDEX recipe_tags_tag_idx ON recipe_tags(tag_id);
```

## Row-Level Security (RLS)

```sql
-- Recipes
ALTER TABLE recipes ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can CRUD own recipes"
  ON recipes FOR ALL
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- Tags
ALTER TABLE tags ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can CRUD own tags"
  ON tags FOR ALL
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- Recipe Tags (access if user owns the recipe)
ALTER TABLE recipe_tags ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage tags on own recipes"
  ON recipe_tags FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM recipes
      WHERE recipes.id = recipe_tags.recipe_id
      AND recipes.user_id = auth.uid()
    )
  );
```

## Storage Buckets

```sql
-- Create bucket for recipe images
INSERT INTO storage.buckets (id, name, public)
VALUES ('recipe-images', 'recipe-images', true);

-- Policy: users can upload to their own folder
CREATE POLICY "Users can upload own images"
  ON storage.objects FOR INSERT
  WITH CHECK (
    bucket_id = 'recipe-images'
    AND (storage.foldername(name))[1] = auth.uid()::text
  );

-- Policy: anyone can read (images are public)
CREATE POLICY "Public read for recipe images"
  ON storage.objects FOR SELECT
  USING (bucket_id = 'recipe-images');
```

Image path convention: `recipe-images/{user_id}/{recipe_id}.{ext}`

## Migrations

All schema changes go in `supabase/migrations/` with timestamps:
```
supabase/migrations/
├── 20260601000000_create_recipes.sql
├── 20260601000001_create_tags.sql
├── 20260601000002_create_recipe_tags.sql
├── 20260601000003_add_indexes.sql
├── 20260601000004_add_rls_policies.sql
└── 20260601000005_create_storage_bucket.sql
```
