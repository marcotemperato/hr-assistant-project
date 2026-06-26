# spec-as-source-enforcement

## Implementation completeness

An implementation is not complete until every file referenced by a `[@test]` annotation in the specs exists on disk.

Before declaring work done:

1. Read every `.spec.md` in `specs/`.
2. Extract all `[@test]` paths.
3. Verify each file exists.
4. If any file is missing, create it or explicitly report the blocker.
5. Only when all files exist, proceed to work-review.

A missing `[@test]` is worse than a failing test: it is a requirement with no verification.

---

## Target ownership

The `targets` field in a spec's frontmatter declares ownership: that spec is the authoritative source for those files.

Rules:

1. Every significant behaviour must be described in a spec.
2. Every requirement must have a stable ID (format: `REQ-<AREA>-<NNN>`).
3. Every requirement must have at least one `[@test]`.
4. Every spec must declare its `targets`.
5. Modifying a target file requires modifying its owning spec in the same commit or PR.
6. Generated target files must include a header: `# GENERATED FROM SPEC: <spec path>`.
7. If spec, targets, and tests diverge, the CI must fail.

Do not add requirements not present in the spec.
Do not declare work complete if tests are missing, targets are outdated, or requirements are unverifiable.
