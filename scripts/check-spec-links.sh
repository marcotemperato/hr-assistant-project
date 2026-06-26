#!/usr/bin/env bash
set -euo pipefail

if command -v python3 >/dev/null 2>&1; then
  PYTHON=python3
else
  PYTHON=python
fi

"$PYTHON" - <<'PY'
from pathlib import Path
import re
import sys

spec_root = Path("specs")
pattern = re.compile(r"\[@test\]\s+([^\s`)]+)")
missing = []

for spec in sorted(spec_root.glob("**/*.spec.md")):
    text = spec.read_text(encoding="utf-8")
    for raw_link in pattern.findall(text):
        candidate = (spec.parent / raw_link).resolve()
        cwd = Path.cwd()
        project_relative = candidate.relative_to(cwd) if str(candidate).startswith(str(cwd)) else candidate
        if not candidate.exists():
            missing.append((spec, raw_link, project_relative))

if missing:
    print("FAILED — missing tests referenced by specs.\n")
    current_spec = None
    for spec, raw_link, resolved in missing:
        if spec != current_spec:
            print(f"--- {spec}")
            current_spec = spec
        print(f"  MISSING {raw_link} -> {resolved}")
    print("\nA missing [@test] is worse than a failing test: the requirement is not verifiable.")
    sys.exit(1)

print("check-spec-links: PASSED")
PY
