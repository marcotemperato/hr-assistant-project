---
name: spec-verify
description: "Runs all spec consistency checks (link integrity, target ownership, manifest build) and the test suite, then reports results. Trigger — verify specs, spec check, run spec suite, check spec consistency, validate spec links, spec integrity."
---

# Spec Verify

Run the full spec verification suite in this order. The only exception to running all steps: if Step 1 fails, stop and report — do not run Steps 2–4.

## Step 1 — Check spec test links

Run:

```bash
bash scripts/check-spec-links.sh
```

This checks that every `[@test]` annotation in every `.spec.md` points to a file that actually exists on disk.

If `scripts/check-spec-links.sh` is missing or cannot run, do not give up — reproduce the check directly: read every `specs/**/*.spec.md`, extract each `[@test]` path, resolve it **relative to the spec file**, and test whether that file exists. The result is the same; the script is just a convenience.

- **Exits zero** (all links resolve) → continue to Step 2.
- **Exits non-zero** (broken links found) → stop here, skip Steps 2–4. For each failing annotation report: the spec file that contains it, the `[@test]` path that does not exist, and why this is critical (no verifier = worse than a failing test). Tell the user to fix it by either creating the missing file at the expected path or correcting the `[@test]` annotation in the spec to point to an existing file, then re-run spec-verify. Record all of this in the report file described under **Reporting** — do not leave the findings only in chat.

## Step 2 — Check target ownership

Run:

```bash
bash scripts/check-target-ownership.sh
```

This checks that no file declared as a `targets` in a spec has been modified without a corresponding update to its owning spec.

## Step 3 — Build spec manifest

Run:

```bash
python3 scripts/build-spec-manifest.py
```

This writes `.spec-source-manifest.json` — a machine-readable map of specs → requirements → targets → tests.

## Step 4 — Run the test suite

Run the project test suite. Detect the test runner automatically:

- If `pytest.ini`, `pyproject.toml`, or `setup.cfg` exists → `pytest tests/ -v`
- If `package.json` with a `test` script exists → `npm test`
- If `Cargo.toml` exists → `cargo test`
- If unsure, ask the user which command to run before proceeding.

## Reporting

After completing the run (whether it finished all four steps or stopped early at Step 1), **always** produce this summary with actual results filled in — write it to `.spec-verify-report.md` in the project root **and** print it to chat. The on-disk report is the durable, CI-uploadable record; the chat copy is the in-session view. A check that was skipped because an earlier one failed is reported as `SKIPPED (Step 1 failed)`, never as PASSED.

```
spec-verify results
───────────────────
check-spec-links:       PASSED / FAILED / SKIPPED
check-target-ownership: PASSED / FAILED / SKIPPED
build-spec-manifest:    PASSED / FAILED / SKIPPED
test suite:             PASSED / FAILED / SKIPPED (N tests)

Overall: PASSED / FAILED
```

When a check FAILED, append a **Findings** section to the report naming exactly what broke. For a `check-spec-links` failure this means, for each broken annotation: the spec file (e.g. `specs/auth.spec.md`), the missing `[@test]` path (e.g. `tests/auth/test_login.py`), the impact (a missing `[@test]` leaves the requirement with no verifier — worse than a failing test), and the fix (create the missing file, or correct the `[@test]` path in the spec). Then re-run spec-verify.

When all four steps pass, the last line must read exactly: `Overall: PASSED`

If anything failed: stop. Do not proceed to the next task, do not declare implementation complete, do not say "you can now merge". The only valid next action is fixing what failed and re-running spec-verify.
