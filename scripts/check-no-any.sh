#!/bin/bash
# Architecture Guard: No 'any' type in TypeScript
# Usage: ./scripts/check-no-any.sh [web]
set -e

PLATFORM="${1:-web}"

echo "=== No-Any Type Guard ==="
echo "Platform: $PLATFORM"
echo ""

if [[ "$PLATFORM" == "web" ]]; then
  # Find explicit 'any' type annotations
  # Match: ': any', 'as any', '<any>', 'any[]', 'any |', '| any'
  # Exclude: test files (mocks sometimes need any), type definition files
  VIOLATIONS=$(grep -rn \
    --include="*.ts" --include="*.tsx" \
    -E ':\s*any\b|as\s+any\b|<any>|any\[\]|\bany\s*\||\|\s*any\b' \
    web/src/ 2>/dev/null \
    | grep -v "\.test\." \
    | grep -v "\.d\.ts" \
    | grep -v "// eslint-disable" \
    | grep -v "// @ts-ignore" \
    || true)

  if [[ -n "$VIOLATIONS" ]]; then
    echo "❌ FAIL: 'any' type annotations found in source code:"
    echo ""
    echo "$VIOLATIONS"
    echo ""
    echo "Fix: Replace 'any' with a proper type, 'unknown', or a type guard."
    exit 1
  else
    echo "✅ PASS: No 'any' type annotations in source code"
  fi
fi
