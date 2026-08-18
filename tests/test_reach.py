"""test_reach.py: the surfaces this tool reaches beyond Claude Code.

Two things are asserted here, both of which drift silently if nobody looks.

The Cursor rule is generated from the activation hook rather than written by
hand, so this file fails if the two ever disagree. A second copy of a ruleset is
a second thing to keep in sync, and the copy is always the one that goes stale.

`/sloptrim init` writes the contract into AGENTS.md, which is how Codex, Cursor,
Jules and several others pick up instructions. That was built and never
documented, so the README claim and the code are pinned to each other.

"""
import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

CURSOR = REPO / ".cursor" / "rules" / "sloptrim.mdc"
LIB = REPO / "hooks" / "sloptrim-lib.js"


def contract_from_hook():
    src = io.open(LIB, encoding="utf-8").read()
    i = src.find("'# Sloptrim',")
    j = src.find("SILENT.", i)
    j = src.find("',", j) + 2
    lines = re.findall(r"^\s*'((?:[^'\\]|\\.)*)',?\s*$", src[i:j], re.M)
    return "\n".join(l.replace("\\'", "'").replace('\\"', '"').replace("\\\\", "\\")
                     for l in lines).strip()


# --------------------------------------------------------------------- cursor
def test_cursor_rule_exists():
    assert CURSOR.exists(), "Cursor users get nothing without this file"


def test_cursor_rule_has_frontmatter():
    t = io.open(CURSOR, encoding="utf-8").read()
    assert t.startswith("---\n"), "Cursor ignores a rule file with no frontmatter"
    assert "globs:" in t.split("---")[1]


def test_cursor_rule_matches_the_hook_contract():
    """The rule is generated. If someone edits one copy, this catches it."""
    body = io.open(CURSOR, encoding="utf-8").read().split("---\n", 2)[2].strip()
    assert body == contract_from_hook(), (
        "the Cursor rule and the activation hook disagree; regenerate with "
        "the generator rather than editing either by hand")


def test_cursor_rule_targets_prose_and_not_code():
    t = io.open(CURSOR, encoding="utf-8").read()
    head = t.split("---")[1]
    for ext in (".md", ".txt", ".rst", ".tex"):
        assert '"**/*%s"' % ext in head
    for ext in (".py", ".js", ".ts", ".json"):
        assert ext not in head, "%s must not be in scope; this never touches code" % ext


# --------------------------------------------------------------------- agents
def test_init_writes_agents_md():
    """The multi-agent path. Codex and others read AGENTS.md."""
    tracker = io.open(REPO / "hooks" / "sloptrim-tracker.js", encoding="utf-8").read()
    assert "AGENTS.md" in tracker


def test_readme_tells_people_the_multi_agent_path_exists():
    r = io.open(REPO / "README.md", encoding="utf-8").read()
    assert "AGENTS.md" in r, (
        "init writes AGENTS.md and the README never says so, which hides "
        "every agent that is not Claude Code")
