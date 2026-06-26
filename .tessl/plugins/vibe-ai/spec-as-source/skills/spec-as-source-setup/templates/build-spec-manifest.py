from pathlib import Path
import json
import re

ROOT = Path.cwd()
SPEC_ROOT = ROOT / "specs"
REQ_PATTERN = re.compile(r"^#{2,3}\s+(REQ-[A-Z0-9-]+)", re.MULTILINE)
TEST_PATTERN = re.compile(r"\[@test\]\s+([^\s`)]+)")


def parse_targets(spec: Path):
    text = spec.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return []

    parts = text.split("---", 2)
    if len(parts) < 3:
        return []

    frontmatter = parts[1].splitlines()
    targets = []
    in_targets = False

    for line in frontmatter:
        stripped = line.strip()
        if stripped.startswith("targets:"):
            in_targets = True
            continue
        if in_targets:
            if stripped.startswith("-"):
                raw = stripped[1:].strip().strip('"\'')
                resolved = (spec.parent / raw).resolve()
                try:
                    targets.append(str(resolved.relative_to(ROOT)))
                except ValueError:
                    targets.append(raw)
            elif stripped and not line.startswith(" "):
                in_targets = False

    return targets


def parse_requirements(spec: Path):
    text = spec.read_text(encoding="utf-8")
    req_matches = list(REQ_PATTERN.finditer(text))
    requirements = {}

    for idx, match in enumerate(req_matches):
        req_id = match.group(1)
        start = match.end()
        end = req_matches[idx + 1].start() if idx + 1 < len(req_matches) else len(text)
        block = text[start:end]
        tests = []
        for raw in TEST_PATTERN.findall(block):
            resolved = (spec.parent / raw).resolve()
            try:
                tests.append(str(resolved.relative_to(ROOT)))
            except ValueError:
                tests.append(raw)
        requirements[req_id] = {"tests": tests}

    return requirements


manifest = {}
for spec in sorted(SPEC_ROOT.glob("**/*.spec.md")):
    manifest[str(spec.relative_to(ROOT))] = {
        "targets": parse_targets(spec),
        "requirements": parse_requirements(spec),
    }

output = ROOT / ".spec-source-manifest.json"
output.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"spec manifest written to {output.relative_to(ROOT)}")
