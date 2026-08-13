"""test_coverage.py: every route prose can take out of the engine, and whether it is covered.

The tool has two independent layers. A contract that shapes prose as it is
written, and a guard that scores a file after it is saved. A route is covered if
at least one layer reaches it. This file exists because a route was found that
neither layer reached: an agent that delegated a document to a subagent produced
prose the contract had never seen, and six measured documents scored the same
whether the tool was on or off.

Each test below is one route. A failure means prose can leave without either
layer touching it.
"""
import io
import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import detect

PLUGIN = json.loads(io.open(REPO / ".claude-plugin" / "plugin.json", encoding="utf-8").read())
HOOKS = PLUGIN["hooks"]
GUARD = io.open(REPO / "hooks" / "sloptrim-guard.js", encoding="utf-8").read()

SLOP = ("In today's fast-paced digital landscape, it is crucial to delve into the "
        "multifaceted tapestry of pivotal solutions. This comprehensive guide will "
        "showcase a robust, seamless framework that empowers teams to unlock their "
        "full potential. It is not just a tool, it is a game-changer.")

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def make_docx(path, text=SLOP):
    body = "".join('<w:p><w:r><w:t>%s.</w:t></w:r></w:p>' % s.strip()
                   for s in text.split(". ") if s.strip())
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("[Content_Types].xml", '<?xml version="1.0"?><Types/>')
        z.writestr("word/document.xml",
                   '<?xml version="1.0"?><w:document xmlns:w="%s"><w:body>%s</w:body></w:document>'
                   % (W, body))
    return path


def run_guard(payload, config_dir):
    return subprocess.run(
        ["node", str(REPO / "hooks" / "sloptrim-guard.js")],
        input=json.dumps(payload).encode("utf-8"),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env={**os.environ, "CLAUDE_PLUGIN_ROOT": str(REPO),
             "CLAUDE_CONFIG_DIR": str(config_dir), "PYTHONIOENCODING": "utf-8"},
        timeout=180)


def nudge(out):
    if not out.stdout.strip():
        return ""
    return json.loads(out.stdout.decode("utf-8"))["hookSpecificOutput"]["additionalContext"]


# --------------------------------------------------------------- the contract
def test_the_session_gets_the_contract():
    assert "SessionStart" in HOOKS


def test_a_subagent_gets_the_contract():
    """SessionStart context is parent-thread only. Without a SubagentStart hook a
    delegated document is written with no contract at all."""
    assert "SubagentStart" in HOOKS, "subagent prose would be written unguarded"
    cmd = json.dumps(HOOKS["SubagentStart"])
    assert "sloptrim-subagent.js" in cmd


def test_the_subagent_hook_returns_the_form_that_is_not_discarded():
    """SubagentStart drops raw stdout. Writing the contract to stdout the way the
    SessionStart hook does looks identical to a working hook and delivers nothing."""
    src = io.open(REPO / "hooks" / "sloptrim-subagent.js", encoding="utf-8").read()
    assert "hookSpecificOutput" in src
    assert "SubagentStart" in src


def test_the_subagent_hook_is_silent_when_switched_off():
    out = subprocess.run(
        ["node", str(REPO / "hooks" / "sloptrim-subagent.js")],
        input=b"{}", stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env={**os.environ, "CLAUDE_PLUGIN_ROOT": str(REPO)}, timeout=30)
    assert out.returncode == 0
    # It reads the real mode flag; whatever it is, it must not crash and must
    # emit either nothing or well-formed JSON.
    if out.stdout.strip():
        json.loads(out.stdout.decode("utf-8"))


# ------------------------------------------------------------------ the guard
def test_the_guard_watches_every_writing_tool():
    matchers = [g.get("matcher", "") for g in HOOKS["PostToolUse"]]
    joined = "|".join(matchers)
    for tool in ("Write", "Edit", "NotebookEdit"):
        assert tool in joined, "%s can save prose the guard never sees" % tool


def test_the_guard_reads_the_notebook_argument():
    """NotebookEdit names its target notebook_path. Reading only file_path would
    match the tool and then silently score nothing."""
    assert "notebook_path" in GUARD


@pytest.mark.parametrize("ext", [".md", ".txt", ".rst", ".tex", ".org", ".adoc"])
def test_plain_prose_formats_are_in_scope(ext):
    assert "'%s'" % ext in GUARD


@pytest.mark.parametrize("ext", [".docx", ".pptx", ".xlsx", ".odt", ".epub", ".ipynb"])
def test_document_formats_are_in_scope(ext):
    assert "'%s'" % ext in GUARD


def test_a_slop_docx_really_reaches_the_detector(tmp_path):
    """The declaration above is a string search. This runs the hook the way
    Claude Code runs it, on a document, and requires the nudge to come back."""
    p = make_docx(tmp_path / "brief.docx")
    out = run_guard({"tool_name": "Write", "tool_input": {"file_path": str(p)}}, tmp_path)
    assert out.returncode == 0, out.stderr[:400]
    assert "brief.docx" in nudge(out), out.stdout[:400]


def test_a_notebook_saved_by_notebookedit_really_reaches_the_detector(tmp_path):
    nb = {"cells": [{"cell_type": "markdown", "source": [SLOP]}],
          "metadata": {}, "nbformat": 4, "nbformat_minor": 5}
    p = tmp_path / "notes.ipynb"
    io.open(p, "w", encoding="utf-8").write(json.dumps(nb))
    out = run_guard({"tool_name": "NotebookEdit",
                     "tool_input": {"notebook_path": str(p)}}, tmp_path)
    assert out.returncode == 0, out.stderr[:400]
    assert "notes.ipynb" in nudge(out), out.stdout[:400]


def test_a_pdf_is_really_left_alone(tmp_path):
    p = tmp_path / "brief.pdf"
    p.write_bytes(b"%PDF-1.4\n" + SLOP.encode("utf-8"))
    out = run_guard({"tool_name": "Write", "tool_input": {"file_path": str(p)}}, tmp_path)
    assert out.returncode == 0, out.stderr[:400]
    assert out.stdout.strip() == b"", out.stdout[:400]


def test_a_notebook_is_scored_on_its_markdown_and_not_its_code(tmp_path):
    nb = {"cells": [
        {"cell_type": "markdown", "source": [SLOP]},
        {"cell_type": "code", "source": ["x = 1  # delve into the tapestry\n"]},
    ], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}
    p = tmp_path / "n.ipynb"
    io.open(p, "w", encoding="utf-8").write(json.dumps(nb))
    text = detect.extract_notebook_text(str(p))
    assert "fast-paced" in text
    assert "x = 1" not in text, "code cells are not prose and must not be scored"
    assert detect.scan(text)["_metrics"]["ai_tell_score"] >= 40


def test_a_notebook_with_no_markdown_scores_nothing(tmp_path):
    nb = {"cells": [{"cell_type": "code", "source": ["print(1)\n"]}]}
    p = tmp_path / "n.ipynb"
    io.open(p, "w", encoding="utf-8").write(json.dumps(nb))
    assert detect.extract_notebook_text(str(p)) == ""


def test_a_broken_notebook_does_not_raise(tmp_path):
    p = tmp_path / "n.ipynb"
    io.open(p, "w", encoding="utf-8").write("{not json")
    assert detect.extract_notebook_text(str(p)) == ""


# ------------------------------------------------------ known uncovered route
def test_the_shell_route_is_uncovered_and_documented():
    """A file written by a shell command reaches disk without passing Write or
    Edit, so the guard never fires on it. The contract still applies to whoever
    composed the text, so this is a gap in the second layer only. It is recorded
    rather than fixed: matching Bash would mean parsing shell to guess which
    paths a command writes, and guessing wrong in either direction is worse than
    the gap.
    """
    matchers = "|".join(g.get("matcher", "") for g in HOOKS["PostToolUse"])
    assert "Bash" not in matchers
    doc = io.open(REPO / "README.md", encoding="utf-8").read()
    assert "Bash" in doc, (
        "the guard never fires on a file written by a shell command. That gap is "
        "only honest if the README says so")


def test_pdf_and_rtf_are_declared_out_of_scope():
    assert "BINARY_PROSE" in GUARD
    for ext in (".pdf", ".rtf"):
        assert "'%s'" % ext in GUARD
