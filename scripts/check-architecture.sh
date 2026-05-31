#!/bin/bash
# Architecture Guard: Ensures layer boundaries are respected.
# Usage: ./scripts/check-architecture.sh [web|android]
set -e

PLATFORM="${1:-all}"
EXIT_CODE=0

echo "=== Architecture Guard ==="
echo "Platform: $PLATFORM"
echo ""

# --- Web checks ---
if [[ "$PLATFORM" == "web" || "$PLATFORM" == "all" ]]; then
  echo "--- Web Architecture Checks ---"

  # Rule: Only shared/services/ may import from @supabase/supabase-js
  echo "[1/3] Checking Supabase import boundaries..."
  VIOLATIONS=$(grep -r "from.*@supabase/supabase-js\|from.*supabase" web/src/ \
    --include="*.ts" --include="*.tsx" \
    -l 2>/dev/null | grep -v "shared/services/" | grep -v "node_modules" || true)

  if [[ -n "$VIOLATIONS" ]]; then
    echo "❌ FAIL: Direct Supabase imports found outside shared/services/:"
    echo "$VIOLATIONS"
    EXIT_CODE=1
  else
    echo "✅ PASS: All Supabase imports are in shared/services/"
  fi

  # Rule: Features should not import from other features
  echo "[2/3] Checking feature isolation..."
  FEATURE_VIOLATIONS=""
  if [[ -d "web/src/features" ]]; then
    for feature_dir in web/src/features/*/; do
      feature_name=$(basename "$feature_dir")
      OTHER_FEATURES=$(grep -r "from.*features/" "$feature_dir" \
        --include="*.ts" --include="*.tsx" \
        -l 2>/dev/null | xargs grep -l "features/" 2>/dev/null | while read -r file; do
          grep "from.*features/" "$file" | grep -v "features/$feature_name" || true
        done)
      if [[ -n "$OTHER_FEATURES" ]]; then
        FEATURE_VIOLATIONS="$FEATURE_VIOLATIONS\n$OTHER_FEATURES"
      fi
    done
  fi

  if [[ -n "$FEATURE_VIOLATIONS" ]]; then
    echo "❌ FAIL: Cross-feature imports found:"
    echo -e "$FEATURE_VIOLATIONS"
    EXIT_CODE=1
  else
    echo "✅ PASS: Features are isolated"
  fi

  # Rule: No default exports
  echo "[3/3] Checking for default exports..."
  DEFAULT_EXPORTS=$(grep -r "export default" web/src/ \
    --include="*.ts" --include="*.tsx" \
    -l 2>/dev/null | grep -v "node_modules" | grep -v ".test." || true)

  if [[ -n "$DEFAULT_EXPORTS" ]]; then
    echo "⚠️  WARN: Default exports found (prefer named exports):"
    echo "$DEFAULT_EXPORTS"
    # Warning only, not a hard failure
  else
    echo "✅ PASS: No default exports"
  fi

  echo ""
fi

# --- Android checks ---
if [[ "$PLATFORM" == "android" || "$PLATFORM" == "all" ]]; then
  echo "--- Android Architecture Checks ---"

  # Rule: Only shared/data/ may import Supabase client
  echo "[1/2] Checking Supabase import boundaries..."
  VIOLATIONS=$(grep -r "import.*io.github.jan.supabase\|import.*SupabaseClient" android/app/src/main/ \
    --include="*.kt" \
    -l 2>/dev/null | grep -v "shared/data/" | grep -v "shared/di/" || true)

  if [[ -n "$VIOLATIONS" ]]; then
    echo "❌ FAIL: Direct Supabase imports found outside shared/data/:"
    echo "$VIOLATIONS"
    EXIT_CODE=1
  else
    echo "✅ PASS: All Supabase imports are in shared/data/"
  fi

  # Rule: No MaterialTheme usage
  echo "[2/2] Checking for Material Design usage..."
  MATERIAL_VIOLATIONS=$(grep -r "MaterialTheme\|material3\|androidx.compose.material3" android/app/src/main/ \
    --include="*.kt" \
    -l 2>/dev/null || true)

  if [[ -n "$MATERIAL_VIOLATIONS" ]]; then
    echo "❌ FAIL: Material Design references found (use NibbleTheme):"
    echo "$MATERIAL_VIOLATIONS"
    EXIT_CODE=1
  else
    echo "✅ PASS: No Material Design usage"
  fi

  echo ""
fi

if [[ $EXIT_CODE -ne 0 ]]; then
  echo "=== ❌ Architecture checks FAILED ==="
  exit 1
else
  echo "=== ✅ All architecture checks passed ==="
fi
