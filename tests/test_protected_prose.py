"""Quotes and code examples must not become instructions to rewrite evidence."""
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import detect

# Catalogue §69, verbatim. Repetition supplies enough prose for the guard tier.
SLOP = ("Unlock the full potential of your team and stay ahead of the curve by "
        "embracing a holistic approach that turns challenges into opportunities.")


@pytest.mark.parametrize("mark", ["> ", "   > ", ">> "])
def test_explicit_quote_does_not_depend_on_line_wrapping(mark):
    words = SLOP.split()
    note = "The client sent this on Monday.\nWe answered it the same day.\n"
    one = note + mark + SLOP
    wrapped = note + mark + " ".join(words[:13]) + "\n" + mark + " ".join(words[13:])
    assert detect.scan(one)["_metrics"]["ai_tell_score"] == detect.scan(wrapped)["_metrics"]["ai_tell_score"]
    assert "69_canonical_slop" not in detect.scan(one)
    assert "69_canonical_slop" in detect.scan(SLOP)
    assert "69_canonical_slop" in detect.scan(one + "\n" + SLOP)
    assert detect.strip_quoted_spans(one).strip() == note.strip()
    assert detect.strip_quoted_spans(mark + SLOP + "\n" + SLOP).strip() == SLOP


@pytest.mark.parametrize("sep", ["\n", "\n\n"])
def test_a_document_written_as_blockquotes_is_still_scored(sep):
    whole = sep.join("> " + s for s in [SLOP] * 6)
    assert "69_canonical_slop" in detect.scan(whole)
    assert detect.strip_quoted_spans(whole) == whole


# Actual U+200B, U+00A0, and Cyrillic 'a', plus significant literal whitespace.
LITERAL = 'value = "a\u200bb\u00a0p\u0430per"  \t'
CODE = [
    "`" + LITERAL + "`",
    "```python\n" + LITERAL + "\n```",
    "~~~~\n" + LITERAL + "\n~~~~~",
    "````markdown\n```\n" + LITERAL + "\n```\n````",
    "    " + LITERAL + "\n    \n    next = 2  ",
    "```python\n" + LITERAL + "\n\n",  # Unclosed fence through EOF.
]


@pytest.mark.parametrize("code", CODE, ids=["inline", "fenced", "tilde", "nested", "indented", "unclosed"])
def test_clean_preserves_code_and_still_scrubs_adjacent_prose(code):
    before = "The p\u0430per\u200b is\u00a0ready.  \n\n" + code
    expected = "The paper is ready.\n\n" + code
    assert detect.clean_text(before) == expected
    assert detect.clean_text(expected) == expected
    metrics = detect.scan(before)["_metrics"]
    assert metrics["invisible_chars"] == 1
    assert metrics["nonstandard_spaces"] == 1
    assert metrics["homoglyphs"] == 1
    after = detect.scan(expected)
    for rule in ("62_invisible_chars", "66_homoglyphs", "67_nonstandard_spaces", "68_trailing_whitespace"):
        assert rule not in after


def test_protection_tokens_do_not_collide_with_prose_or_code():
    text = '|SLOPTRIMCODE0END| |SLOPTRIMCODEX1END| `|SLOPTRIMCODE0END| a\u200bb`'
    assert detect.clean_text(text) == text


def test_code_markers_do_not_make_neighboring_scripts_look_mixed():
    for text in ("ра`x`ра", "ρα`x`ρα", "left`x`right", "שלום`x`שלום"):
        assert detect.clean_text(text) == text
        assert "66_homoglyphs" not in detect.scan(text)


@pytest.mark.parametrize("newline", ["\n", "\r\n"], ids=["lf", "crlf"])
def test_cli_round_trips_protected_code_bytes(tmp_path, newline):
    for code in CODE:
        source = code.replace("\n", newline).encode("utf-8")
        path = tmp_path / "example.md"
        path.write_bytes(source)
        out = subprocess.run([sys.executable, str(ROOT / "scripts/detect.py"), "--clean", str(path)],
                             capture_output=True, timeout=8)
        assert out.returncode == 0, out.stderr
        assert out.stdout == source
        scan = subprocess.run([sys.executable, str(ROOT / "scripts/detect.py"), str(path)],
                              capture_output=True, timeout=8)
        assert scan.returncode == 0, scan.stderr
        assert json.loads(scan.stdout)["_metrics"]["invisible_chars"] == 0


def test_plain_prose_characters_remain_actionable():
    text = "The p\u0430per\u200b is\u00a0ready.  \n"
    assert detect.clean_text(text) == "The paper is ready."
    result = detect.scan(text)
    for rule in ("62_invisible_chars", "66_homoglyphs", "67_nonstandard_spaces", "68_trailing_whitespace"):
        assert rule in result
