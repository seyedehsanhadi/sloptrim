"""Record a real session, hook by hook, and write down exactly what came back.

The animation in the README is drawn from this file. Recording the hook lines
rather than writing them means the picture cannot claim behaviour the hooks do
not have: every hook line, every score and every millisecond it draws in the
guard's own colour came out of a real invocation here, with the payload shapes
Claude Code sends. The grey labels beside them are narration written in
record/anim.py, drawn in a different colour and without the "sloptrim" prefix so
they cannot be read as recorded output.

The prose is record/draft.md and record/rewrite.md, two short sample documents
written for this recording.

    python record/session_capture.py      # re-record into record/session.json
"""
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
HOOKS = os.path.join(ROOT, "hooks")
OUT = os.path.join(HERE, "session.json")

DRAFT_NAME = "draft.md"
FIXED_NAME = "rewrite.md"
DRAFT = os.path.join(HERE, DRAFT_NAME)
FIXED = os.path.join(HERE, FIXED_NAME)
PROMPT = "write the summer reading challenge listing"

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def write_docx(path, text):
    """The smallest Word document the guard will read out of a zip."""
    paras = []
    for block in re.split(r"\n\s*\n", text.strip()):
        block = " ".join(block.split())
        if block:
            block = (block.replace("&", "&amp;").replace("<", "&lt;")
                     .replace(">", "&gt;"))
            paras.append("<w:p><w:r><w:t>%s</w:t></w:r></w:p>" % block)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", '<?xml version="1.0"?><Types/>')
        z.writestr("word/document.xml",
                   '<?xml version="1.0"?><w:document xmlns:w="%s"><w:body>%s'
                   "</w:body></w:document>" % (W, "".join(paras)))
    return path


def redact(text, work):
    """Keep the shape, drop the machine.

    The contract legitimately carries an absolute path to detect.py, because
    that is how the hook tells the model where to find it. True on the machine
    that recorded it, and nobody else's business once this file is committed.
    """
    for real, stand_in in ((work, "<project>"), (ROOT, "<plugin>"),
                           (os.path.expanduser("~"), "~")):
        for form in (real, real.replace("\\", "\\\\"), real.replace("\\", "/")):
            text = text.replace(form, stand_in)
    return text


def run(hook, payload, env_extra=None, cwd=None):
    """Fire one hook the way the harness does and time the round trip.

    cwd matters: `/sloptrim init` writes AGENTS.md next to wherever the agent is
    working, so recording it from the repository root drops the file in here.
    """
    env = dict(os.environ, SLOPTRIM_DEFAULT_MODE="full", PYTHONIOENCODING="utf-8")
    env.update(env_extra or {})
    t0 = time.perf_counter()
    p = subprocess.run(["node", os.path.join(HOOKS, hook)],
                       input=json.dumps(payload), capture_output=True,
                       text=True, encoding="utf-8", env=env, cwd=cwd)
    ms = (time.perf_counter() - t0) * 1000
    out = p.stdout.strip()
    context = ""
    if out.startswith("{"):
        try:
            context = json.loads(out)["hookSpecificOutput"]["additionalContext"]
        except Exception:
            context = out
    else:
        context = out
    return {"hook": hook, "ms": round(ms, 1), "exit": p.returncode,
            "silent": not out, "context": context}


def main():
    work = tempfile.mkdtemp()
    listing = os.path.join(work, "listing.md")
    sid = "capture"
    events = []

    ev = run("sloptrim-activate.js", {"session_id": sid, "source": "startup"})
    ev["event"] = "SessionStart"
    events.append(ev)

    ev = run("sloptrim-tracker.js", {"session_id": sid, "prompt": PROMPT})
    ev["event"] = "UserPromptSubmit"
    events.append(ev)

    ev = run("sloptrim-subagent.js", {"session_id": sid})
    ev["event"] = "SubagentStart"
    events.append(ev)

    draft_text = io.open(DRAFT, encoding="utf-8").read()
    fixed_text = io.open(FIXED, encoding="utf-8").read()

    io.open(listing, "w", encoding="utf-8", newline="\n").write(draft_text)
    ev = run("sloptrim-guard.js",
             {"session_id": sid, "tool_name": "Write",
              "tool_input": {"file_path": listing}})
    ev["event"] = "PostToolUse"
    ev["tool"] = "Write"
    ev["file"] = "listing.md"
    ev["lines"] = draft_text.rstrip("\n").count("\n") + 1
    events.append(ev)

    io.open(listing, "w", encoding="utf-8", newline="\n").write(fixed_text)
    ev = run("sloptrim-guard.js",
             {"session_id": sid, "tool_name": "Edit",
              "tool_input": {"file_path": listing}})
    ev["event"] = "PostToolUse"
    ev["tool"] = "Edit"
    ev["file"] = "listing.md"
    events.append(ev)

    # The same prose saved as a Word document, so the zip path is exercised
    # rather than described.
    docx = write_docx(os.path.join(work, "listing.docx"), draft_text)
    ev = run("sloptrim-guard.js",
             {"session_id": sid, "tool_name": "Write",
              "tool_input": {"file_path": docx}})
    ev["event"] = "PostToolUse"
    ev["tool"] = "Write"
    ev["file"] = "listing.docx"
    events.append(ev)

    ev = run("sloptrim-tracker.js", {"session_id": sid, "prompt": "/sloptrim init"},
             cwd=work)
    ev["event"] = "UserPromptSubmit"
    ev["command"] = "/sloptrim init"
    ev["wrote_agents_md"] = os.path.exists(os.path.join(work, "AGENTS.md"))
    events.append(ev)

    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    import detect
    scores = {}
    for tag, text in (("draft", draft_text), ("fixed", fixed_text)):
        m = detect.scan(text)["_metrics"]
        scores[tag] = {"score": m["ai_tell_score"], "band": m.get("ai_tell_band")}

    for e in events:
        e["context"] = redact(e.get("context", ""), work)

    io.open(OUT, "w", encoding="utf-8", newline="\n").write(
        json.dumps({"prompt": PROMPT, "draft": DRAFT_NAME, "fixed": FIXED_NAME,
                    "scores": scores, "events": events}, indent=2) + "\n")

    print("recorded %d hook invocations to %s" % (len(events), os.path.relpath(OUT, ROOT)))
    for e in events:
        print("  %-16s %-24s %6.1f ms  %s"
              % (e["event"], e["hook"], e["ms"],
                 "silent" if e["silent"] else e["context"][:58].replace("\n", " ")))


if __name__ == "__main__":
    main()
