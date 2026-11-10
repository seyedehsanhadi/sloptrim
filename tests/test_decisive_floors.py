"""Score floors and the evidence required to raise them."""
import importlib.util
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]

HUMAN = (
    "The bridge carried coal until 1958. Its six arches were built from stone "
    "quarried two miles upstream, and the mortar has been repointed twice, once "
    "after the flood of 1911 and again in 1963. The parapet on the western side "
    "still shows the marks where a lorry struck it in 1974. Traffic was rerouted "
    "in 1981. Since then the deck has carried only pedestrians and the occasional "
    "farm vehicle, which the county surveyor permits under a weight limit of "
    "three tonnes. An inspection in 2019 found the eastern abutment sound but "
    "recommended pointing work within a decade. The stone came from Ashby quarry, "
    "closed since 1936. Matching it now means either reclaimed material or a "
    "sandstone from Derbyshire that weathers to a slightly different colour, a "
    "compromise the conservation officer accepted in her 2021 report. The parish "
    "council has applied twice for grant funding. The first bid failed on "
    "paperwork, the second is pending. Volunteers clear the drainage channels "
    "each spring, which has slowed the spalling on the north face."
)

EN = (
    "We tried the rewrite twice, and both times it made the latency worse. The first "
    "attempt split the database into a read replica and a write primary, which looked "
    "reasonable on paper and passed review without much argument. In practice the "
    "replication lag meant every query that read its own write came back stale, and the "
    "bug reports took a week to connect to the change because they arrived as individual "
    "complaints rather than as a pattern. The second attempt replaced the ORM with hand "
    "written SQL, which was faster on the benchmark and so much harder to review that we "
    "reverted it after a month, having spent three weeks on it. I still think the original "
    "design was right and that we simply outgrew it. The people who wrote it were not "
    "wrong about the constraints they were working under, and the load we put on it five "
    "years later was not something anyone could have planned for at the time. What I would "
    "do differently is measure first, and keep the old path alive long enough to compare "
    "against it honestly instead of trusting the benchmark harness we had."
)

ZW = "\u200b"
LONG = HUMAN + "\n\n" + EN


def reflowed(text):
    sentences = re.split(r"(?<=[.])\s+", text)
    cuts = (0, 2, 5, 8, len(sentences))
    return "\n\n".join(" ".join(sentences[a:b]) for a, b in zip(cuts, cuts[1:]))


def detector():
    spec = importlib.util.spec_from_file_location(
        "floors_detect", REPO / "scripts" / "detect.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def guarded(metrics):
    """The shipped guard rule: over the threshold, with confidence behind it."""
    return metrics["ai_tell_score"] > 40 and metrics.get("confidence") != "none"


def test_flattery_belongs_to_one_family():
    fired = {k for k in detector().scan("Great question! I can help with that.")
             if not k.startswith("_")}
    assert "48_sycophantic" in fired
    assert "47_chatbot_artifacts" not in fired


def test_a_single_pattern_does_not_carry_a_clean_document():
    scan = detector().scan
    assert not guarded(scan(HUMAN)["_metrics"])
    for text in (
            "Great question! " + HUMAN,
            HUMAN + " See https://example.com/p?utm_source=chatgpt.com for detail.",
    ):
        assert not guarded(scan(text)["_metrics"])


def test_corroborated_patterns_raise_the_floor():
    metrics = detector().scan(
        "Please see the report [Your Name] here: "
        "https://example.com?utm_source=chatgpt.com citeturn0search0"
    )["_metrics"]
    assert metrics["ai_tell_score"] >= 65


def score(text):
    return detector().scan(text)["_metrics"]


def test_one_pasted_zero_width_space_is_not_evidence():
    assert not guarded(score(EN.replace("the database", "the" + ZW + "database")))


def test_a_redacted_xxx_is_not_evidence():
    assert not guarded(score(EN.replace("the original design", "the xxx design")))


def test_reflowed_paragraphs_with_one_zero_width_space_are_not_evidence():
    assert not guarded(score(reflowed(HUMAN).replace("The bridge", "The" + ZW + "bridge", 1)))


def test_a_template_slot_still_floors_a_long_document():
    assert score(LONG.replace("The parish", "[Your Name] The parish", 1))["ai_tell_score"] >= 45


def test_an_ai_tracking_link_still_floors_a_long_document():
    link = LONG + " See https://example.com/p?utm_source=chatgpt.com for detail."
    assert score(link)["ai_tell_score"] >= 45


def test_three_zero_width_characters_still_floor():
    marked = (LONG.replace("The bridge", "The" + ZW + "bridge", 1)
              .replace("The stone", "The" + ZW + "stone", 1)
              .replace("Volunteers", "Volun" + ZW + "teers", 1))
    assert score(marked)["ai_tell_score"] >= 45


def test_one_zero_width_character_does_not_corroborate_a_slot():
    marked = (LONG.replace("The bridge", "The" + ZW + "bridge", 1)
              .replace("The parish", "[Your Name] The parish", 1))
    assert 45 <= score(marked)["ai_tell_score"] < 65


def test_a_zero_width_character_with_a_homoglyph_stays_flagged():
    marked = (LONG.replace("The bridge", "The" + ZW + "bridge", 1)
              .replace("quarried", "qu\u0430rried", 1))
    assert guarded(score(marked))


def test_a_template_slot_that_contains_xxx_still_floors():
    assert score(LONG + " Regards, [Your xxx]")["ai_tell_score"] >= 45


def test_bracketed_citation_keys_are_not_template_slots():
    cited = LONG + " The format follows [RFC2119] and [ISO-8601]; see [UNICODE] and [NII]."
    result = detector().scan(cited)
    assert "63_placeholder_text" not in result
    assert not guarded(result["_metrics"])


@pytest.mark.parametrize("slot", [
    "[COMPANY]", "[COMPANY NAME]", "[YOUR NAME]", "[DEAR HIRING MANAGER]",
    "[CANDIDATE]", "[TODO]", "[XX]", "[START DATE]",
])
def test_an_all_caps_slot_still_floors_a_long_document(slot):
    result = detector().scan(LONG + " Regards, " + slot)
    assert "63_placeholder_text" in result
    assert result["_metrics"]["ai_tell_score"] >= 45
