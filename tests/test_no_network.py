"""test_no_network.py: nothing in this repository may reach the network.

The public benchmark accepts a pinned local dataset path and has no reason to
open a socket. The scan walks the whole tree rather than a fixed list, so a
fetch added anywhere fails the suite.
"""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SELF = Path(__file__).resolve()

SCANNED = (".py", ".js", ".mjs", ".cjs", ".ps1", ".sh")
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".pytest_cache"}

BANNED = re.compile(
    r"\b(?:"
    r"urllib|urlopen|http\.client|socket|ssl|ftplib|smtplib|telnetlib|"
    r"requests|httpx|aiohttp|"
    r"XMLHttpRequest|WebSocket|EventSource|"
    r"Invoke-WebRequest|Invoke-RestMethod|Net\.WebClient|curl|wget"
    r")\b"
    r"|require\(\s*['\"](?:https?|net|dgram|tls|dns)['\"]\s*\)"
    r"|\bfetch\s*\("
)


def scanned_files():
    out = []
    for path in REPO.rglob("*"):
        if not path.is_file() or path.suffix not in SCANNED:
            continue
        if SKIP_DIRS & set(p.name for p in path.parents):
            continue
        if path.resolve() == SELF:
            continue
        out.append(path)
    return sorted(out)


def test_the_scan_reaches_the_tool_and_the_recorder():
    found = {str(p.relative_to(REPO)).replace("\\", "/") for p in scanned_files()}
    for required in ("scripts/detect.py", "hooks/sloptrim-guard.js",
                     "hooks/sloptrim-lib.js", "hooks/sloptrim-statusline.ps1",
                     "record/session_capture.py", "record/anim.py",
                     "tests/test_hooks.sh"):
        assert required in found, "%s was not scanned; the sweep is not reaching it" % required


def test_nothing_in_the_repository_has_network_capability():
    offenders = []
    for path in scanned_files():
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            m = BANNED.search(line)
            if m:
                offenders.append("%s:%d %s" % (path.relative_to(REPO), n, m.group(0)))
    assert not offenders, (
        "nothing here may reach the network. Found:\n  " + "\n  ".join(offenders))


def test_the_pattern_would_catch_a_fetch():
    """A sweep that cannot fail is not a check."""
    for sample in ("import urllib.request", "const r = await fetch(url)",
                   "Invoke-WebRequest -Uri $u", "curl -sSL https://example.com",
                   "const net = require('net')"):
        assert BANNED.search(sample), sample
