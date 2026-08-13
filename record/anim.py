"""Draw the animated demonstration for the README, light and dark.

Every hook line, score and millisecond in the picture is read from
record/session.json, which record/session_capture.py produces by firing the real
hooks with the payload shapes Claude Code sends and timing each round trip. The
picture is a recording, not a reconstruction, so it cannot show behaviour the
hooks do not have.

The grey labels beside those lines are narration written here, and they are the only
exempt runs: they carry class="n" and the grey narration colour, nothing else. Every
other run in the picture, the latencies, the event and file names, the scores and the
bands, the flagged pattern names and the prose itself, is re-read by check_recorded()
against record/session.json and the two prose files, and the redraw stops if a run is
not there or if narration strays out of grey.

The prose comes off disk too, and the word-level diff between the draft and the
rewrite is computed with difflib, so what gets struck out is what actually
changed.

    python record/session_capture.py   # re-record
    python record/anim.py              # redraw
"""
import difflib
import io
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(os.path.dirname(HERE), "assets")
CAPTURE = os.path.join(HERE, "session.json")

W, PAD, FS, LH = 800, 26, 12.5, 19.0
CW = FS * 0.6
RAIL = 26
X = RAIL + 24
COLS = int((W - X - PAD - 96) / CW)

LOOP = 13.5
EASE = "cubic-bezier(.22,.61,.36,1)"

T = {
    "light": dict(dim="#8a929c", faint="#b6bcc4", text="#16130F", cut="#E2542B",
                  add="#2f855a", hair="#e6e2db", lit="#fdeee9", user="#0969da"),
    "dark": dict(dim="#79828d", faint="#525b66", text="#EDE8DF", cut="#FF6B3D",
                 add="#68d391", hair="#2a313b", lit="#2a1811", user="#4493f8"),
}


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def cells(s):
    return sum(2 if ord(ch) > 0x2000 else 1 for ch in s)


def words_of(path):
    out = []
    for para in io.open(path, encoding="utf-8").read().split("\n"):
        p = " ".join(para.split())
        if p:
            out += re.findall(r"\S+", p)
        elif out and out[-1] != "\n":
            out.append("\n")
    while out and out[-1] == "\n":
        out.pop()
    return out


def layout(words, top):
    pos, col, row = [], 0, 0
    for w in words:
        if w == "\n":
            pos.append(None)
            col, row = 0, row + 1.35
            continue
        n = cells(w)
        if col and col + n > COLS:
            col, row = 0, row + 1
        pos.append((X + col * CW, top + row * LH))
        col += n + 1
    return pos, row + 1


def wrap(text, width):
    lines, cur = [], ""
    for w in text.split(" "):
        if len(cur) + len(w) + 1 > width:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        lines.append(cur)
    return lines


def pc(t):
    return 100.0 * min(max(t, 0.0), LOOP) / LOOP


def flags_of(context):
    """The pattern names out of a guard line, without the surrounding advice."""
    m = re.search(r"Flagged: (.*?)\. Fix", context, re.S)
    return m.group(1) if m else context


def score_of(event):
    """The score and band exactly as the guard printed them for that file."""
    return re.search(r"\(score (\d+/\w+)\)", event["context"]).group(1)


def unesc(s):
    return s.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")


def prose_path(cap, side):
    return os.path.join(HERE, cap[side])


def recorded_text(cap):
    """Every string the capture licenses, flattened so a drawn run can be looked up."""
    out = []

    def walk(node):
        if isinstance(node, dict):
            if "score" in node and "band" in node:
                out.append("%s/%s" % (node["score"], node["band"]))
            if "ms" in node:
                out.append("%s ms" % node["ms"])
            if "tool" in node and "file" in node:
                out.append("%s(%s)" % (node["tool"], node["file"]))
            walk(list(node.values()))
        elif isinstance(node, list):
            for v in node:
                walk(v)
        else:
            out.append("%s" % node)

    walk(cap)
    for side in ("draft", "fixed"):
        out.append(io.open(prose_path(cap, side), encoding="utf-8").read())
    return "\n".join(out)


def classes(tag):
    m = re.search(r'class="([^"]*)"', tag)
    return set(m.group(1).split()) if m else set()


def check_recorded(svg, c, recorded, path):
    """Stop the redraw unless every run but narration is in the capture."""
    missing, strayed = [], []

    def narration(tag, inner):
        if 'fill="%s"' % c["dim"] not in tag:
            strayed.append(unesc(inner).strip())

    for tag, inner in re.findall(r"(<text\b[^>]*>)(.*?)</text>", svg, re.S):
        for stag, sinner in re.findall(r"(<tspan\b[^>]*>)(.*?)</tspan>", inner, re.S):
            if "n" in classes(stag):
                narration(stag, sinner)
                inner = inner.replace(stag + sinner + "</tspan>", "")
        if "n" in classes(tag):
            narration(tag, inner)
            continue
        for part in inner.split("&#183;"):
            run = unesc(part).strip()
            if run.startswith("> "):
                run = run[2:].strip()
            if run and run not in recorded:
                missing.append(run)
    if strayed:
        raise SystemExit(
            "%s draws narration outside the grey narration colour, where it reads as "
            "recorded output:\n  %s" % (path, "\n  ".join(strayed)))
    if missing:
        raise SystemExit(
            "%s draws text that record/session.json never recorded:\n  %s\nEither draw "
            'the recorded run or mark it narration with class="n" in the grey '
            "narration colour." % (path, "\n  ".join(missing)))


def build(theme, cap):
    c = T[theme]
    ev = {i: e for i, e in enumerate(cap["events"])}
    before = prose_path(cap, "draft")
    after = prose_path(cap, "fixed")
    wb, wa = words_of(before), words_of(after)
    ops = difflib.SequenceMatcher(None, wb, wa, autojunk=False).get_opcodes()
    sb, sa = cap["scores"]["draft"], cap["scores"]["fixed"]

    # Beat times. Setting the scene is quick, because it is only context; the
    # part where the guard reads the file and the text changes under it is the
    # part worth watching, so it gets the room. The latencies printed beside
    # each line are the real measured ones and are not what paces this.
    t = {"session": 0.15, "prompt": 0.6, "sub": 1.05, "write": 1.5, "text": 1.7,
         "say": 2.5, "strike": 3.4, "drop": 5.0, "move": 5.3, "arrive": 5.8,
         "settle": 7.0, "edit": 7.2, "docx": 8.4, "docxsay": 9.0,
         "init": 10.2, "local": 11.4}
    SWEEP, GLIDE = 1.1, 0.9

    y = 60.0
    ys = {}
    ys["session"] = y; y += 25
    ys["prompt"] = y; y += 25
    ys["sub"] = y; y += 32
    ys["write"] = y; y += 24
    text_top = y
    pb, rb = layout(wb, text_top)
    pa, ra = layout(wa, text_top)
    say = wrap(flags_of(ev[3]["context"]), COLS - 12)
    ys["say"] = text_top + max(rb, ra) * LH + 6
    y = ys["say"] + 18 * len(say) + 14
    ys["edit"] = y; y += 32
    ys["docx"] = y; y += 18
    ys["docxsay"] = y; y += 32
    ys["init"] = y; y += 18
    ys["init2"] = y; y += 30
    ys["local"] = y; y += 26
    h = y + 14

    css = ['text{font-family:ui-monospace,Menlo,Consolas,"DejaVu Sans Mono",monospace;'
           'font-size:%gpx}' % FS,
           '.s{font-family:ui-sans-serif,system-ui,"Segoe UI",sans-serif;font-size:11px}',
           '.t{font-size:10px;letter-spacing:.09em}.ms{font-size:10px}',
           'g[class]{transform-box:fill-box}',
           '.sk{transform-box:fill-box;transform-origin:left center}']
    body = []

    def fade(name, a, b=None, hold=0.3):
        if b is None:
            css.append("@keyframes %s{0%%,%.2f%%{opacity:0}%.2f%%,100%%{opacity:1}}"
                       % (name, pc(a), pc(a + hold)))
        else:
            css.append("@keyframes %s{0%%,%.2f%%{opacity:0}%.2f%%,%.2f%%{opacity:1}"
                       "%.2f%%,100%%{opacity:0}}"
                       % (name, pc(a), pc(a + hold), pc(b), pc(b + hold)))
        css.append(".%s{animation:%s %.2fs %s infinite}" % (name, name, LOOP, EASE))

    def rise(name, a):
        css.append("@keyframes %s{0%%,%.2f%%{opacity:0;transform:translateY(5px)}"
                   "%.2f%%,100%%{opacity:1;transform:translateY(0)}}"
                   % (name, pc(a), pc(a + 0.35)))
        css.append(".%s{animation:%s %.2fs %s infinite}" % (name, name, LOOP, EASE))

    roles = []
    for tag, i1, i2, j1, j2 in ops:
        if tag == "equal":
            for k in range(i2 - i1):
                roles.append(("keep", wb[i1 + k], pb[i1 + k], pa[j1 + k], i1 + k))
        else:
            for i in range(i1, i2):
                roles.append(("cut", wb[i], pb[i], pb[i], i))
            for j in range(j1, j2):
                roles.append(("add", wa[j], pa[j], pa[j], j))
    n_b, n_a = max(len(wb), 1), max(len(wa), 1)

    for n, (kind, w, src, dst, ordinal) in enumerate(roles):
        if src is None or dst is None:
            continue
        tl, wid = esc(w), cells(w) * CW - CW * 0.15
        if kind == "keep":
            f = ordinal / n_b
            a, b = t["move"] + f * 0.18, t["move"] + f * 0.18 + GLIDE
            css.append("@keyframes k%d{0%%,%.2f%%{opacity:0;transform:translate(%.1fpx,%.1fpx)}"
                       "%.2f%%,%.2f%%{opacity:1;transform:translate(%.1fpx,%.1fpx)}"
                       "%.2f%%,100%%{opacity:1;transform:translate(%.1fpx,%.1fpx)}}"
                       % (n, pc(t["text"] + f * 0.3), src[0], src[1],
                          pc(t["text"] + f * 0.3 + 0.25), pc(a), src[0], src[1],
                          pc(b), dst[0], dst[1]))
            css.append(".k%d{animation:k%d %.2fs %s infinite}" % (n, n, LOOP, EASE))
            body.append('<g class="k%d"><text textLength="%.1f" lengthAdjust="spacingAndGlyphs" '
                        'fill="%s">%s</text></g>' % (n, wid, c["text"], tl))
        elif kind == "cut":
            f = ordinal / n_b
            s0, d0 = t["strike"] + f * SWEEP, t["drop"] + f * 0.08
            css.append("@keyframes c%d{0%%,%.2f%%{opacity:0;fill:%s;"
                       "transform:translate(%.1fpx,%.1fpx)}"
                       "%.2f%%,%.2f%%{opacity:1;fill:%s;transform:translate(%.1fpx,%.1fpx)}"
                       "%.2f%%,%.2f%%{opacity:1;fill:%s;transform:translate(%.1fpx,%.1fpx)}"
                       "%.2f%%,100%%{opacity:0;fill:%s;transform:translate(%.1fpx,%.1fpx)}}"
                       % (n, pc(t["text"] + f * 0.3), c["text"], src[0], src[1],
                          pc(t["text"] + f * 0.3 + 0.25), pc(s0), c["text"], src[0], src[1],
                          pc(s0 + 0.18), pc(d0), c["cut"], src[0], src[1],
                          pc(d0 + 0.35), c["cut"], src[0], src[1] + 7))
            css.append(".c%d{animation:c%d %.2fs %s infinite}" % (n, n, LOOP, EASE))
            css.append("@keyframes s%d{0%%,%.2f%%{transform:scaleX(0);opacity:0}"
                       "%.2f%%,%.2f%%{transform:scaleX(1);opacity:1}"
                       "%.2f%%,100%%{transform:scaleX(1);opacity:0}}"
                       % (n, pc(s0), pc(s0 + 0.2), pc(d0), pc(d0 + 0.25)))
            css.append(".s%d{animation:s%d %.2fs %s infinite}" % (n, n, LOOP, EASE))
            body.append('<g class="c%d"><text textLength="%.1f" lengthAdjust="spacingAndGlyphs">'
                        '%s</text><rect class="s%d sk" x="0" y="-4" width="%.1f" height="1.4" '
                        'fill="%s"/></g>' % (n, wid, tl, n, wid, c["cut"]))
        else:
            g = ordinal / n_a
            a0 = t["arrive"] + g * 0.45
            css.append("@keyframes a%d{0%%,%.2f%%{opacity:0;fill:%s;"
                       "transform:translate(%.1fpx,%.1fpx)}"
                       "%.2f%%{opacity:1;fill:%s;transform:translate(%.1fpx,%.1fpx)}"
                       "%.2f%%,100%%{opacity:1;fill:%s;transform:translate(%.1fpx,%.1fpx)}}"
                       % (n, pc(a0), c["add"], dst[0], dst[1] + 6,
                          pc(a0 + 0.35), c["add"], dst[0], dst[1],
                          pc(t["settle"]), c["text"], dst[0], dst[1]))
            css.append(".a%d{animation:a%d %.2fs %s infinite}" % (n, n, LOOP, EASE))
            body.append('<g class="a%d"><text textLength="%.1f" lengthAdjust="spacingAndGlyphs">'
                        "%s</text></g>" % (n, wid, tl))

    for k in ("session", "prompt", "sub", "write", "edit", "docx", "docxsay",
              "init", "local"):
        rise("r_" + k, t[k if k != "init2" else "init"])
    fade("fSay", t["say"], t["move"] + 0.3)
    css.append("@keyframes rail{0%,2%{transform:scaleY(0)}18%,100%{transform:scaleY(1)}}")
    css.append(".rail{transform-box:fill-box;transform-origin:top center;"
               "animation:rail %.2fs %s infinite}" % (LOOP, EASE))
    css.append("@media(prefers-reduced-motion:reduce){*{animation:none!important}"
               "g[class^=c],.fSay{opacity:0}}")

    o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %.0f" width="%d" '
         'height="%.0f" role="img" aria-label="A recorded session. The contract arrives at '
         'session start, again on the prompt, and again inside a subagent. A saved file scores '
         '%d and its patterns are named. After the fix the next read is silent at %d. The same '
         'text saved as a .docx scores the same, read out of the zip. Every hook latency is '
         'measured.">' % (W, h, W, h, sb["score"], sa["score"]),
         "<style>%s</style>" % "".join(css),
         '<text x="%d" y="30" fill="%s" class="s t n">RECORDED SESSION &#183; NOTHING HERE WAS '
         "ASKED FOR</text>" % (X, c["dim"]),
         '<line x1="%d" y1="42" x2="%d" y2="42" stroke="%s"/>' % (X, W - PAD, c["hair"]),
         '<rect class="rail" x="%d" y="52" width="3" height="%.1f" rx="1.5" fill="%s"/>'
         % (RAIL, ys["local"] - 46, c["cut"]),
         '<text x="%d" y="30" fill="%s" class="s t" text-anchor="end">sloptrim</text>'
         % (RAIL + 14, c["cut"])]

    def row(key, mark, left, right, ms=None, ltone=None, rtone=None, note=""):
        g = ['<g class="r_%s">' % key,
             '<circle cx="%d" cy="%.1f" r="3" fill="%s"/>' % (X + 4, ys[key] - 4, mark),
             '<text x="%d" y="%.1f" fill="%s">%s</text>'
             % (X + 18, ys[key], ltone or c["text"], left)]
        if right:
            tail = ('<tspan fill="%s" class="n"> &#183; %s</tspan>' % (c["dim"], note)
                    if note else "")
            g.append('<text x="%d" y="%.1f" fill="%s" class="%s" text-anchor="end">%s%s</text>'
                     % (W - PAD - (54 if ms else 0), ys[key], rtone or c["dim"],
                        "s" if rtone else "s n", right, tail))
        if ms:
            g.append('<text x="%d" y="%.1f" fill="%s" class="ms" text-anchor="end">%s ms</text>'
                     % (W - PAD, ys[key], c["faint"], ms))
        g.append("</g>")
        return "".join(g)

    o.append(row("session", c["cut"], "SessionStart", "the writing contract enters context",
                 ev[0]["ms"]))
    o.append(row("prompt", c["user"], "&gt; " + esc(cap["prompt"]), "restated on every prompt",
                 ev[1]["ms"]))
    o.append(row("sub", c["cut"], "SubagentStart", "a subagent gets the same contract",
                 ev[2]["ms"]))
    o.append(row("write", c["add"], "Write(%s)" % ev[3]["file"],
                 "%d/%s" % (sb["score"], sb["band"]), ev[3]["ms"], None, c["cut"]))
    o += body
    o.append('<g class="fSay">')
    for i, ln in enumerate(say):
        o.append('<text x="%d" y="%.1f" fill="%s" class="s">%s%s</text>'
                 % (X, ys["say"] + i * 18, c["cut"],
                    "sloptrim &#183; " if i == 0 else "", esc(ln)))
    o.append("</g>")
    o.append(row("edit", c["add"], "Edit(%s)" % ev[4]["file"],
                 "%d/%s" % (sa["score"], sa["band"]),
                 ev[4]["ms"], None, c["add"], "the guard returns nothing"))
    o.append(row("docx", c["add"], "Write(%s)" % ev[5]["file"],
                 score_of(ev[5]), ev[5]["ms"], None, c["cut"]))
    o.append('<g class="r_docxsay"><text x="%d" y="%.1f" fill="%s" class="s n">'
             "the same text saved as a .docx, read out of the zip</text></g>"
             % (X + 18, ys["docxsay"], c["dim"]))
    o.append(row("init", c["user"], "&gt; /sloptrim init", "", ev[6]["ms"]))
    o.append('<g class="r_init"><text x="%d" y="%.1f" fill="%s" class="s n">'
             "prose contract written to AGENTS.md"
             "</text></g>" % (X + 18, ys["init2"], c["dim"]))
    o.append('<g class="r_local"><text x="%d" y="%.1f" fill="%s" class="s n">no network, no model, '
             "Python standard library only &#183; Linux, Windows, macOS</text></g>"
             % (X, ys["local"], c["dim"]))
    o.append("</svg>")
    return "\n".join(o) + "\n"


def main():
    cap = json.load(io.open(CAPTURE, encoding="utf-8"))
    recorded = recorded_text(cap)
    os.makedirs(ASSETS, exist_ok=True)
    for theme in ("light", "dark"):
        p = os.path.join(ASSETS, "demo-%s.svg" % theme)
        svg = build(theme, cap)
        check_recorded(svg, T[theme], recorded, p)
        io.open(p, "w", encoding="utf-8", newline="\n").write(svg)
        print("wrote %s (%.1f KB)" % (os.path.relpath(p, os.path.dirname(HERE)),
                                      os.path.getsize(p) / 1024))


if __name__ == "__main__":
    main()
