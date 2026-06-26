---
name: spec-ci-sync
description: "Syncs .github/workflows/spec-verification.yml with the test runner and test files declared in specs. Trigger — update CI workflow, sync spec CI, regenerate workflow, CI out of sync with specs, add spec test to CI."
---

# Spec CI Sync

Regenerate `.github/workflows/spec-verification.yml` so it runs **exactly the test files the specs declare**, guarded by the three spec-consistency checks. Run after adding a spec or changing the stack.

The workflow must end up with four things right. Treat them as a checklist:

1. the correct **test runner**, detected from the project;
2. a test step that lists the **exact spec-declared test files** (never a bare directory glob);
3. the **three spec-check steps** (`check-spec-links`, `check-target-ownership`, `build-spec-manifest`);
4. a **diff shown and confirmed** before the file is written.

## Step 1 — Detect the test runner

First match wins: `pytest.ini` / `setup.cfg` / `pyproject.toml [tool.pytest]` → **pytest**; `package.json` test script → **npm** (jest/vitest if in devDependencies); `Cargo.toml` → **cargo**; `go.mod` → **go**. No match → ask the user.

## Step 2 — Read the manifest and collect the exact test files

Read `.spec-source-manifest.json` (run `python3 scripts/build-spec-manifest.py` first if missing) and collect every unique path under `requirements[*].tests`:

```bash
python3 -c "import json,itertools; m=json.load(open('.spec-source-manifest.json')); print('\n'.join(sorted({t for s in m.values() for r in s['requirements'].values() for t in r['tests']})))"
```

If the manifest has no requirements, fall back to `grep -rhoE '\[@test\] [^ ]+' specs/ | sed 's/\[@test\] //'`. These exact paths go into the test command in Step 3 — do not substitute a directory glob.

## Step 3 — Build the workflow

```yaml
name: Spec Verification
on:
  push: { branches: [main] }
  pull_request: { branches: [main] }
jobs:
  verify-specs:
    name: Run spec verification
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      <SETUP_AND_INSTALL>
      - name: Check [@test] links resolve
        run: bash scripts/check-spec-links.sh
      - name: Check target ownership
        run: bash scripts/check-target-ownership.sh
      - name: Build spec manifest
        run: python3 scripts/build-spec-manifest.py
      - name: Run spec-linked tests
        run: <TEST_CMD>
```

| Runner | `<SETUP_AND_INSTALL>` | `<TEST_CMD>` |
|---|---|---|
| pytest | `- uses: actions/setup-python@v5`<br>`        with: { python-version: "3.11" }`<br>`      - run: pip install -r requirements.txt` | `pytest <the exact files from Step 2> -v --tb=short` |
| npm/jest/vitest | `- uses: actions/setup-node@v4`<br>`        with: { node-version: "20" }`<br>`      - run: npm ci` | `npm test` |
| cargo | *(omit the line)* | `cargo test` |
| go | *(omit the line)* | `go test ./...` |

For pytest, the test command must name every file from Step 2 (space- or `\`-separated), e.g. `pytest tests/auth/test_login.py tests/auth/test_rate_limit.py -v --tb=short`. Keep the three spec-check steps exactly as shown. Add steps only for the detected runner — never for runners the project does not use.

## Step 4 — Diff, confirm, write

Always show the diff first, in a fenced ` ```diff ` block, so the change is reviewable before anything is written — full content as a `+` diff for a new file; changed lines only for an existing one. Then ask: **"Update the workflow? (yes/no)"** and write the file only after an explicit "yes". If it is already in sync, say so and do not overwrite. Showing the diff is unconditional; only the write waits on confirmation.

## Step 5 — Report

Report the runner detected, how many test files came from how many specs, and whether the workflow was written / updated / unchanged. Then: "Next step: commit and push to trigger CI."
