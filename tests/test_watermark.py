"""test_watermark.py: what --clean removes, and what it must never touch.

Every vector here comes from a real audit. The `keep` cases are the ones that
were being destroyed: the England flag became a black flag, a Japanese name lost
its variant form, three Cyrillic letters inside a Russian bank name were
rewritten to Latin, French and German typography was flattened, Arabic lost the
marks that order it and Thai lost every line-break opportunity.

The rule the code follows, and that these tests pin, is that a character is
removed only where it has no job. The same codepoint can be debris in English
and load-bearing three words later.
"""
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
DETECT = REPO / "scripts" / "detect.py"


def clean(text, tmp_path):
    p = tmp_path / "doc.md"
    with open(p, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
    r = subprocess.run([sys.executable, str(DETECT), "--clean", str(p)],
                       capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        raise RuntimeError(r.stderr)
    return r.stdout


# Hidden channels that carry no meaning where they sit.
REMOVE = [
    ("zero-width space in English", "The pump​moves 40 litres."),
    ("zero-width non-joiner between Latin letters", "The pum‌p moves."),
    ("zero-width joiner between Latin letters", "The pum‍p moves."),
    ("word joiner", "The pump⁠moves 40 litres."),
    ("byte-order mark mid-text", "The pump﻿moves 40 litres."),
    ("left-to-right mark with no RTL", "The pump‎moves 40 litres."),
    ("tag-block payload", "Totally clean text.\U000e0068\U000e0069"),
    ("tag payload after a cancel", "Report ready.\U000e007f\U000e0041\U000e0042"),
    ("variation selector with no glyph base", "Report ready︀ for review."),
    ("supplementary variation selector, no CJK", "Report\U000e0100 ready."),
    ("homoglyph inside a Latin word", "The pаper is ready."),
    ("no-break space between two words", "The pump moves 40 litres."),
    ("ideographic space in English", "The pump　moves 40 litres."),
    ("interlinear annotation", "The pump￹moves￺40￻ litres."),
]

# Characters doing real work. Destroying any of these is the defect.
KEEP = [
    ("England flag tag sequence",
     "Match in \U0001F3F4\U000E0067\U000E0062\U000E0065\U000E006E\U000E0067\U000E007F today."),
    ("Japanese ideographic variation sequence", "The name 葛\U000E0100飾 here."),
    ("Cyrillic glued to a Latin run", "Pay СберBank today."),
    ("emoji joined family", "We shipped \U0001f468‍\U0001f469‍\U0001f467 today."),
    ("emoji with variation selector 16", "It works ❤️ now."),
    ("keycap sequence", "Press 1️⃣ to continue."),
    ("Persian non-joiner inside a word", "می‌رود به"),
    ("Devanagari joiner", "क्‍ष in Hindi."),
    ("Arabic with bidi marks", "الاسم ‏Ahmed‎ here."),
    ("Thai zero-width word breaks", "สวัสดี​ครับ"),
    ("Mongolian free variation selector", "ᠦ᠋ᠦ text"),
    ("Khmer inherent vowel", "ក឴ខ text"),
    ("no-break space before French punctuation", "Le prix : 40 EUR"),
    ("narrow no-break space in a figure", "It costs 40 EUR today"),
    ("soft hyphen inside a word", "Do­nau­dampf­schiff"),
    ("genuine Cyrillic sentence", "Насос перекачивает."),
    ("genuine Greek sentence", "Η αντλία λειτουργεί."),
    ("combining accents", "André measured the flõw rate."),
]


@pytest.mark.parametrize("name,text", REMOVE, ids=[n for n, _ in REMOVE])
def test_hidden_channel_is_removed(name, text, tmp_path):
    assert clean(text, tmp_path) != text, "%s survived --clean" % name


@pytest.mark.parametrize("name,text", KEEP, ids=[n for n, _ in KEEP])
def test_working_characters_survive(name, text, tmp_path):
    assert clean(text, tmp_path) == text, "%s was altered by --clean" % name


def test_detection_agrees_with_cleaning(tmp_path):
    """A character the scrub keeps must not be reported as a watermark.

    These disagreed once, and every document containing an emoji collected
    points for a variation selector that was doing its job.
    """
    sys.path.insert(0, str(REPO / "scripts"))
    import detect
    for name, text in KEEP:
        m = detect.scan(text)["_metrics"]
        assert m["invisible_chars"] == 0, "%s counted as invisible" % name
        assert m["nonstandard_spaces"] == 0, "%s counted as a stray space" % name


def test_a_file_ending_in_a_newline_still_does(tmp_path):
    text = "The build finished.\nAll tests passed.\n"
    assert clean(text, tmp_path) == text


def test_leading_indentation_survives(tmp_path):
    """Four spaces open a Markdown code block; they are not stray whitespace."""
    text = "    indented code block\nnext line\n"
    assert clean(text, tmp_path) == text


def test_extra_files_are_reported_not_dropped_silently(tmp_path):
    """Two paths used to scan the first and drop the rest without a word. It still
    scans the first, because a shell glob that worked must keep working, but it now
    says on stderr that it did."""
    import json
    a, b = tmp_path / "a.md", tmp_path / "b.md"
    a.write_text("First.\n", encoding="utf-8")
    b.write_text("Second.\n", encoding="utf-8")
    r = subprocess.run([sys.executable, str(DETECT), str(a), str(b)],
                       capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, "a glob that used to work must keep working"
    assert json.loads(r.stdout)["_metrics"]["ai_tell_score"] is not None
    assert "one at a time" in r.stderr, "the dropped file must not be silent"


def test_truncation_is_reported(tmp_path):
    """The scan stops at 256 KB while the guard accepts 512 KB, so anything past the
    cap is unread. The report has to say so rather than look complete."""
    import json
    small = tmp_path / "small.md"
    small.write_text("The lock was rebuilt in 1804.\n", encoding="utf-8")
    r = subprocess.run([sys.executable, str(DETECT), str(small)],
                       capture_output=True, text=True, encoding="utf-8")
    assert json.loads(r.stdout)["_metrics"]["truncated"] is False

    big = tmp_path / "big.md"
    big.write_text("The lock was rebuilt in 1804. " * 12000, encoding="utf-8")
    r = subprocess.run([sys.executable, str(DETECT), str(big)],
                       capture_output=True, text=True, encoding="utf-8")
    m = json.loads(r.stdout)["_metrics"]
    assert m["truncated"] is True
    assert m["scanned_chars"] == 262144
