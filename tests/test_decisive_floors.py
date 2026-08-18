"""Score floors and the evidence required to raise them."""
import importlib.util
from pathlib import Path

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
