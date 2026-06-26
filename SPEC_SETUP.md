# Spec-as-Source Setup

Setup complete. Two remaining manual steps:

1. Enable pre-commit locally:
   ```bash
   pip install pre-commit && pre-commit install
   ```

2. On GitHub → Settings → Branches → Add rule for "main":
   - ✓ Require status checks to pass before merging
   - ✓ Require branches to be up to date before merging
   - ✓ Status check: "Run spec verification"

## Detected stack

- **Test runner:** pytest (via Poetry)
- **CI workflow:** `.github/workflows/spec-verification.yml`

If this project uses a different runner, ask the agent to run `spec-ci-sync`.

## Windows note

Shell scripts use `python3` with fallback to `python`. Run them via Git Bash:
`"C:\Program Files\Git\bin\bash.exe" scripts/verify.sh`

## Files created

```
scripts/check-spec-links.sh
scripts/check-target-ownership.sh
scripts/build-spec-manifest.py
scripts/verify.sh
.pre-commit-config.yaml
.github/workflows/spec-verification.yml
```

## Next steps

1. Create specs in `specs/*.spec.md` using spec-driven development.
2. Run `bash scripts/verify.sh` or ask the agent to use `spec-verify` after each implementation cycle.
