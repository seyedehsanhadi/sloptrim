"""test_catalogue.py: the pattern catalogue must survive its own detector, in both directions."""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

import detect

PATTERNS_MD = REPO / "references" / "patterns.md"
STRUCTURAL = ("56_", "60_", "40_", "55_", "44_", "61_", "46_", "33_", "34_")

EXTRACTION_IMMUNE = {
    70: "needs 25+ lines and 3+ standalone rules; no one-line example can carry it",
    41: "needs a long document (cadence statistic)",
    44: "needs 4+ paragraphs (paragraph-length CV)",
    46: "document-level statistic (semicolon underuse)",
    34: "bullets span lines; single-example extraction cannot carry the block",
    35: "needs heading + echo line pair",
    59: "needs a markdown heading line",
    66: "homoglyph codepoints do not survive the catalogue file",
    67: "non-standard spaces do not survive the catalogue file",
    68: "trailing whitespace is stripped by extraction",
}


def _sections() -> dict:
    text = PATTERNS_MD.read_text(encoding="utf-8")
    parts = re.split(r"^### (\d+)\.\s+[^\n]*$", text, flags=re.M)
    return {int(parts[i]): parts[i + 1] for i in range(1, len(parts), 2)}


def _befores(body: str) -> list:
    return [m.group(1).strip() for m in
            re.finditer(r"^\*\*Before[^:]*:\*\*\s*(.*(?:\n(?!\*\*|###).*)*)", body, re.M)]


def _afters(body: str) -> list:
    return [m.group(1).strip() for m in
            re.finditer(r"^\*\*After[^:]*:\*\*\s*(.+)$", body, re.M)]


def _registry_ids() -> set:
    src = (REPO / "scripts" / "detect.py").read_text(encoding="utf-8")
    return {int(m.group(1)) for m in re.finditer(r'"(\d+)_[a-z_]+"', src)}


def _fired(text: str) -> set:
    return {int(k.split("_")[0]) for k in detect.scan(text) if not k.startswith("_")}


def test_machine_checked_count_is_honest():
    assert len(_registry_ids()) == 62


def test_every_after_example_is_clean():
    dirty = []
    for num, body in _sections().items():
        for a in _afters(body):
            if len(a.split()) < 6:
                continue
            flagged = [k for k in detect.scan(a)
                       if not k.startswith("_") and not k.startswith(STRUCTURAL)]
            if flagged:
                dirty.append((num, flagged, a[:80]))
    assert not dirty, (
        "the catalogue's own After examples still trip the detector:\n"
        + "\n".join(f"  #{n} {f} :: {a}" for n, f, a in dirty)
    )


def test_every_before_example_fires_its_own_pattern():
    registry = _registry_ids()
    silent = []
    for num, body in _sections().items():
        if num not in registry or num in EXTRACTION_IMMUNE:
            continue
        befores = _befores(body)
        if not befores:
            continue
        if not any(num in _fired(b) for b in befores):
            silent.append(num)
    assert not silent, (
        f"patterns {silent} have a detector AND a Before example, but the "
        "detector never fires on it: placebo regex or drifted example"
    )


def test_extraction_immune_detectors_fire():
    cases = {
        41: " ".join(["Short one.", "This is a much longer sentence that "
                      "unwinds carefully across many more words indeed."] * 8),
        44: "\n\n".join(["One sentence here. Another follows it. A third "
                         "rounds the paragraph out nicely today."] * 5),
        34: ("The essay argues three things.\n\n- First point here\n"
             "- Second point here\n- Third point here\n\nProse resumes after "
             "the bullets and continues the argument for a while longer."),
        35: "## Payment Options\n\nWe offer several payment options.\n\n"
            "## Shipping Rules\n\nOur shipping rules are simple.",
        59: "# The Quick Brown Fox Jumps Over The Lazy Dog\n\nBody text "
            "follows with normal prose that runs long enough to scan.",
        66: "The pаyment system works well.",
        67: "The plan works well and the team agrees on it.",
        68: "A line with trailing spaces   \nand another line.\n\n\n",
    }
    dead = {num: sample for num, sample in cases.items()
            if num not in _fired(sample)}
    assert not dead, f"detectors exist but never fire, even on synthetic input: {sorted(dead)}"


def test_befores_and_afters_separate_in_aggregate():
    text = PATTERNS_MD.read_text(encoding="utf-8")
    bdoc = "\n\n".join(re.findall(r"^\*\*Before[^:]*:\*\*\s*(.+)$", text, re.M))
    adoc = "\n\n".join(re.findall(r"^\*\*After[^:]*:\*\*\s*(.+)$", text, re.M))
    b = detect.scan(bdoc)["_metrics"]["ai_tell_score"]
    a = detect.scan(adoc)["_metrics"]["ai_tell_score"]
    assert b >= 55, f"Before-doc scored only {b}: detector too weak on dense slop"
    assert a <= 20, f"After-doc scored {a}: the catalogue's own fixes leave tells"
    assert b - a >= 35, f"separation {b - a} too small (before={b}, after={a})"


def test_catalogue_matches_skill_index():
    cat = set(_sections())
    skill = {int(m.group(1)) for m in
             re.finditer(r"^(\d+)\.\s+\S", (REPO / "SKILL.md").read_text(encoding="utf-8"), re.M)}
    assert cat == skill, (
        f"catalogue and SKILL.md index disagree, only in catalogue: {sorted(cat - skill)}, "
        f"only in SKILL.md: {sorted(skill - cat)}"
    )
