"""test_cjk.py: Chinese text must reach the detectors, and English must not move.

Every assertion here failed before the CJK path existed. The numbers quoted are
the ones measured when the fix was written, so a later change that quietly
reverts the tokenisation fails a test with the reason attached instead of just
disagreeing with the expected value.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
DETECT = REPO / "scripts" / "detect.py"
sys.path.insert(0, str(REPO / "scripts"))

import detect


def run_detect(text: str) -> dict:
    r = subprocess.run(
        [sys.executable, str(DETECT)],
        input=text,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if r.returncode != 0:
        raise RuntimeError(f"detect.py exited {r.returncode}: {r.stderr}")
    return json.loads(r.stdout)


ZH_SLOP = (
    "在当今快速变化的时代，赋能团队变得尤为重要。"
    "通过深度协同与持续创新，组织能够释放前所未有的价值。"
    "让我们携手并进，共同开启新的篇章。"
    "总而言之，未来充满无限可能。"
)


def test_chinese_sentences_split_on_their_own_stops():
    # Stock: one sentence for the whole paragraph, because `.!?` never appears.
    assert detect.split_sentences(ZH_SLOP) == [
        "在当今快速变化的时代，赋能团队变得尤为重要。",
        "通过深度协同与持续创新，组织能够释放前所未有的价值。",
        "让我们携手并进，共同开启新的篇章。",
        "总而言之，未来充满无限可能。",
    ]


def test_chinese_counts_as_words_not_as_one_token():
    # Stock: 5. A run of Chinese is one `\b[\w'-]+\b` match because `\b` does not
    # fire between two CJK characters, so 79 characters read as 5 words and fell
    # below `_SCORE_MIN_WORDS`.
    assert detect.count_words(ZH_SLOP) == 44


def test_a_short_chinese_document_is_no_longer_below_the_floor():
    # The reason above the floor is what makes the score mean anything: stock
    # reports "5 words: too short to score" for this text.
    result = run_detect(ZH_SLOP)
    metrics = result["_metrics"]
    assert metrics["sentences"] == 4
    assert metrics["confidence"] != "none"
    assert "too short to score" not in metrics["confidence_reason"]
    assert metrics["length_cv"] is not None


def test_stops_and_closers_stay_with_their_sentence():
    # `？！` is two stops and one break; the closing quote belongs to the quote.
    assert detect.split_sentences("什么？！") == ["什么？！"]
    assert detect.split_sentences("等等……") == ["等等……"]
    assert detect.split_sentences("他说：“走吧？！”然后走了。") == [
        "他说：“走吧？！”",
        "然后走了。",
    ]


def test_english_inside_chinese_still_breaks():
    # Chinese technical prose carries whole English sentences. Handing the whole
    # document to a Chinese-only splitter left them run together.
    assert detect.split_sentences("用 Python 写的。It runs fast.") == [
        "用 Python 写的。",
        "It runs fast.",
    ]


def test_a_decimal_point_inside_chinese_is_not_a_break():
    assert detect.split_sentences("在 3.5 版本里，这个行为变了。") == ["在 3.5 版本里，这个行为变了。"]


@pytest.mark.parametrize(
    "text, sentences, words",
    [
        ("It's a well-known fact, isn't it?", 1, 6),
        ("Dr. Smith came. Then he left.", 2, 6),
        ("He met Dr. Smith at 3.5 p.m. in the yard.", 1, 12),
    ],
    ids=["apostrophe", "abbreviation", "initials"],
)
def test_english_tokenisation_is_unchanged(text, sentences, words):
    assert len(detect.split_sentences(text)) == sentences
    assert detect.count_words(text) == words


EN_SLOP = (
    "Certainly! Urban beekeeping stands as a compelling testament to the transformative "
    "power of community stewardship, marking a pivotal chapter in how cities reimagine "
    "their relationship with the natural world. Across today's rapidly shifting urban "
    "landscape, these vibrant rooftop apiaries are reshaping how residents cultivate, "
    "harvest, and connect. At its core, the appeal is multifaceted. In conclusion, the "
    "outlook is bright and exciting times lie ahead for this rewarding journey."
)


def test_english_scores_are_byte_identical_under_the_language_gate():
    # The gate keys on CJK codepoints alone. This is the control that says so: it
    # is the same five numbers stock sloptrim 0.9.6 reports for this text, checked
    # by loading the unpatched module beside the patched one. If any of them ever
    # moves, the fix has started changing English output.
    metrics = run_detect(EN_SLOP)["_metrics"]
    assert metrics["ai_tell_score"] == 57
    assert metrics["ai_tell_band"] == "mixed"
    assert metrics["sentences"] == 5
    assert metrics["length_cv"] == pytest.approx(0.673, abs=0.001)
    assert metrics["patterns_flagged"] == 5
