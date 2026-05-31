# Android App Setup

## Tech Stack

| Library | Purpose |
|---------|---------|
| Kotlin 2.0+ | Language |
| Jetpack Compose (BOM latest) | UI framework |
| Compose Navigation | Type-safe navigation |
| Supabase Kotlin SDK | Backend communication |
| Koin | Dependency injection |
| Kotlin Coroutines + Flow | Async, reactive state |
| Coil | Image loading |
| JUnit 5 | Test runner |
| MockK | Mocking |
| Turbine | Flow testing |
| ktlint | Code formatting |

## Project Structure

```
android/app/src/main/kotlin/com/nibble/
├── app/
│   ├── NibbleApp.kt              # Application class, Koin init
│   ├── MainActivity.kt           # Single activity
│   └── navigation/
│       ├── NavGraph.kt           # Route definitions
│       └── Routes.kt             # Type-safe route objects
├── features/
│   ├── auth/
│   │   ├── LoginScreen.kt
│   │   └── LoginViewModel.kt
│   ├── recipes/
│   │   ├── list/
│   │   │   ├── RecipeListScreen.kt
│   │   │   └── RecipeListViewModel.kt
│   │   ├── detail/
│   │   │   ├── RecipeDetailScreen.kt
│   │   │   └── RecipeDetailViewModel.kt
│   │   ├── form/
│   │   │   ├── RecipeFormScreen.kt
│   │   │   └── RecipeFormViewModel.kt
│   │   └── components/
│   │       ├── RecipeCard.kt
│   │       └── IngredientList.kt
│   ├── tags/
│   │   └── ...
│   └── import/
│       └── ...
├── shared/
│   ├── data/                     # Repository layer
│   │   ├── RecipeRepository.kt
│   │   ├── TagRepository.kt
│   │   ├── AuthRepository.kt
│   │   └── dto/                  # Data Transfer Objects
│   │       ├── RecipeDto.kt
│   │       └── TagDto.kt
│   ├── domain/                   # Business models
│   │   ├── Recipe.kt
│   │   ├── Tag.kt
│   │   └── RecipeImport.kt
│   ├── di/                       # Koin modules
│   │   ├── AppModule.kt
│   │   ├── DataModule.kt
│   │   └── FeatureModule.kt
│   └── ui/
│       ├── theme/
│       │   ├── NibbleTheme.kt    # Custom theme (NOT Material)
│       │   ├── Color.kt
│       │   ├── Typography.kt
│       │   └── Shape.kt
│       └── components/           # Shared composables
│           ├── NibbleButton.kt
│           ├── NibbleCard.kt
│           ├── NibbleTextField.kt
│           └── NibbleTopBar.kt
```

## Custom Theme (NOT Material Design)

```kotlin
// shared/ui/theme/NibbleTheme.kt
@Composable
fun NibbleTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit
) {
    val colors = if (darkTheme) DarkNibbleColors else LightNibbleColors
    val typography = NibbleTypography

    CompositionLocalProvider(
        LocalNibbleColors provides colors,
        LocalNibbleTypography provides typography,
    ) {
        Surface(
            color = colors.background,
            contentColor = colors.textPrimary,
        ) {
            content()
        }
    }
}

// Usage: NibbleTheme.colors.primary, NibbleTheme.typography.heading
object NibbleTheme {
    val colors: NibbleColors @Composable get() = LocalNibbleColors.current
    val typography: NibbleTypography @Composable get() = LocalNibbleTypography.current
}
```

## Key Rules

1. **No MaterialTheme** — use `NibbleTheme` exclusively
2. **No Material Design components** — build custom or use Foundation
3. **MVVM architecture** — ViewModels expose `StateFlow`, Composables collect
4. **Repository pattern** — all Supabase calls go through repositories
5. **Koin for DI** — modules defined in `shared/di/`
6. **Coroutines only** — no RxJava, no callbacks

## Build Configuration

```kotlin
// build.gradle.kts (app)
android {
    namespace = "com.nibble"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.nibble"
        minSdk = 26
        targetSdk = 35
    }

    buildFeatures {
        compose = true
    }
}
```

## Commands

```bash
./gradlew build              # Full build
./gradlew test               # Unit tests
./gradlew ktlintCheck        # Lint check
./gradlew ktlintFormat       # Auto-format
./gradlew assembleDebug      # Debug APK
./gradlew assembleRelease    # Release APK (needs signing config)
```

## Distribution

For personal use: sideload debug APK directly.
Later: Play Store ($25 one-time fee) if making public.
