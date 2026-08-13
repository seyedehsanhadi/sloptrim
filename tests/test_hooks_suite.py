"""Run the hook suite from pytest, so one command covers both runtimes.

The detector is Python and the hooks are Node, so they are exercised by two
harnesses: these files, and tests/test_hooks.sh piping synthetic payloads into
each hook. Nothing joined them, which meant `pytest tests/` could pass with
every hook broken. This is the join.
"""
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SUITE = REPO / "tests" / "test_hooks.sh"


def _bash():
    """A bash that can still see node.

    On Windows the first bash on PATH is often Git's raw MSYS shell, which does
    not carry the Windows PATH through, so the hooks fail with `node: command
    not found` and the suite reports 39 failures that are nothing to do with the
    hooks. Candidates are tried until one can find node.
    """
    seen = []
    for cand in (r"C:\Program Files\Git\bin\bash.exe", shutil.which("bash"),
                 r"C:\Program Files\Git\usr\bin\bash.exe"):
        if not cand or cand in seen or not Path(cand).exists():
            continue
        seen.append(cand)
        probe = subprocess.run([cand, "-lc", "command -v node"],
                               capture_output=True, text=True)
        if probe.returncode == 0 and probe.stdout.strip():
            return cand
    return None


BASH = _bash()


@pytest.mark.skipif(BASH is None, reason="no bash that can find node")
def test_the_hook_suite_passes():
    r = subprocess.run([BASH, str(SUITE)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", cwd=str(REPO))
    tail = "\n".join((r.stdout or "").strip().splitlines()[-12:])
    assert r.returncode == 0, "tests/test_hooks.sh failed:\n%s\n%s" % (tail, r.stderr[-800:])
    assert "0 failed" in (r.stdout or ""), tail
