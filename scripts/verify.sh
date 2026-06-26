#!/usr/bin/env bash
set -euo pipefail

echo "=== Spec Verification ==="
echo ""

bash scripts/check-spec-links.sh
bash scripts/check-target-ownership.sh
if command -v python3 >/dev/null 2>&1; then
  python3 scripts/build-spec-manifest.py
else
  python scripts/build-spec-manifest.py
fi

echo ""
echo "Spec checks passed. Running test suite..."
echo ""

if [ -f "pytest.ini" ] || [ -f "pyproject.toml" ] || [ -f "setup.cfg" ]; then
    if command -v poetry >/dev/null 2>&1 && [ -f "poetry.lock" ]; then
        poetry run pytest tests/ -v
    else
        pytest tests/ -v
    fi
elif [ -f "package.json" ] && grep -q '"test"' package.json; then
    npm test
elif [ -f "Cargo.toml" ]; then
    cargo test
else
    echo "No test runner detected. Run your test suite manually."
    exit 1
fi
