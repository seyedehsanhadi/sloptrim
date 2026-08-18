"""The writing contract and the detector vocabulary stay in step.

The banned list is read out of the contract itself, so editing either side
alone fails here.
"""
import importlib.util
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LIB = REPO / "hooks" / "sloptrim-lib.js"

# Caught in context rather than as bare words, by 24 and 51.
CONTEXT_ONLY = {"comprehensive", "boast"}


def load_detector():
    path = REPO / "scripts" / "detect.py"
    spec = importlib.util.spec_from_file_location("contract_reach_detect", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def contract_words():
    line = re.search(r"Banned vocabulary \(use plain alternatives\): (.+?)\.'",
                     LIB.read_text(encoding="utf-8"))
    assert line, "the contract no longer states a banned vocabulary"
    words = [re.sub(r"\s*\(.*?\)", "", w).strip()
             for w in line.group(1).split(",")]
    return [w for w in words if w and w not in CONTEXT_ONLY]


def test_every_banned_word_reaches_a_detector_family():
    detector = load_detector()
    words = contract_words()
    assert len(words) >= 25, "the parsed contract vocabulary looks truncated"
    missed = []
    for word in words:
        probe = ("The clerk recorded the %s in the ledger on Tuesday. A second "
                 "entry noted the %s again before the office closed for the "
                 "week. The totals were checked twice." % (word, word))
        fired = {k for k in detector.scan(probe) if not k.startswith("_")}
        if not fired:
            missed.append(word)
    assert not missed, (
        "the contract bans these words and no detector family fires on them, so "
        "the guard cannot enforce the rule it ships: %s" % ", ".join(missed))
