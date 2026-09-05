"""Save-path, extraction and character regressions found in the 0.9.2 review."""
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import detect

SLOP = ("Great question! In today's fast-paced world, our comprehensive guide serves "
        "as a testament to the transformative power of leveraging cutting-edge solutions. "
        "It's not just about tools; it's about unlocking unprecedented value. It is worth "
        "noting that experts argue this journey is just beginning, paving the way for a "
        "brighter future. In conclusion, the future looks bright. I hope this helps!")


def hook(name, payload, folder, root=ROOT):
    return subprocess.run(
        ["node", str(ROOT / "hooks" / name)], input=json.dumps(payload),
        capture_output=True, text=True, encoding="utf-8", timeout=25, cwd=ROOT,
        env={**os.environ, "CLAUDE_PLUGIN_ROOT": str(root), "CLAUDE_CONFIG_DIR": str(folder)})


@pytest.mark.parametrize("text", ["\U000e0061" * 8000 + "a", " " * 32000 + "a"],
                         ids=["tags", "whitespace"])
def test_pathological_runs_fit_the_guard_budget(text):
    for args in ([], ["--clean"]):
        r = subprocess.run([sys.executable, str(ROOT / "scripts/detect.py")] + args,
                           input=text.encode("utf-8"), capture_output=True, timeout=8)
        assert r.returncode == 0, r.stderr
        if args:
            assert r.stdout.decode("utf-8") == detect.clean_text(text)


def test_flag_terminator_does_not_protect_a_trailing_payload():
    flag = "\U0001f3f4\U000e0067\U000e0062\U000e0065\U000e006e\U000e0067\U000e007f"
    text = flag + "\U000e0061" * 8000
    assert detect.clean_text(text) == flag
    assert detect.detect_invisible_chars(text)["count"] == 8000


def test_homoglyph_detection_matches_preservation_and_the_scan_window():
    native = "Pay СберBank today."
    assert detect.clean_text(native) == native
    assert "66_homoglyphs" not in detect.scan(native)
    prefix = ("word " * 52429)[:detect._SCAN_CAP]
    assert "66_homoglyphs" not in detect.scan(prefix + " pаper")
    assert "66_homoglyphs" in detect.scan("The pаper is ready.")


@pytest.mark.parametrize("opening,closing", [("````markdown", "````"), ("~~~~", "~~~~~")])
def test_long_fences_keep_nested_examples_out_of_prose(opening, closing):
    text = opening + "\n```\n" + SLOP + "\n```\n~~~\n" + closing + "\nReal prose."
    assert "1_ai_vocabulary" not in detect.scan(text)
    assert detect.strip_code(text).strip() == "Real prose."
    assert "1_ai_vocabulary" in detect.scan(text + "\n" + SLOP)


def test_indented_code_does_not_remove_paragraph_continuations():
    text = "    " + SLOP + "\n\n    " + SLOP + "\n\nReal prose."
    assert detect.strip_code(text).strip() == "Real prose."
    continuation = "A paragraph continues\n    on this indented line."
    assert detect.strip_code(continuation) == continuation


@pytest.mark.parametrize("ext", ["xlsx", "xlsm"])
def test_spreadsheets_follow_cell_references_and_preserve_boundaries(tmp_path, ext):
    p = tmp_path / ("book." + ext)
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("xl/sharedStrings.xml", '<sst><si><t>UNUSED</t></si><si><t>First</t></si>'
                   '<si><r><t>Sec</t></r><r><t>ond</t></r></si></sst>')
        z.writestr("xl/worksheets/sheet1.xml", '<worksheet><sheetData>'
                   '<row><c t="s"><v>2</v></c><c t="s"><v>1</v></c></row>'
                   '<row><c t="inlineStr"><is><t>Third</t></is></c>'
                   '<c t="s"><v>2</v></c><c t="str"><f>formula</f><v>Fourth</v></c>'
                   '<c><v>42</v></c><c t="s"><v>-1</v></c><c t="s"><v>999</v></c>'
                   '<c t="s"><v>bad</v></c></row></sheetData></worksheet>')
    assert detect.read_input([str(p)]) == "Second\nFirst\nThird\nSecond\nFourth"


@pytest.mark.parametrize("ext", ["odt", "odp", "ods"])
def test_opendocument_keeps_inline_text_and_whitespace(tmp_path, ext):
    p = tmp_path / ("linked." + ext)
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("content.xml", '<doc xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0">'
                   '<text:p>Keep <text:a>linked <text:span>words</text:span></text:a> here.</text:p>'
                   '<text:p>two<text:s text:c="2"/>words<text:tab/>tab<text:line-break/>line.</text:p></doc>')
    assert detect.read_input([str(p)]) == "Keep linked words here.\ntwo  words\ttab\nline."


@pytest.mark.parametrize("obj", [[], {"cells": None}, {"cells": [None]},
    {"cells": [{"cell_type": "markdown", "source": [1]}]},
    {"cells": [{"cell_type": "markdown", "source": None}]}])
def test_malformed_notebook_has_a_clean_cli_error(tmp_path, obj):
    p = tmp_path / "bad.ipynb"
    p.write_text(json.dumps(obj), encoding="utf-8")
    r = subprocess.run([sys.executable, str(ROOT / "scripts/detect.py"), str(p)],
                       capture_output=True, text=True, timeout=8)
    assert r.returncode == 1
    assert json.loads(r.stderr) == {"error": "empty input"}


def test_relative_patch_paths_use_the_payload_working_directory(tmp_path):
    (tmp_path / "draft.md").write_text(SLOP, encoding="utf-8")
    for ti in ({"file_path": "draft.md"},
               {"command": "*** Begin Patch\n*** Update File: draft.md\n@@\n-old\n+new\n*** End Patch"}):
        r = hook("sloptrim-guard.js", {"cwd": str(tmp_path), "tool_input": ti}, tmp_path)
        assert "draft.md" in json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"]


@pytest.mark.parametrize("script,reason", [
    ("print('not a report')", "invalid detector report"),
    ("print('null')", "invalid detector score"),
    ("raise SystemExit(1)", "detector could not read or score this file"),
    ("import time; time.sleep(9)", "detector timed out"),
])
def test_failed_detection_is_visible_in_the_session_ledger(tmp_path, script, reason):
    (tmp_path / "draft.md").write_text(SLOP, encoding="utf-8")
    # The fake install must not contain the deliverable, which is exempt inside a plugin.
    fake = tmp_path / "install"
    (fake / "scripts").mkdir(parents=True)
    (fake / "scripts/detect.py").write_text(script, encoding="utf-8")
    r = hook("sloptrim-guard.js", {"session_id": "failed", "tool_input": {
        "file_path": str(tmp_path / "draft.md")}}, tmp_path, root=fake)
    assert r.returncode == 0 and not r.stdout
    r = hook("sloptrim-tracker.js", {"session_id": "failed", "prompt": "/sloptrim show"}, tmp_path)
    assert "not scored: " + reason in json.loads(r.stdout)["reason"]


def test_init_while_off_writes_nothing(tmp_path):
    (tmp_path / ".sloptrim-active").write_text("off", encoding="utf-8")
    r = subprocess.run(["node", str(ROOT / "hooks/sloptrim-tracker.js")],
                       input='{"prompt":"/sloptrim init"}', cwd=tmp_path,
                       capture_output=True, text=True, timeout=8,
                       env={**os.environ, "CLAUDE_CONFIG_DIR": str(tmp_path), "CLAUDE_PLUGIN_ROOT": str(ROOT)})
    assert "No files written" in json.loads(r.stdout)["reason"]
    assert not (tmp_path / "AGENTS.md").exists()
    assert not (tmp_path / ".cursor").exists()
