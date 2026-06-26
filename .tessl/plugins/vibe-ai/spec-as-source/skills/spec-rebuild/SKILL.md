---
name: spec-rebuild
description: "Deletes all files declared as targets in specs/*.spec.md and rebuilds them from the specs to verify spec-as-source integrity. Trigger — clean rebuild, verify source of truth, spec drift check, regenerate from specifications, rebuild from spec."
---

# Spec Rebuild

Proves that `.spec.md` files are the real source of truth: deletes the generated code and tests declared as `targets` in specs, rebuilds them from the specs, then runs `spec-verify` to confirm everything passes.

Only files listed under `targets:` in a spec's frontmatter are touched — that list is the ownership contract.

## Step 1 — Safety checks

Run both before touching anything:

```bash
git diff --stat && git diff --cached --stat
ls specs/*.spec.md
```

- Uncommitted changes present → stop: "Commit or stash your changes before rebuilding."
- No `.spec.md` files → stop: "No specs found. Nothing to rebuild from."

## Step 2 — List targets and reject unsafe paths

List every `targets:` path and refuse any that escapes the project or points at a protected directory. Targets may be written relative to the spec file (e.g. `../src/app.py`) or to the project root (e.g. `src/app.py`); both forms are normalised to a project-relative path before checking:

```bash
python3 -c "
import os, re, sys
unsafe, ok = [], []
for f in sorted(os.listdir('specs')):
    if not f.endswith('.spec.md'): continue
    fm = re.search(r'^---\n(.*?)\n---', open(f'specs/{f}').read(), re.DOTALL)
    if not fm: continue
    for t in re.findall(r'^\s*-\s+(\S+)', fm.group(1).split('targets:')[-1], re.M):
        rel = os.path.normpath(os.path.join('specs', t)) if t.startswith('../') else os.path.normpath(t)
        bad = os.path.isabs(t) or t.startswith('~') or rel.startswith('..') or rel.split(os.sep)[0] in ('specs','scripts','.git','.github','.tessl','.tessl-plugin')
        (unsafe if bad else ok).append((rel, f))
if unsafe:
    print('UNSAFE TARGET PATHS — aborting:')
    for r, f in unsafe: print(f'  {r}  <- {f}')
    sys.exit(1)
for r, f in ok: print(f'  {r}  <- {f}')
"
```

If it exits non-zero, **stop** — a spec is declaring a target outside the project or in a protected directory. Do not delete anything.

## Step 3 — Confirm before deleting

Write the validated deletion plan from Step 2 to `.spec-rebuild-plan.md` (each file to be deleted and the spec that owns it) so there is a durable record of exactly what is about to happen, then show that same list to the user and ask, in these words:

> Delete these files and rebuild them from the specs? (yes/no)

Wait for an explicit **yes**. Anything else → stop (the plan file is harmless on its own — nothing has been deleted). Never delete without confirmation.

## Step 4 — Delete the targets

Delete only the validated `targets` paths from Step 2. Never delete `specs/`, `scripts/`, `.github/`, `.git/`, `.tessl/`, `.tessl-plugin/`, or config files.

## Step 5 — Rebuild from specs

For each spec in `specs/` (alphabetical order if several share targets), issue this prompt, substituting the filename:

```
The spec at specs/<filename>.spec.md is approved and is the only source of truth.
Implement all its targets from scratch:
- Create every file listed in `targets:` frontmatter.
- Implement only requirements present in the spec (REQ-* sections). Do not add behaviour not described.
- Add `# GENERATED FROM SPEC: specs/<filename>.spec.md` as the first line of every target source file.
- In every test file that is a target, add `# @spec: specs/<filename>.spec.md` and a `# @req: REQ-XXX` comment above each test function that covers that requirement.
Do not ask clarifying questions — the spec is the specification.
```

## Step 6 — Verify

Run `spec-verify` (check-spec-links → check-target-ownership → build-spec-manifest → test suite).

- All checks pass → report: "Rebuild successful. Specs are the source of truth."
- Any check fails → report which check failed and what is missing, then ask: "Retry the failed spec or stop?"
