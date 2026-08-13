#!/usr/bin/env python3
"""validation_corpus.py: a fixed calibration pair for detect.py.

One set was written by people, the other by language models. The separation test
checks that the instrument still tells those two fixed sets apart, which is how a
calibration fixture works. It is not evidence that a score identifies who wrote any
other document, and nothing here should be read that way. See ETHICS.md.
"""
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

DETECT = Path(__file__).resolve().parent.parent / "scripts" / "detect.py"


def detect(t: str) -> dict:
    r = subprocess.run([sys.executable, str(DETECT)], input=t,
                       capture_output=True, text=True, encoding="utf-8")
    return json.loads(r.stdout)


HUMAN = {
 "h_factual_short": (
   "Balsa is a fast-growing tree native to Central and South America. Its wood is "
   "light because the cells are large and thin-walled. A cubic metre of dried balsa "
   "weighs about 160 kilograms, roughly a fifth of oak."),
 "h_factual_long": (
   "Balsa is a fast-growing tree native to Central and South America. Its wood is light "
   "because the cells are large and thin-walled, with much of the volume given over to air. "
   "A cubic metre of dried balsa weighs about 160 kilograms, roughly a fifth of oak. "
   "Builders of model aircraft favoured it for this reason. During the Second World War the "
   "de Havilland Mosquito used balsa cores in its plywood skin, which kept the airframe light "
   "and stiff. The tree reaches harvestable size in about five years. Plantations in Ecuador "
   "supply most of the world market today. Because the wood dents easily, furniture makers "
   "rarely use it."),
 "h_opinion_short": (
   "I gave up on the standing desk after three weeks. My back felt fine; my feet did not. "
   "The trick nobody tells you is that you still need a stool."),
 "h_technical_doc": (
   "The parser reads one token at a time. If it sees an opening brace it pushes a new scope "
   "onto the stack. Closing braces pop it. Errors bubble up as exceptions, which the caller "
   "catches and reports with a line number."),
 "h_classic_prose": (
   "It was the best of times, it was the worst of times. People walked the streets at night "
   "without fear, and the lamps burned low. A man could lose himself in the crowd and be "
   "glad of it."),
 "h_news_lede": (
   "A water main broke on Tuesday morning, flooding two blocks of downtown and closing the "
   "library until noon. City crews reached the site within an hour. No injuries were reported. "
   "The mayor said repairs would cost about forty thousand dollars."),
}

AI = {
 "ai_slop_short": (
   "In today's fast-paced world, leveraging cutting-edge solutions is essential. By fostering "
   "collaboration and driving innovation, teams unlock unprecedented value. Ultimately, the "
   "possibilities are endless."),
 "ai_slop_long": (
   "In today's rapidly evolving digital landscape, artificial intelligence stands as a "
   "testament to human ingenuity. By leveraging cutting-edge algorithms, fostering "
   "collaboration, and driving innovation, organizations can unlock unprecedented value. "
   "It's worth noting that this transformative journey, while challenging, paves the way for "
   "a brighter future. These powerful tools are reshaping how we work, highlighting the "
   "importance of adaptation and underscoring the need for continuous learning. In conclusion, "
   "the future is bright, and exciting times lie ahead."),
 "ai_encyclopedic": (
   "The Eurasian otter stands as a testament to nature's remarkable adaptability, playing a "
   "vital role in its ecosystem. This fascinating creature showcases an array of behaviors "
   "that underscore its ecological significance, highlighting the intricate balance of "
   "riverine environments and reflecting the broader importance of conservation efforts."),
 "ai_chatbot": (
   "Great question! I'd be happy to help you with that. Here's a comprehensive overview of the "
   "topic. It's important to note that there are several key factors to consider. Let me know "
   "if you'd like me to expand on any section!"),
}


def fmt(name: str, d: dict) -> str:
    m = d["_metrics"]
    pats = sorted((int(k.split("_")[0]) for k in d if not k.startswith("_")))
    return (f"{name:20} score={m['ai_tell_score']:>3} {m['ai_tell_band']:16} "
            f"cv={str(m['length_cv']):>5} sent={m['sentences']:>2} pats={pats}")


def main() -> int:
    print("=== HUMAN (want: low score, clean/light-tells, few/no patterns) ===")
    h_scores = []
    for n, t in HUMAN.items():
        d = detect(t); h_scores.append(d["_metrics"]["ai_tell_score"])
        print(fmt(n, d))
    print("\n=== AI (want: high score, mixed/heavy-tells/pervasive-tells) ===")
    a_scores = []
    for n, t in AI.items():
        d = detect(t); a_scores.append(d["_metrics"]["ai_tell_score"])
        print(fmt(n, d))
    print(f"\nHUMAN max={max(h_scores)}  AI min={min(a_scores)}  "
          f"margin={min(a_scores) - max(h_scores)}")
    print("Ideal: HUMAN max well under 40 (clean/light-tells), AI min above 40.")
    return 0


def test_corpus_separation():
    h = [detect(t)["_metrics"]["ai_tell_score"] for t in HUMAN.values()]
    a = [detect(t)["_metrics"]["ai_tell_score"] for t in AI.values()]
    assert max(h) <= 20, f"human max {max(h)} left the clean band"
    assert min(a) >= 30, f"AI min {min(a)} fell below 30"
    assert min(a) - max(h) >= 15, f"separation margin {min(a) - max(h)} < 15"


def test_windows_encoding_artifacts_are_not_ai_evidence(tmp_path):
    import subprocess
    human = HUMAN["h_technical_doc"]

    plain = detect(human)["_metrics"]

    p = tmp_path / "bom_crlf.md"
    p.write_bytes(b"\xef\xbb\xbf" + human.replace(". ", ".\r\n").encode("utf-8"))
    r = subprocess.run([sys.executable, str(DETECT), str(p)],
                       capture_output=True, text=True, encoding="utf-8")
    m = json.loads(r.stdout)["_metrics"]

    assert m["invisible_chars"] == 0, "leading BOM counted as an invisible char"
    assert m["ai_tell_score"] <= max(plain["ai_tell_score"], 20), (
        f"BOM+CRLF inflated a human file from {plain['ai_tell_score']} "
        f"to {m['ai_tell_score']}"
    )

    smug = detect(human[:40] + "​" + human[40:])["_metrics"]
    assert smug["invisible_chars"] >= 1, "interior zero-width char no longer detected"


if __name__ == "__main__":
    sys.exit(main())
