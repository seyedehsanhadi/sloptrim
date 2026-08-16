"""check_docs.py: re-derive every falsifiable documentation claim from the code
and from this tree. Offline, standard library only. Exits 1 on the first
disagreement it can name, listing every failure with both values.

Usage:
    python scripts/check_docs.py            # everything, runs both suites
    python scripts/check_docs.py --no-suites  # skip pytest and the hook suite
"""

import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import detect

PASSED = 0
FAILURES = []


def check(label, ok, detail=""):
    global PASSED
    if ok:
        PASSED += 1
    else:
        FAILURES.append((label, detail))
    return ok


def eq(label, got, want, where=""):
    return check(label, got == want,
                 "%sstates %r, the tree gives %r" % (where and where + ": ", got, want))


# --------------------------------------------------------------- number words
_WORDS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
    "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16,
    "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20,
}


def as_int(token):
    token = token.strip().lower()
    if token.isdigit():
        return int(token)
    return _WORDS.get(token)


# ------------------------------------------------------------- document sweep
DOC_SUFFIX = {".md", ".mdc", ".cff", ".json"}
DOC_NAME = {"NOTICE"}
SKIP_PART = {".git", "__pycache__", ".pytest_cache", "node_modules", ".venv"}

REQUIRED = [
    "README.md", "CHANGELOG.md", "CITATION.cff", "ETHICS.md", "NOTICE",
    "CONTRIBUTING.md", "SECURITY.md", "SKILL.md", "references/patterns.md",
    ".claude-plugin/plugin.json", ".claude-plugin/marketplace.json",
    ".cursor/rules/sloptrim.mdc",
]


def discover():
    found = []
    for path in sorted(REPO.rglob("*")):
        if not path.is_file():
            continue
        if SKIP_PART & set(path.parts):
            continue
        if path.suffix in DOC_SUFFIX or path.name in DOC_NAME:
            found.append(path)
    return found


DOCS = discover()
REL = {p: p.relative_to(REPO).as_posix() for p in DOCS}
RAW = {p: p.read_text(encoding="utf-8") for p in DOCS}


def flatten(text):
    text = text.replace("`", "").replace("*", "")
    text = text.replace("\u2019", "'").replace("\u2264", "<=")
    text = text.replace("\u2014", " ").replace("\u2013", "-")
    return re.sub(r"\s+", " ", text)


FLAT = {p: flatten(RAW[p]) for p in DOCS}


# -------------------------------------------------------------- derived facts
SRC = (REPO / "scripts" / "detect.py").read_text(encoding="utf-8")
GUARD = (REPO / "hooks" / "sloptrim-guard.js").read_text(encoding="utf-8")
LIB = (REPO / "hooks" / "sloptrim-lib.js").read_text(encoding="utf-8")
PLUGIN = json.loads((REPO / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
MARKET = json.loads((REPO / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
PATTERNS = (REPO / "references" / "patterns.md").read_text(encoding="utf-8")

VERSION = PLUGIN["version"]

HEADINGS = re.findall(r"^### (\d+)\. ", PATTERNS, re.M)
CATALOGUE = len(re.findall(r"^### ", PATTERNS, re.M))
CATALOGUE_NUMS = sorted(int(n) for n in HEADINGS)

RULE_KEYS = sorted(set(re.findall(r"[\"'](\d{1,2}_[a-z0-9_]+)[\"']", SRC)))
FAMILIES = sorted({int(k.split("_", 1)[0]) for k in RULE_KEYS})
UNREACHED = sorted(set(CATALOGUE_NUMS) - set(FAMILIES))

REPORT_ONLY = set(detect._SCORE_REPORT_ONLY)
STYLE_ONLY = set(detect._SCORE_STYLE_ONLY)
DEMOTED = REPORT_ONLY | STYLE_ONLY


def scoring_keys():
    text = "This is ordinary prose written to fill the buffer here. " * 40
    burst = {"cv": 0.6, "monotonous": False}
    para = {"cv": 0.6}
    punct = {"checked": True, "underused": True}
    base = detect.ai_tell_score({}, text, burst, para, punct, None)["score"]
    moving = set()
    for key in RULE_KEYS:
        one = detect.ai_tell_score({key: {"count": 6}}, text, burst, para, punct, None)
        if one["score"] != base:
            moving.add(key)
    return moving


MOVING = scoring_keys()
SCORING_FAMS = sorted({int(k.split("_", 1)[0]) for k in MOVING})
ADVICE_FAMS = sorted(set(FAMILIES) - set(SCORING_FAMS))

BANDS = []
for _s in range(0, 101):
    _b = detect._band(_s)
    if not BANDS or BANDS[-1][0] != _b:
        BANDS.append([_b, _s, _s])
    else:
        BANDS[-1][2] = _s
BAND_NAMES = [b[0] for b in BANDS]
SCORE_MAX = BANDS[-1][2]

HOOK_BANDS = re.findall(r"return '(reads [^']+)'", LIB)


def js_set(name, source):
    body = re.search(r"const %s = new Set\(\[(.*?)\]\)" % name, source, re.S)
    return set(re.findall(r"'([^']+)'", body.group(1)))


PROSE_EXT = js_set("PROSE_EXT", GUARD)
OFFICE_EXT = js_set("OFFICE_EXT", GUARD)
NOTEBOOK_EXT = js_set("NOTEBOOK_EXT", GUARD)
ALL_EXT = PROSE_EXT | OFFICE_EXT | NOTEBOOK_EXT
ZIP_DOC = set(re.findall(r'"(\.[a-z]+)": \(', SRC))

_thr = re.search(r"mode === 'strict' \? (\d+) : (\d+)", GUARD)
STRICT_THRESHOLD, DEFAULT_THRESHOLD = int(_thr.group(1)), int(_thr.group(2))
PATH_TIMEOUT = int(re.search(r"timeout: (\d+) \}, \[filePath\]", GUARD).group(1)) // 1000
PIPE_TIMEOUT = int(re.search(r"runDetect\(text, \{ timeout: (\d+)", GUARD).group(1)) // 1000

WORKFLOWS = sorted((REPO / ".github" / "workflows").glob("*.yml")) if \
    (REPO / ".github" / "workflows").is_dir() else []
CI_PRESENT = bool(WORKFLOWS)


# --------------------------------------------------------------------- suites
def run(cmd, cwd=REPO):
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True,
                          encoding="utf-8", errors="replace", env=env)


def python_test_count():
    out = run([sys.executable, "-m", "pytest", "tests/", "--collect-only", "-q"])
    hit = re.search(r"(\d+) tests? collected", out.stdout)
    if not hit:
        raise SystemExit("check_docs: pytest collection produced no count\n"
                         + out.stdout[-2000:] + out.stderr[-2000:])
    return int(hit.group(1))


def tool(name):
    found = shutil.which(name)
    if not found:
        raise SystemExit("check_docs: %s is not on PATH and the suites need it" % name)
    return found


def hook_check_count():
    out = run([tool("bash"), "tests/test_hooks.sh"])
    hit = re.search(r"hook tests: (\d+) passed, (\d+) failed", out.stdout)
    if not hit:
        raise SystemExit("check_docs: the hook suite produced no count\n"
                         + out.stdout[-2000:] + out.stderr[-2000:])
    if hit.group(2) != "0":
        raise SystemExit("check_docs: the hook suite reports %s failures" % hit.group(2))
    return int(hit.group(1))


def doctor_ok_lines():
    payload = json.dumps({"prompt": "/sloptrim doctor", "session_id": "check_docs"})
    cfg = tempfile.mkdtemp(prefix="check_docs-cfg-")
    try:
        with open(os.path.join(cfg, ".sloptrim-active"), "w", encoding="utf-8") as fh:
            fh.write("full")
        env = dict(os.environ, CLAUDE_CONFIG_DIR=cfg,
                   CLAUDE_PLUGIN_ROOT=str(REPO), SLOPTRIM_DEFAULT_MODE="full")
        out = subprocess.run([tool("node"), str(REPO / "hooks" / "sloptrim-tracker.js")],
                             input=payload, capture_output=True, text=True,
                             encoding="utf-8", errors="replace", cwd=str(REPO), env=env)
        return out.stdout.count("[OK]")
    finally:
        shutil.rmtree(cfg, ignore_errors=True)


WITH_SUITES = "--no-suites" not in sys.argv
PY_TESTS = python_test_count() if WITH_SUITES else None
HOOK_CHECKS = hook_check_count() if WITH_SUITES else None
TOTAL_TESTS = (PY_TESTS + HOOK_CHECKS) if WITH_SUITES else None
DOCTOR_LINES = doctor_ok_lines() if WITH_SUITES else None


# -------------------------------------------------------------- claim grammar
NUM = (r"(\d+|zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|"
       r"twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|"
       r"nineteen|twenty)")


def C(pattern, *values):
    return (re.compile(pattern.replace("(?:N)", NUM), re.I),
            [str(v) for v in values])


CLAIMS = [
    C(r"catalogue of (?:N) documented patterns", CATALOGUE),
    C(r"catalogue of (?:N) patterns", CATALOGUE),
    C(r"catalogue holds (?:N) patterns", CATALOGUE),
    C(r"(?:N) documented (?:AI-writing )?patterns", CATALOGUE),
    C(r"documents (?:N) patterns", CATALOGUE),
    C(r"against (?:N) documented patterns", CATALOGUE),

    C(r"(?:N) of the (?:N) have a detector", len(FAMILIES), CATALOGUE),
    C(r"(?:N) of them have a detector", len(FAMILIES)),
    C(r"(?:N) of them with a detector", len(FAMILIES)),
    C(r"(?:N) machine-checked by", len(FAMILIES)),
    C(r"Of the (?:N),", len(FAMILIES)),
    C(r"of the (?:N) rules are held out", len(FAMILIES)),

    C(r"the other (?:N) need a reading", len(UNREACHED)),
    C(r"remaining (?:N) need a reading", len(UNREACHED)),
    C(r"(?:N) requiring semantic judgment", len(UNREACHED)),
    C(r"The (?:N) catalogue entries with no detector", len(UNREACHED)),

    C(r"(?:N) able to move the score", len(SCORING_FAMS)),
    C(r"(?:N) can move the score", len(SCORING_FAMS)),
    C(r"(?:N) still do", len(SCORING_FAMS)),
    C(r"(?:N)(?: of the \d+ catalogue)? numbers carry no weight", len(ADVICE_FAMS)),
    C(r"(?:N) are reported as writing advice", len(ADVICE_FAMS)),
    C(r"only (?:N) patterns end up advice-only", len(ADVICE_FAMS)),

    C(r"(?:N) detector rules (?:are |held |demoted)", len(DEMOTED)),
    C(r"(?<!of the )(?<!\d)(?:N) rules are held out of the score", len(DEMOTED)),
    C(r"why (?:N) rules are held out", len(DEMOTED)),
    C(r"fall on (?:N) catalogue numbers", len(DEMOTED)),
    C(r"land on (?:N) catalogue numbers", len(DEMOTED)),
    C(r"(?:N) to report-only and (?:N) to", len(REPORT_ONLY), len(STYLE_ONLY)),
    C(r"(?:N) keys live there today", len(REPORT_ONLY)),
    C(r"(?:N) of the 71 catalogue numbers carry no weight", len(ADVICE_FAMS)),

    C(r"(?:N) formats", len(ALL_EXT)),
    C(r"Formats \| (?:N),", len(ALL_EXT)),
    C(r"(?:N) zip-based", len(OFFICE_EXT)),
    C(r"(?:N) plain-text", len(PROSE_EXT)),

    C(r"(?:N) bands", len(BAND_NAMES)),
    C(r"those (?:N) names describe", len(BAND_NAMES) + len(HOOK_BANDS)),
    C(r"ai_tell_score \(0-(\d+)\)", SCORE_MAX),
    C(r"score is 0-(\d+)", SCORE_MAX),
    C(r"scores the file 0 to (\d+)", SCORE_MAX),
    C(r"The (\d+) to (\d+) score lands", 0, SCORE_MAX),
    C(r"the 0-(\d+) score", SCORE_MAX),

    C(r"(\d+) seconds on text it pipes in", PIPE_TIMEOUT),
    C(r"(\d+) seconds when it hands over a path", PATH_TIMEOUT),
    C(r"(\d+)-second ceiling", PIPE_TIMEOUT),
    C(r"guard timeout is (\d+)s", PIPE_TIMEOUT),

    C(r"nudges above (\d+), or above (\d+) in strict", DEFAULT_THRESHOLD, STRICT_THRESHOLD),
    C(r"Flags at (\d+) instead of (\d+)", STRICT_THRESHOLD, DEFAULT_THRESHOLD),

    C(r"version-(\d+\.\d+\.\d+)", VERSION),
    C(r"(?<!cff-)version: (\d+\.\d+\.\d+)", VERSION),
    C(r"## \[(\d+\.\d+\.\d+)\]", VERSION),
    C(r"tag/v(\d+\.\d+\.\d+)", VERSION),
    C(r'"version": "(\d+\.\d+\.\d+)"', VERSION),
]

if WITH_SUITES:
    CLAIMS += [
        C(r"(\d+) Python tests", PY_TESTS),
        C(r"# (\d+) tests", PY_TESTS),
        C(r"(\d+) hook checks", HOOK_CHECKS),
        C(r"tests-(\d+)-", TOTAL_TESTS),
        C(r"answers with (?:N) \[OK\] lines", DOCTOR_LINES),
        C(r"It answers with (?:N) \[OK\]", DOCTOR_LINES),
    ]

SENTINELS = [
    r"documented patterns", r"have a detector", r"machine-checked",
    r"move the score", r"reported as writing advice", r"held out of the score",
    r"demoted out of the score", r"carry no weight", r"need a reading",
    r"formats", r"zip-based", r"bands", r"version-\d",
    r"catalogue of", r"catalogue holds",
]
if WITH_SUITES:
    SENTINELS += [r"hook checks", r"Python tests", r"\[OK\] lines", r"tests-\d"]
SENTINELS = [re.compile(s, re.I) for s in SENTINELS]
COUNTED = re.compile(NUM + r"\b", re.I)
SEGMENT = re.compile(r"[^.|]+")


def claim_pass():
    for path in DOCS:
        flat = FLAT[path]
        spans = []
        for rx, wanted in CLAIMS:
            for m in rx.finditer(flat):
                spans.append(m.span())
                for i, want in enumerate(wanted, start=1):
                    got = m.group(i)
                    same = (got == want) or (as_int(got) is not None
                                             and as_int(got) == as_int(want))
                    check("%s: %s" % (REL[path], m.group(0).strip()[:70]), same,
                          "%s says %r where the tree gives %r"
                          % (REL[path], got, want))
        for seg in SEGMENT.finditer(flat):
            body = seg.group(0)
            if not COUNTED.search(body):
                continue
            if not any(rx.search(body) for rx in SENTINELS):
                continue
            a, b = seg.span()
            covered = any(s < b and a < e for s, e in spans)
            check("%s: claim sentence is checked" % REL[path], covered,
                  "%s carries a count-bearing sentence no rule in check_docs.py "
                  "re-derives, so it could drift unnoticed: %r"
                  % (REL[path], body.strip()[:160]))


# ------------------------------------------------------------ links and paths
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
ATTR = re.compile(r'(?:src|href|srcset)="([^"]+)"')
PATHY = re.compile(r"(?<![\w/~.${}-])((?:\.?[A-Za-z0-9_-]+/)+[A-Za-z0-9_.-]+\.[a-z]{2,6})\b")
EXTERNAL = ("http://", "https://", "mailto:", "#", "$", "~")


def slug(heading):
    s = heading.strip().lower()
    s = re.sub(r"[`*]", "", s)
    s = re.sub(r"[^\w\s-]", "", s)
    return re.sub(r"\s+", "-", s.strip())


def link_pass():
    for path in DOCS:
        raw = RAW[path]
        anchors = {slug(h) for h in re.findall(r"^#{1,6} (.+)$", raw, re.M)}
        targets = LINK.findall(raw) + ATTR.findall(raw)
        for target in targets:
            target = target.split()[0] if " " in target else target
            if target.startswith("#"):
                check("%s: anchor %s" % (REL[path], target),
                      target[1:] in anchors,
                      "%s links to %s and no heading in it slugifies to that"
                      % (REL[path], target))
                continue
            if target.startswith(EXTERNAL):
                continue
            resolved = (path.parent / target.split("#")[0]).resolve()
            check("%s: link %s" % (REL[path], target), resolved.exists(),
                  "%s links to %s which resolves to %s and that does not exist"
                  % (REL[path], target, resolved))
        for token in set(PATHY.findall(raw)):
            head = token.split("/")[0]
            if head in ("word", "ppt", "xl", "https:", "http:"):
                continue
            if token.endswith((".docx", ".txt", ".epub")) and not (REPO / token).exists() \
                    and head not in {p.name for p in REPO.iterdir()}:
                continue
            if head not in {p.name for p in REPO.iterdir()}:
                check("%s: path %s" % (REL[path], token), False,
                      "%s names the path %s and no such directory exists at the "
                      "root of this repository" % (REL[path], token))
                continue
            check("%s: path %s" % (REL[path], token), (REPO / token).exists(),
                  "%s names the path %s and it does not exist in this tree"
                  % (REL[path], token))


# ---------------------------------------------------------------- svg strings
def svg_text(name):
    body = (REPO / "assets" / name).read_text(encoding="utf-8")
    out = []
    for chunk in re.findall(r"<text[^>]*>(.*?)</text>", body, re.S):
        flat = re.sub(r"<[^>]+>", "", chunk).strip()
        if flat:
            out.append(flat)
    return out


def svg_pass():
    light = svg_text("detection-light.svg")
    dark = svg_text("detection-dark.svg")
    check("detection SVGs render the same strings", light == dark,
          "assets/detection-light.svg and assets/detection-dark.svg disagree: %r"
          % (sorted(set(light) ^ set(dark)),))
    demo_l, demo_d = svg_text("demo-light.svg"), svg_text("demo-dark.svg")
    check("demo SVGs render the same strings", demo_l == demo_d,
          "assets/demo-light.svg and assets/demo-dark.svg disagree: %r"
          % (sorted(set(demo_l) ^ set(demo_d))[:10],))

    readme = FLAT[REPO / "README.md"]
    figures = [t for t in light if re.fullmatch(r"0\.\d{3}", t)]
    labels = [t for t in light if re.fullmatch(r"[A-Za-z][A-Za-z ]{3,}", t)
              and t not in ("against Mixtral",)]
    check("the detection chart renders four figures", len(figures) == 4,
          "assets/detection-light.svg renders %r" % (figures,))
    for fig in figures:
        check("README.md quotes the charted figure %s" % fig, fig in readme,
              "assets/detection-light.svg renders %s and README.md never states it"
              % fig)
    for label in labels:
        check("README.md names the charted corpus %r" % label, label in readme,
              "assets/detection-light.svg labels a bar %r and README.md never "
              "names it" % label)
    for doc in DOCS:
        for quoted in set(re.findall(r"\b0\.\d{3}\b", FLAT[doc])):
            check("%s: %s is a charted figure" % (REL[doc], quoted),
                  quoted in figures,
                  "%s quotes %s and no committed chart renders it"
                  % (REL[doc], quoted))

    joined = " ".join(demo_l)
    hit = re.search(r"(\d+)/(\w+)", joined)
    check("the demo SVG still renders a score and band", hit is not None,
          "no <score>/<band> string found in assets/demo-light.svg")
    if hit is None:
        return
    score, band = hit.group(1, 2)
    check("the demo SVG renders a real band name", band in BAND_NAMES,
          "assets/demo-light.svg renders the band %r and detect.py emits %r"
          % (band, BAND_NAMES))
    result = json.loads(run([sys.executable, str(REPO / "scripts" / "detect.py"),
                             str(REPO / "record" / "draft.md")]).stdout)
    eq("the demo score matches record/draft.md",
       str(result["_metrics"]["ai_tell_score"]), score, "assets/demo-light.svg")
    eq("the demo band matches record/draft.md",
       result["_metrics"]["ai_tell_band"], band, "assets/demo-light.svg")
    labelled = [v["label"] for k, v in result.items()
                if not k.startswith("_") and isinstance(v, dict) and "label" in v]
    for tell in re.findall(r"sloptrim . ([^<]+)", joined):
        for name in [n.strip() for n in tell.split(";") if n.strip()]:
            check("the demo SVG names a tell record/draft.md raises", name in labelled,
                  "assets/demo-light.svg names the tell %r and detect.py does not "
                  "raise it on record/draft.md, which raises %r" % (name, labelled))
    clean = json.loads(run([sys.executable, str(REPO / "scripts" / "detect.py"),
                            str(REPO / "record" / "rewrite.md")]).stdout)
    eq("the demo clean read matches record/rewrite.md",
       clean["_metrics"]["ai_tell_band"], BAND_NAMES[0], "record/rewrite.md")

    for name in ("sloptrim-logo.svg", "sloptrim-logo-dark.svg"):
        body = (REPO / "assets" / name).read_text(encoding="utf-8")
        check("assets/%s embeds the font NOTICE documents" % name,
              "font/woff2" in body or "font-woff2" in body,
              "NOTICE documents an embedded woff2 subset and assets/%s carries no "
              "woff2 data URI" % name)
    embedded = sorted(p.relative_to(REPO).as_posix() for p in REPO.rglob("*")
                      if p.is_file() and p.suffix in {".svg", ".css", ".html"}
                      and not SKIP_PART & set(p.parts)
                      and re.search(r"font/woff2|font-woff2",
                                    p.read_text(encoding="utf-8", errors="replace")))
    check("only the two logos carry third-party material",
          embedded == ["assets/sloptrim-logo-dark.svg", "assets/sloptrim-logo.svg"],
          "NOTICE says no other file carries third-party material, and a woff2 "
          "payload sits in %r" % (embedded,))


# ------------------------------------------------------------- code agreement
def import_pass():
    local = {p.stem for p in REPO.rglob("*.py") if not SKIP_PART & set(p.parts)}
    wanted = set()
    for path in sorted(REPO.rglob("*.py")):
        if SKIP_PART & set(path.parts):
            continue
        body = path.read_text(encoding="utf-8")
        for name in re.findall(r"^\s*(?:import|from) ([A-Za-z_][\w.]*)", body, re.M):
            root = name.split(".")[0]
            if root not in local and root != "__future__":
                wanted.add(root)
    for name in sorted(wanted):
        try:
            found = importlib.util.find_spec(name) is not None
        except (ImportError, ValueError):
            found = False
        check("the environment provides %s" % name, found,
              "a script in this tree imports %s and this interpreter cannot find "
              "it, so a suite will die during collection rather than fail a test"
              % name)


def code_pass():
    eq("plugin.json and marketplace.json describe the same plugin",
       MARKET["plugins"][0]["description"], PLUGIN["description"],
       ".claude-plugin/marketplace.json")
    eq("plugin.json and marketplace.json name the same plugin",
       MARKET["plugins"][0]["name"], PLUGIN["name"], ".claude-plugin/marketplace.json")
    for hook in PLUGIN["hooks"].values():
        for group in hook:
            for entry in group["hooks"]:
                rel = re.search(r"hooks/[\w.-]+", entry["command"]).group(0)
                check("plugin.json wires an existing hook: %s" % rel,
                      (REPO / rel).exists(),
                      ".claude-plugin/plugin.json runs %s and it is not in this tree"
                      % rel)

    check("the catalogue numbers its sections 1..%d" % CATALOGUE,
          CATALOGUE_NUMS == list(range(1, CATALOGUE + 1)),
          "references/patterns.md has %d sections numbered %r"
          % (CATALOGUE, CATALOGUE_NUMS))
    check("every detector family has a catalogue section",
          set(FAMILIES) <= set(CATALOGUE_NUMS),
          "scripts/detect.py carries rule families %r with no catalogue section"
          % (sorted(set(FAMILIES) - set(CATALOGUE_NUMS)),))

    listed = re.search(r"catalogue entries with no detector behind them \(([\d, ]+)\)",
                       FLAT[REPO / "SKILL.md"])
    if listed:
        stated = [int(n) for n in listed.group(1).split(",")]
        eq("SKILL.md lists the entries with no detector",
           str(stated), str(UNREACHED), "SKILL.md")

    ethics = FLAT[REPO / "ETHICS.md"]
    for name in BAND_NAMES:
        check("ETHICS.md names the band %r" % name, name in ethics,
              "detect.py emits the band %r and ETHICS.md never names it" % name)
    for name in HOOK_BANDS:
        check("ETHICS.md names the hook phrase %r" % name, name in ethics,
              "hooks/sloptrim-lib.js prints %r and ETHICS.md never names it" % name)
    readme = FLAT[REPO / "README.md"]
    for name in BAND_NAMES:
        check("README.md names the band %r" % name, name in readme,
              "detect.py emits the band %r and README.md never names it" % name)
    changelog = FLAT[REPO / "CHANGELOG.md"]
    for name, low, high in BANDS:
        check("CHANGELOG.md gives the right range for %r" % name,
              "%s (%d-%d)" % (name, low, high) in changelog,
              "detect.py puts %r at %d-%d and CHANGELOG.md does not say so"
              % (name, low, high))

    for section in re.findall(r"sections ([\d, and]+) are drawn from Pangram",
                              FLAT[REPO / "NOTICE"]):
        for num in re.findall(r"\d+", section):
            body = re.split(r"^### ", PATTERNS, flags=re.M)
            hit = [b for b in body if b.startswith(num + ". ")]
            check("patterns.md section %s cites Pangram" % num,
                  bool(hit) and "Pangram" in hit[0],
                  "NOTICE says references/patterns.md section %s draws on Pangram "
                  "Labs and that section does not cite them" % num)
    check("tests/validation_corpus.py holds the sample NOTICE names",
          "h_classic_prose" in (REPO / "tests" / "validation_corpus.py")
          .read_text(encoding="utf-8"),
          "NOTICE names h_classic_prose in tests/validation_corpus.py and it is "
          "not there")

    for ext in sorted(ZIP_DOC):
        check("guard.js and detect.py agree that %s is a document" % ext,
              ext in OFFICE_EXT,
              "scripts/detect.py unpacks %s and hooks/sloptrim-guard.js does not "
              "route it" % ext)


# ----------------------------------------------------- re-derivability and CI
MEASURE = re.compile(r"figure|number|measurement|result|rate|roc|auc|corpus|"
                     r"corpora|benchmark|claim|published|score", re.I)
NEGATION = re.compile(r"\b(no|not|nothing|never|neither|cannot|can't|without|"
                      r"privately|elsewhere)\b", re.I)
DERIVE = re.compile(r"[^.]*\b(re-?deriv\w*|recomput\w*|reproduc\w*)\b[^.]*")


def honesty_pass():
    for path in DOCS:
        for m in DERIVE.finditer(FLAT[path]):
            sentence = m.group(0).strip()
            if not MEASURE.search(sentence):
                continue
            check("%s: no measurement is claimed re-derivable here" % REL[path],
                  bool(NEGATION.search(sentence)),
                  "%s says %r, and no corpus or harness is in this repository"
                  % (REL[path], sentence[:200]))
        for stray in re.findall(r"\b(?:bench|demo)/[\w./-]+", FLAT[path]):
            check("%s: no path into a directory that was not published" % REL[path],
                  False,
                  "%s names %s and that directory is not part of this repository"
                  % (REL[path], stray))
        for m in re.finditer(r"[^.]*\b(?:CI|continuous integration|workflow)\b[^.]*",
                             FLAT[path]):
            sentence = m.group(0).strip()
            if not re.search(r"\bworkflow|\bCI\b", sentence):
                continue
            denies = re.search(r"no CI workflow|is no CI|without CI|no workflow",
                               sentence, re.I)
            check("%s: what it says about CI matches the tree" % REL[path],
                  not (denies and CI_PRESENT),
                  "%s says %r while this tree carries %r"
                  % (REL[path], sentence[:160],
                     [w.relative_to(REPO).as_posix() for w in WORKFLOWS]))


# -------------------------------------------------------------- self-reported
SELF_RX = re.compile(r"check_docs(?:\.py)?[^.]{0,120}?(\d+) checks|"
                     r"(\d+) checks[^.]{0,120}?check_docs", re.I)


def self_claims():
    return [(p, m) for p in DOCS for m in SELF_RX.finditer(FLAT[p])]


def self_pass(total):
    for path, m in self_claims():
        stated = m.group(1) or m.group(2)
        eq("%s: the stated check count" % REL[path], stated, str(total), REL[path])


def main():
    for name in REQUIRED:
        check("the sweep covers %s" % name,
              (REPO / name) in DOCS,
              "%s is named as a document of this project and the sweep did not "
              "find it" % name)
    claim_pass()
    import_pass()
    link_pass()
    svg_pass()
    code_pass()
    honesty_pass()
    total = PASSED + len(FAILURES) + len(self_claims())
    self_pass(total)

    print("documents swept (%d):" % len(DOCS))
    for path in DOCS:
        print("  " + REL[path])
    print()
    print("derived from the tree:")
    print("  catalogue %d, detectors %d, unreached %d %s"
          % (CATALOGUE, len(FAMILIES), len(UNREACHED), UNREACHED))
    print("  scoring %d, advice-only %d, demoted keys %d (%d report, %d style)"
          % (len(SCORING_FAMS), len(ADVICE_FAMS), len(DEMOTED),
             len(REPORT_ONLY), len(STYLE_ONLY)))
    print("  formats %d (%d plain, %d zip, %d notebook), bands %s"
          % (len(ALL_EXT), len(PROSE_EXT), len(OFFICE_EXT), len(NOTEBOOK_EXT),
             "/".join(BAND_NAMES)))
    print("  version %s, thresholds %d default %d strict"
          % (VERSION, DEFAULT_THRESHOLD, STRICT_THRESHOLD))
    if WITH_SUITES:
        print("  %d python tests, %d hook checks, %d together, doctor prints %d [OK]"
              % (PY_TESTS, HOOK_CHECKS, TOTAL_TESTS, DOCTOR_LINES))
    print()
    if FAILURES:
        for label, detail in FAILURES:
            print("FAIL  %s" % label)
            print("      %s" % detail)
        print()
        print("check_docs: %d of %d checks failed" % (len(FAILURES), total))
        return 1
    print("check_docs: %d checks passed" % total)
    return 0


if __name__ == "__main__":
    sys.exit(main())
