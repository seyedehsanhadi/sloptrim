#!/usr/bin/env python3
"""test_skill.py: validate SKILL.md frontmatter and structure."""

from __future__ import annotations
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("FAIL: PyYAML is required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

REPO = Path(__file__).resolve().parent.parent
SKILL = REPO / "SKILL.md"
PATTERNS = REPO / "references" / "patterns.md"
DETECT = REPO / "scripts" / "detect.py"


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def ok(msg: str) -> None:
    print(f"PASS  {msg}")


def main() -> int:
    if not SKILL.exists():
        fail(f"{SKILL} does not exist")
    if not PATTERNS.exists():
        fail(f"{PATTERNS} does not exist")
    if not DETECT.exists():
        fail(f"{DETECT} does not exist")

    skill_text = SKILL.read_text(encoding="utf-8")
    fm_match = re.match(r"^---\n(.*?)\n---\n", skill_text, re.DOTALL)
    if not fm_match:
        fail("SKILL.md is missing YAML frontmatter delimiters")
    try:
        fm = yaml.safe_load(fm_match.group(1))
    except yaml.YAMLError as e:
        fail(f"SKILL.md frontmatter does not parse as YAML: {e}")
    ok("YAML frontmatter parses")

    for field in ("name", "description"):
        if field not in fm:
            fail(f"required field '{field}' missing from frontmatter")
    ok("required fields (name, description) present")

    if not re.match(r"^[a-z][a-z0-9-]*[a-z0-9]$", fm["name"]):
        fail(f"name {fm['name']!r} is not valid kebab-case")
    ok(f"name '{fm['name']}' is valid kebab-case")

    if "<" in fm["description"] or ">" in fm["description"]:
        fail("description contains < or > characters which break frontmatter parsing")
    ok("description has no XML brackets")

    desc = fm["description"].lower()
    triggers = [
        "humanize", "de-ai", "de-slop", "ai tells",
        "robotic", "chatgpt", "natural", "sound human",
    ]
    hits = [t for t in triggers if t in desc]
    if len(hits) < 6:
        fail(f"description has only {len(hits)}/{len(triggers)} trigger keywords: likely to miss auto-activation")
    ok(f"description has {len(hits)}/{len(triggers)} trigger keywords")

    at = fm.get("allowed-tools")
    if at is not None and not isinstance(at, str):
        fail(f"allowed-tools should be a comma-separated string, got {type(at).__name__}")
    if isinstance(at, str):
        tools = [t.strip() for t in at.split(",") if t.strip()]
        if not tools:
            fail("allowed-tools is empty after split")
        ok(f"allowed-tools is a {len(tools)}-tool comma-separated string")

    if "version" not in fm:
        fail("version field missing")
    if not isinstance(fm["version"], str):
        fail(f"version should be a string, got {type(fm['version']).__name__}")
    ok(f"version field present: {fm['version']!r}")

    if REPO.name == fm["name"]:
        ok(f"directory name matches the 'name' field ({fm['name']})")
    else:
        print(f"WARN: directory '{REPO.name}' does not match name '{fm['name']}'. "
              "This is fine if the skill is symlinked or you renamed the parent.")

    skill_body = re.sub(r"^---\n.*?\n---\n", "", skill_text, flags=re.S)
    skill_nums = set(int(m.group(1)) for m in re.finditer(r"^\s*(\d+)\.\s+\S", skill_body, re.M))

    patterns_text = PATTERNS.read_text(encoding="utf-8")
    patterns_nums = set(int(m.group(1)) for m in re.finditer(r"^### (\d+)\.\s+", patterns_text, re.M))

    missing_in_patterns = skill_nums - patterns_nums
    if missing_in_patterns:
        fail(f"SKILL.md indexes patterns not in references/patterns.md: {sorted(missing_in_patterns)}")
    ok(f"all {len(skill_nums)} pattern indices in SKILL.md cross-reference patterns.md")

    body_words = len(skill_body.split())
    rough_tokens = int(body_words * 1.33)
    if rough_tokens > 3000:
        print(f"WARN: SKILL.md body is ~{rough_tokens} tokens. Consider moving more detail to references/.")
    else:
        ok(f"SKILL.md body size is ~{rough_tokens} tokens (under 3 K target)")

    EXPECTED_PATTERN_COUNT = 71
    if len(patterns_nums) != EXPECTED_PATTERN_COUNT:
        fail(f"references/patterns.md has {len(patterns_nums)} patterns, expected {EXPECTED_PATTERN_COUNT}")
    ok(f"references/patterns.md has {EXPECTED_PATTERN_COUNT} patterns")

    plugin_copy = REPO / "skills" / "sloptrim" / "SKILL.md"
    if plugin_copy.exists():
        if plugin_copy.read_text(encoding="utf-8") != skill_text:
            fail("skills/sloptrim/SKILL.md has drifted from root SKILL.md: "
                 "run: cp SKILL.md skills/sloptrim/SKILL.md")
        ok("plugin skill copy matches root SKILL.md")

    detect_text = DETECT.read_text(encoding="utf-8")
    if not detect_text.startswith("#!"):
        print("WARN: scripts/detect.py is missing a shebang line")

    if "def main" not in detect_text:
        fail("scripts/detect.py is missing a main() function")
    ok("scripts/detect.py looks runnable")

    command = REPO / "install" / "sloptrim-command.md"
    if not command.exists():
        fail(f"{command} does not exist: the clone install has no way to add /sloptrim to the / menu")
    command_text = command.read_text(encoding="utf-8")
    cmd_fm = re.match(r"^---\n(.*?)\n---\n(.*)$", command_text, re.DOTALL)
    if not cmd_fm:
        fail("install/sloptrim-command.md is missing YAML frontmatter delimiters")
    try:
        cmd_meta = yaml.safe_load(cmd_fm.group(1))
    except yaml.YAMLError as e:
        fail(f"install/sloptrim-command.md frontmatter does not parse as YAML: {e}")
    if not cmd_meta.get("description"):
        fail("install/sloptrim-command.md is missing a description field")
    cmd_body = cmd_fm.group(2).strip()
    if not cmd_body.startswith("/sloptrim"):
        fail("install/sloptrim-command.md body does not start with /sloptrim")
    if "$ARGUMENTS" not in cmd_body:
        fail("install/sloptrim-command.md body does not forward $ARGUMENTS to the router")
    ok("install/sloptrim-command.md registers the / menu entry and forwards args to the router")

    print()
    print("All compliance checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())


def test_skill_structure():
    assert main() == 0
