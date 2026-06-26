---
name: spec-as-source-setup
description: "Installs spec-as-source enforcement scripts, CI workflow, and pre-commit hooks into a project. Trigger — setup spec enforcement, add spec checks, configure spec-as-source, install spec scripts, add spec CI."
---

# Spec-as-Source Setup

Set up mechanical spec-as-source enforcement on top of `tessl-labs/spec-driven-development`.
Execute every step in order. Create each file by copying the corresponding template from this skill's `templates/` directory verbatim, unless a step says to adapt something.

**Prerequisites**: `tessl init` and `tessl install tessl-labs/spec-driven-development` already done. Git repo initialized.

---

## Step 1 — Create `scripts/check-spec-links.sh`

Create the `scripts/` directory if it does not exist.
Copy `templates/check-spec-links.sh` to `scripts/check-spec-links.sh`, then make it executable:

```bash
chmod +x scripts/check-spec-links.sh
```

**What it does**: verifies that every `[@test]` annotation in every `.spec.md` points to a file that actually exists on disk. A missing test file is worse than a failing test: the requirement has no verifier.

---

## Step 2 — Create `scripts/check-target-ownership.sh`

Copy `templates/check-target-ownership.sh` to `scripts/check-target-ownership.sh`, then make it executable:

```bash
chmod +x scripts/check-target-ownership.sh
```

**What it does**: detects whether any file declared as a `targets` entry in a spec has been modified without a corresponding update to its owning spec. This is the core spec-as-source guard.

---

## Step 3 — Create `scripts/build-spec-manifest.py`

Copy `templates/build-spec-manifest.py` to `scripts/build-spec-manifest.py`. No chmod needed — it is a Python script called directly.

**What it does**: reads all `specs/*.spec.md` files and writes `.spec-source-manifest.json` — a machine-readable map of specs → requirements → targets → tests.

---

## Step 4 — Create `scripts/verify.sh`

Copy `templates/verify.sh` to `scripts/verify.sh`.

**What it does**: orchestrates steps 1–3 in sequence, then auto-detects and runs the project test suite (pytest / npm test / cargo test).

Now make every shell script executable in one step and **verify the bits actually stuck** — the executable bit is a separate operation that file-write tools do not set, so a freshly written `.sh` is `644` until you `chmod` it:

```bash
chmod +x scripts/check-spec-links.sh scripts/check-target-ownership.sh scripts/verify.sh
ls -l scripts/
```

Every `.sh` in the listing must show `x` in its permissions (e.g. `-rwxr-xr-x`). If any does not, re-run the `chmod`. Without the executable bit the scripts are useless to pre-commit and CI. (`build-spec-manifest.py` needs no `+x` — it is called as `python3 scripts/build-spec-manifest.py`.)

---

## Step 5 — Create `.pre-commit-config.yaml`

Copy `templates/pre-commit-config.yaml` to `.pre-commit-config.yaml` in the project root. No adaptation needed.

---

## Step 6 — Create `.github/workflows/spec-verification.yml`

Create `.github/workflows/` if it does not exist.
Copy `templates/spec-verification.yml` to `.github/workflows/spec-verification.yml`.

**Auto-detect the test runner — do not block the rest of setup waiting for an answer.** The CI file must exist on disk before you move on. First match wins:

- `pytest.ini` / `setup.cfg` / `pyproject.toml [tool.pytest]` → **pytest**
- `package.json` with a `test` script → **npm** (jest/vitest if in devDependencies)
- `Cargo.toml` → **cargo**
- `go.mod` → **go**
- no match → default to **pytest** and flag it in the confirmation below

Then **replace** the `# ADAPT: install and run tests here` placeholder with the install + test steps for the detected runner (never leave the placeholder in the final file):

| Runner | steps to insert |
|---|---|
| pytest | `- uses: actions/setup-python@v5`<br>`        with: { python-version: "3.11" }`<br>`      - run: pip install -r requirements.txt`<br>`      - run: pytest -v` |
| npm | `- uses: actions/setup-node@v4`<br>`        with: { node-version: "20" }`<br>`      - run: npm ci`<br>`      - run: npm test` |
| cargo | `- run: cargo test` |
| go | `- run: go test ./...` |

After writing the file, surface the runner as a **non-blocking confirmation** (state it, then keep going — do not wait):

> "I detected **<runner>** and configured the CI workflow accordingly. If this project uses a different runner, tell me and I'll re-sync it with spec-ci-sync."

Continue to Step 7 immediately.

---

## Step 7 — Post-setup checklist

After creating all six files, write this checklist to `SPEC_SETUP.md` in the project root **and** print it verbatim, so the user has both a durable record and the in-session reminder:

```
Setup complete. Two remaining manual steps:

1. Enable pre-commit locally:
   pip install pre-commit && pre-commit install

2. On GitHub → Settings → Branches → Add rule for "main":
   ✓ Require status checks to pass before merging
   ✓ Require branches to be up to date before merging
   ✓ Status check: "Run spec verification"
```

## Step 8 — Verify the install

Run verification automatically by invoking **spec-verify** (it runs the three spec checks plus the test suite and writes `.spec-verify-report.md`). This both proves the freshly installed scripts work and leaves a baseline report. Do not end the setup before this runs.
