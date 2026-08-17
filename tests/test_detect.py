#!/usr/bin/env python3
"""test_detect.py: exercise scripts/detect.py against known samples."""

from __future__ import annotations
import json
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DETECT = REPO / "scripts" / "detect.py"
SCAN_BUDGET_S = 120

AI_SAMPLE = """\
Certainly! Below is an overview of the topic. Great question, by the way.

Urban beekeeping stands as a compelling testament to the transformative power of community stewardship, marking a pivotal chapter in how cities reimagine their relationship with the natural world. Across today's rapidly shifting urban landscape, these vibrant rooftop apiaries are reshaping how residents cultivate, harvest, and connect, underscoring their crucial role in a robust local food ecosystem.

At its core, the appeal is multifaceted: fostering biodiversity, empowering neighbourhoods, and unlocking a deeper appreciation of pollinators. It is not merely a hobby; it is a movement that leverages small spaces for outsized impact.

While specific details are limited based on available information, it could potentially possibly be argued that such initiatives might have some measurable benefit. Despite challenges typical of emerging practices, the community continues to thrive. In order to fully realize this potential, participants must align with established best practices.

In conclusion, the outlook is bright. Exciting times lie ahead as we delve deeper into this rewarding journey. Let me know if you would like me to expand on any section!
"""

HUMAN_SAMPLE = """\
AI coding assistants can make you faster at the boring parts. Not everything. Definitely not architecture.

They're great at boilerplate: config files, test scaffolding, repetitive refactors. They're also great at sounding right while being wrong. I've accepted suggestions that compiled, passed lint, and still missed the point because I stopped paying attention.

People I talk to land in two camps. Some use it like autocomplete for chores and review every line. Others disable it after it keeps suggesting patterns they don't want.
"""

OPENER_REP = """\
The system handles authentication. The system caches sessions for one hour. The system rotates keys daily.
"""

SYN_CYCLE = """\
The protagonist faces many challenges. The main character must overcome obstacles. The central figure eventually triumphs. The hero returns home.
"""

WORKDAY = "I worked from 9 to 5 yesterday, then went home."
FACTUAL_RANGE = "Temperatures range from 0 to 100 degrees."


NANOTECH_SUBSTRING = """\
Our nanotechnology platform combines several proprietary techniques. \
The strategy is to deliver value to customers without bloating the stack.
"""

PHONE_NUMBER = "Call us at 555-1234 or email support@example.com."
AIRCRAFT_MODEL = "The Boeing 747-400 entered service in 1989."
YEAR_RANGE = "The conflict (1939-1945) reshaped Europe."

CONCRETE_EVIDENCE_SAMPLE = """\
Without concrete evidence that the student used an AI tool, the panel \
declined to act on the accusation.
"""

ECOSYSTEM_PADDING_SAMPLE = """\
The Eurasian magpie is a black-and-white corvid found across Europe and Asia. \
It plays a vital role in its ecosystem and conservation efforts are underway.
"""

NOUN_LIST_NOT_ADJECTIVES = (
    "We bought apples, oranges, bananas, grapes and pears for breakfast."
)

ADJECTIVE_STACK = (
    "They launched a bold, ambitious, transformative, innovative initiative."
)


INLINE_HEADER_LIST = """\
- **User Experience:** The user experience has been significantly improved.
- **Performance:** Performance has been enhanced through optimized algorithms.
- **Security:** Security has been strengthened with end-to-end encryption.
"""

MONOTONY_ONLY = (
    "Step one is to validate. Step two is to route. Step three is to respond."
)

CRAFTING_INFLECTION = (
    "The team is crafting a new strategy that crafts identity."
)

SYN_CYCLE_IRREGULAR_PLURALS = """\
Several companies launched new products this quarter. Other firms followed. \
Many organizations had to retool. Most businesses adapted.
"""

EMOJI_FLAG = "The launch event 🇺🇸 was livestreamed."

ABBREV_COMPANY_SUFFIX = (
    "Acme Inc. announced earnings today. Beta Corp. also reported. "
    "Gamma Ltd. closed flat. Delta Co. missed estimates."
)

MAY_MONTH_NOT_HEDGE = (
    "In May 2025 the team possibly missed the deadline."
)

HEDGE_STACK_REAL = (
    "The policy could possibly affect outcomes somewhat."
)

AI_SELF_ID = "As an AI language model, I cannot provide medical advice."

LEGIT_RANGES = (
    "We drove from Boston to Chicago, and the trip took three days. "
    "The book covers everything from biology to chemistry, and reads well. "
    "Prices range from cheap to expensive, depending on the vendor."
)


WATERMARK_TAG = "Clean human prose." + chr(0xE0041) + chr(0xE0049)
ZW_AND_BIDI = "Hidden" + chr(0x200B) + "word" + chr(0x200E) + chr(0x2060) + "text."
NBSP_SAMPLE = "Two" + chr(0x00A0) + "words" + chr(0x202F) + "spaced oddly."
LONE_TRAILING_NEWLINE = "A single paragraph with a conventional trailing newline.\n"
TRAILING_SPACES_EOF = "Pasted text with stray trailing spaces.   "
EOL_TRAILING_SPACES = "Line one has trailing spaces.   \nLine two is clean."

DEFAULT_IGNORABLE_EXTRAS = "Text" + chr(0x034F) + chr(0x115F) + chr(0xFE0F) + "more."

DIRTY_INPUT = (
    "Cellulose" + chr(0x200B) + " is" + chr(0x00A0) + "dense." + chr(0xE0041) + "   \n\n"
)
RICH_UNICODE = "Density rises with β(1→4) bonds; café 日本語 stays intact."

PLACEHOLDER_SAMPLE = "Reach out to [Your Name] at [INSERT EMAIL] before the demo."
REF_MARKUP_SAMPLE = "Revenue rose oai_citation last year and citeturn0search2 confirms it."
UTM_SAMPLE = "Full writeup at https://example.com/post?utm_source=chatgpt.com today."
UTM_TRAILING_PERIOD = "Read the rest at https://x.com/a?utm_source=chatgpt.com."
UTM_DIFF_DOMAIN = "Visit https://x.com/a?utm_source=chatgpt.com.au for the AU site."
HOMOGLYPH_SAMPLE = "The p" + chr(0x0430) + "ssword field is wr" + chr(0x043E) + "ng."

SHORT_HUMAN_FACTUAL = (
    "Balsa is a fast-growing tree native to Central and South America. Its wood is "
    "light because the cells are large and thin-walled. A cubic metre of dried balsa "
    "weighs about 160 kilograms, roughly a fifth of oak."
)
RHYTHM_ONLY_HUMAN = (
    "Snow covered the high passes. Trucks waited below the ridge. Crews cleared the road slowly."
)
SHORT_SLOP = (
    "In today's fast-paced world, leveraging cutting-edge solutions is essential. By "
    "fostering collaboration and driving innovation, teams unlock unprecedented value. "
    "Ultimately, the possibilities are endless."
)
GENUINE_CYRILLIC = "Москва is the capital of Russia."


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


def test_confidence_counts_catalogue_families_not_detector_keys():
    text = """The survey used several methods. These methods provide information about how residents travel between the river district and the central station on ordinary weekdays. Twelve volunteers counted bicycles at the bridge from six in the morning until the last school bus passed shortly after nine, pausing only when traffic officers closed one lane. At the same time, three clerks checked paper tickets on buses that entered the square, while another clerk recorded delays caused by road repairs near the library. Rain stopped the work briefly. When counting resumed, the team kept the morning and afternoon results separate because school traffic changed the totals after three o'clock, and mixing those periods would have hidden the difference between commuter trips and short journeys made by pupils. The final table lists each observation. It also records the date, location, direction of travel, and weather at the time, giving later readers enough detail to check the arithmetic without relying on the summary. No estimate was added where a count was missing."""
    result = run_detect(text)
    keys = {k for k in result if not k.startswith("_")}
    assert keys == {"32_catalog_leadin", "32_catalog_pivot"}
    assert result["_metrics"]["confidence"] == "low"
    assert "1 scored pattern" in result["_metrics"]["confidence_reason"]


def test_great_question_needs_chatbot_punctuation():
    human = run_detect(
        "The committee debated whether representation was a great question in the "
        "colonies, but the larger issue was taxation. The speaker returned to the "
        "same great question in his closing argument and asked the audience to judge "
        "the evidence rather than his choice of words."
    )
    chatbot = run_detect("Great question! I would be happy to help with that.")
    assert "47_chatbot_artifacts" not in human
    assert "47_chatbot_artifacts" in chatbot


def run_clean(text: str) -> str:
    r = subprocess.run(
        [sys.executable, str(DETECT), "--clean"],
        input=text,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if r.returncode != 0:
        raise RuntimeError(f"detect.py --clean exited {r.returncode}: {r.stderr}")
    return r.stdout


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def ok(msg: str) -> None:
    print(f"PASS  {msg}")


def patterns_in(result: dict) -> set[str]:
    return {k for k in result.keys() if not k.startswith("_")}


def main() -> int:
    if not DETECT.exists():
        fail(f"{DETECT} does not exist")

    ai = run_detect(AI_SAMPLE)
    ai_patterns = patterns_in(ai)
    if len(ai_patterns) < 10:
        fail(f"AI sample flagged only {len(ai_patterns)} patterns, expected >= 10")
    ok(f"AI sample flagged {len(ai_patterns)} patterns")

    must_fire = ["1_ai_vocabulary", "51_copula_avoidance", "47_chatbot_artifacts",
                 "48_sycophantic", "39_generic_positive_end"]
    for p in must_fire:
        if p not in ai:
            fail(f"AI sample did not flag {p} (expected to fire)")
    ok(f"all high-confidence detectors fired on AI sample: {must_fire}")

    human = run_detect(HUMAN_SAMPLE)
    human_patterns = patterns_in(human)
    if human_patterns:
        fail(f"humanized sample flagged unexpected patterns: {sorted(human_patterns)}")
    ok("humanized sample: zero false positives")

    op = run_detect(OPENER_REP)
    if "42_opener_repetition" not in op:
        fail("opener-repetition sample did not flag #42")
    ok("opener-repetition correctly detected")

    syn = run_detect(SYN_CYCLE)
    if "8_synonym_cycling" not in syn:
        fail("synonym-cycling sample did not flag #8")
    ok("synonym-cycling correctly detected")

    wd = run_detect(WORKDAY)
    if "15_false_range" in wd:
        fail("workday phrasing 'from 9 to 5' incorrectly flagged as false range")
    ok("false-range stays quiet on 'from 9 to 5'")

    fr = run_detect(FACTUAL_RANGE)
    if "15_false_range" in fr:
        fail("factual range 'from 0 to 100 degrees' incorrectly flagged")
    ok("false-range stays quiet on factual measurements")

    nano = run_detect(NANOTECH_SUBSTRING)
    if "8_synonym_cycling" in nano:
        fail("synonym-cycling false-positive: substring inside 'nanotechnology' "
             "was counted as the cluster member 'technology'")
    ok("synonym-cycling: substring inside compound word does not trigger")

    phone = run_detect(PHONE_NUMBER)
    if "61_hyphen_for_en_dash" in phone:
        fail("hyphen-range false-positive: phone number '555-1234' flagged as a year range")
    ok("hyphen-range: phone numbers do not trigger")

    aircraft = run_detect(AIRCRAFT_MODEL)
    if "61_hyphen_for_en_dash" in aircraft:
        fail("hyphen-range false-positive: aircraft model '747-400' flagged as a year range")
    ok("hyphen-range: aircraft models do not trigger")

    year = run_detect(YEAR_RANGE)
    if "61_hyphen_for_en_dash" not in year:
        fail("hyphen-range failed to flag '1939-1945' as a year range")
    ok("hyphen-range: legitimate year range '1939-1945' is flagged")

    ce = run_detect(CONCRETE_EVIDENCE_SAMPLE)
    if "26_concrete_evidence" not in ce:
        fail("'without concrete evidence' was not flagged by #26")
    ok("concrete-evidence defense phrase correctly detected")

    ep = run_detect(ECOSYSTEM_PADDING_SAMPLE)
    if "14_ecosystem_padding" not in ep:
        fail("ecosystem padding was not flagged by #14")
    ok("ecosystem padding correctly detected")

    nouns = run_detect(NOUN_LIST_NOT_ADJECTIVES)
    if "6_stacked_adjectives" in nouns:
        fail("stacked-adjectives false-positive: plain noun list "
             "(apples, oranges, bananas, grapes, pears) was flagged")
    ok("stacked-adjectives: plain noun lists do not trigger")

    adj = run_detect(ADJECTIVE_STACK)
    if "6_stacked_adjectives" not in adj:
        fail("stacked-adjectives failed to flag the AI-style chain "
             "'bold, ambitious, transformative, innovative'")
    ok("stacked-adjectives: real AI adjective chains are flagged")

    ih = run_detect(INLINE_HEADER_LIST)
    if "33_inline_header_list" not in ih:
        fail("inline-header list did not flag #33: multi-line list regression")
    ok("inline-header list correctly flagged across all rows")

    mo = run_detect(MONOTONY_ONLY)
    if "40_sentence_monotony" not in mo:
        fail("monotony-only sample did not flag #40")
    actual_flagged = len([k for k in mo if not k.startswith("_")])
    reported = mo["_metrics"]["patterns_flagged"]
    if reported != actual_flagged:
        fail(f"patterns_flagged tally is off: reported {reported}, actual {actual_flagged}")
    ok(f"patterns_flagged tally agrees with the actual flagged count ({reported})")

    crf = run_detect(CRAFTING_INFLECTION)
    if "1_ai_vocabulary" not in crf:
        fail("AI_VOCAB did not flag 'crafts' / 'crafting' inflections")
    ok("AI_VOCAB catches 'crafts' and 'crafting' inflections")

    syn_plural = run_detect(SYN_CYCLE_IRREGULAR_PLURALS)
    if "8_synonym_cycling" not in syn_plural:
        fail("synonym cycling failed on irregular plurals "
             "(companies / firms / organizations / businesses)")
    ok("synonym cycling catches irregular plurals")

    flag = run_detect(EMOJI_FLAG)
    if "57_emojis" not in flag:
        fail("emoji detector missed flag-style regional-indicator emoji")
    ok("emoji detector catches regional-indicator flag emoji")

    may = run_detect(MAY_MONTH_NOT_HEDGE)
    if "54_hedge_stacking" in may:
        fail("hedge-stacking false-positive: 'May 2025' + one hedge was flagged")
    ok("hedge-stacking ignores month 'May'")

    real_stack = run_detect(HEDGE_STACK_REAL)
    if "54_hedge_stacking" not in real_stack:
        fail("hedge-stacking failed to flag a genuine lowercase stack")
    ok("hedge-stacking still catches real lowercase stacks")

    self_id = run_detect(AI_SELF_ID)
    if "47_chatbot_artifacts" not in self_id:
        fail("CHATBOT regex missed 'as an AI language model'")
    ok("CHATBOT catches 'as an AI language model' family")

    lr = run_detect(LEGIT_RANGES)
    if "15_false_range" in lr:
        fail("residual #15 detector fired on plain English 'from X to Y' prose")
    ok("FALSE_RANGE detector cleanly removed, no spurious #15 on legit prose")

    abbrev = run_detect(ABBREV_COMPANY_SUFFIX)
    sentences = abbrev["_metrics"]["sentences"]
    if sentences != 4:
        fail(f"sentence splitter counted {sentences} sentences in a 4-sentence "
             "sample with Inc. / Corp. / Ltd. / Co.: abbreviation set incomplete")
    ok("sentence splitter respects Inc. / Corp. / Ltd. / Co. abbreviations")

    wm = run_detect(WATERMARK_TAG)
    if "62_invisible_chars" not in wm:
        fail("TAG-block watermark characters were not flagged by #62")
    ok("invisible-char detector catches TAG-block watermark characters")

    zw = run_detect(ZW_AND_BIDI)
    if "62_invisible_chars" not in zw:
        fail("zero-width + bidi control characters were not flagged by #62")
    ok("invisible-char detector catches zero-width and bidi controls")

    ns = run_detect(NBSP_SAMPLE)
    if "67_nonstandard_spaces" not in ns:
        fail("non-standard spaces (NBSP / narrow NBSP) were not flagged by #67")
    if "62_invisible_chars" in ns:
        fail("non-standard spaces wrongly flagged under #62 (should be #67)")
    ok("non-standard spaces flag #67, not #62")

    lone = run_detect(LONE_TRAILING_NEWLINE)
    if "68_trailing_whitespace" in lone:
        fail("a single conventional trailing newline was wrongly flagged by #68")
    if lone["_metrics"]["trailing_newlines"] != 1:
        fail("metrics did not report the lone trailing newline (U+000A)")
    ok("lone trailing newline reported in metrics but not flagged by #68")

    ts = run_detect(TRAILING_SPACES_EOF)
    if "68_trailing_whitespace" not in ts:
        fail("stray trailing spaces at EOF were not flagged by #68")
    ok("trailing whitespace at EOF is flagged by #68")

    eol = run_detect(EOL_TRAILING_SPACES)
    if "68_trailing_whitespace" not in eol:
        fail("end-of-line trailing spaces were not flagged by #68")
    ok("end-of-line trailing spaces are flagged by #68")

    di = run_detect(DEFAULT_IGNORABLE_EXTRAS)
    if "62_invisible_chars" not in di:
        fail("category classifier missed non-Cf Default_Ignorable codepoints "
             "(CGJ / Hangul filler / VS-16)")
    ok("classifier catches non-Cf Default_Ignorable codepoints")

    # The input ends in a newline, so the output does: a file that ended in one
    # still should, or nothing can round-trip byte for byte.
    cleaned = run_clean(DIRTY_INPUT)
    if cleaned != "Cellulose is dense.\n":
        fail(f"--clean did not produce pure text, got {cleaned!r}")
    cleaned = cleaned.rstrip("\n")
    rescan = run_detect(cleaned)
    for k in ("62_invisible_chars", "67_nonstandard_spaces", "68_trailing_whitespace"):
        if k in rescan:
            fail(f"--clean output still trips {k}")
    if rescan["_metrics"]["invisible_chars"] != 0 or rescan["_metrics"]["nonstandard_spaces"] != 0:
        fail("--clean output still contains invisible or non-standard-space characters")
    ok("--clean output is pure text with zero invisible/space/whitespace flags")

    if run_clean(RICH_UNICODE) != RICH_UNICODE:
        fail("--clean corrupted legitimate Unicode content")
    ok("--clean preserves legitimate Unicode (math symbols, accents, CJK)")

    family = "\U0001f468‍\U0001f469‍\U0001f467‍\U0001f466"
    for label, s in (
        ("family emoji (ZWJ)", family),
        ("checkmark (VS16)", "✔️"),
        ("Persian (ZWNJ)", "می‌خواهم"),
        ("IPA script-g", "/ɡʊd/"),
    ):
        if run_clean(s) != s:
            fail(f"--clean corrupted {label}: stripped a legitimate joiner/selector/letter")
    ok("--clean preserves emoji ZWJ/VS16 sequences, cursive joiners, and IPA")

    if run_clean("Clean prose.​\U000e0041") != "Clean prose.":
        fail("--clean failed to strip a zero-width + TAG-plane watermark")
    if "payment" not in run_clean("The pаyment link"):
        fail("--clean failed to fold a Cyrillic-in-Latin homoglyph attack")
    ok("--clean still strips zero-width/TAG watermarks and folds homoglyph attacks")

    ph = run_detect(PLACEHOLDER_SAMPLE)
    if "63_placeholder_text" not in ph:
        fail("placeholder text '[Your Name]' / '[INSERT EMAIL]' not flagged by #63")
    ok("placeholder / Mad-Libs text flagged by #63")

    rm = run_detect(REF_MARKUP_SAMPLE)
    if "64_chatbot_ref_markup" not in rm:
        fail("chatbot ref markup 'oai_citation' / 'citeturn0search2' not flagged by #64")
    ok("chatbot reference-markup leak flagged by #64")

    utm = run_detect(UTM_SAMPLE)
    if "65_ai_tracking_params" not in utm:
        fail("'utm_source=chatgpt.com' not flagged by #65")
    ok("AI tracking params flagged by #65")

    utm_dot = run_detect(UTM_TRAILING_PERIOD)
    if "65_ai_tracking_params" not in utm_dot:
        fail("'utm_source=chatgpt.com.' (sentence-ending period) not flagged by #65")
    ok("AI tracking params flagged by #65 at end of sentence (trailing period)")

    utm_au = run_detect(UTM_DIFF_DOMAIN)
    if "65_ai_tracking_params" in utm_au:
        fail("#65 false-positive on 'chatgpt.com.au' (different domain)")
    ok("#65 does not fire on 'chatgpt.com.au' (period that starts a TLD label)")

    hg = run_detect(HOMOGLYPH_SAMPLE)
    if "66_homoglyphs" not in hg:
        fail("mixed-script homoglyphs (Cyrillic а/о in ASCII words) not flagged by #66")
    ok("mixed-script homoglyphs flagged by #66")

    cyr = run_detect(GENUINE_CYRILLIC)
    if "66_homoglyphs" in cyr:
        fail("genuine single-script Cyrillic word wrongly flagged by #66")
    ok("genuine single-script Cyrillic does not trigger #66")

    if run_clean(HOMOGLYPH_SAMPLE) != "The password field is wrong.":
        fail(f"--clean did not fold homoglyphs, got {run_clean(HOMOGLYPH_SAMPLE)!r}")
    ok("--clean folds mixed-script homoglyphs to ASCII")
    if run_clean(GENUINE_CYRILLIC) != GENUINE_CYRILLIC:
        fail("--clean corrupted a genuine single-script Cyrillic word")
    ok("--clean preserves genuine single-script Cyrillic")

    for key in ("ai_tell_score", "ai_tell_band", "passive_voice_ratio"):
        if key not in ai["_metrics"]:
            fail(f"_metrics missing v1.3.0 key '{key}'")
    ai_score = ai["_metrics"]["ai_tell_score"]
    human_score = human["_metrics"]["ai_tell_score"]
    if not (0 <= ai_score <= 100 and 0 <= human_score <= 100):
        fail(f"ai_tell_score out of range (ai={ai_score}, human={human_score})")
    if ai_score <= human_score:
        fail(f"ai_tell_score did not discriminate (ai={ai_score} <= human={human_score})")
    ok(f"ai_tell_score discriminates: AI={ai_score} ({ai['_metrics']['ai_tell_band']}) "
       f"vs human={human_score} ({human['_metrics']['ai_tell_band']})")

    short_human = run_detect(SHORT_HUMAN_FACTUAL)
    sh = short_human["_metrics"]
    if sh["ai_tell_score"] > 40:
        fail(f"short human factual scored {sh['ai_tell_score']} (> 40): rhythm "
             f"saturated the score; band={sh['ai_tell_band']!r}")
    ok(f"short human factual stays low: {sh['ai_tell_score']} ({sh['ai_tell_band']})")

    rhythm_only = run_detect(RHYTHM_ONLY_HUMAN)
    ro = rhythm_only["_metrics"]
    if ro["ai_tell_score"] > 40:
        fail(f"rhythm-only sample scored {ro['ai_tell_score']} (> 40): rhythm "
             "bucket is not capped below the mixed band")
    ok(f"rhythm-only evidence capped at 'light tells' or below: {ro['ai_tell_score']}")

    short_slop = run_detect(SHORT_SLOP)
    ss = short_slop["_metrics"]["ai_tell_score"]
    if ss - sh["ai_tell_score"] < 20:
        fail(f"short slop ({ss}) does not clearly outscore short human "
             f"({sh['ai_tell_score']}) : margin {ss - sh['ai_tell_score']} < 20")
    ok(f"short slop outscores short human by a clear margin: {ss} vs {sh['ai_tell_score']}")

    for s in ("This isn't just a tool, it's a revolution.",
              "AI is not just a trend — it's a paradigm shift.",
              "It's not just a feature, but a philosophy.",
              "No fluff, just results."):
        if "18_not_x_just_y" not in run_detect(s):
            fail(f"#18 missed the not-just framing: {s!r}")
    ok("#18 catches the 'not just X, it's/but Y' family (and 'No X, just Y')")

    for s in ("She is not a teacher, but a researcher who also teaches.",
              "I did not sleep well because of the noise."):
        if "18_not_x_just_y" in run_detect(s):
            fail(f"#18 false-positive on ordinary prose: {s!r}")
    ok("#18 leaves ordinary 'not ... but' prose alone")

    tc = run_detect("It works well. Additionally, it scales. Furthermore, it is fast. "
                    "Moreover, it stays cheap.")
    if "37_transition_cluster" not in tc:
        fail("#37 missed a sentence-level transition cluster in one paragraph")
    ok("#37 catches transition clusters within a flowing paragraph")

    if "37_transition_cluster" in run_detect("However you slice it, the answer is the same."):
        fail("#37 false-positive on a single 'However' opener")
    ok("#37 needs >=2 transition openers (single opener does not fire)")


    url_text = "See москва.рф/index for the archive. Ukrainian слово-play in a sentence."
    if "66_homoglyphs" in run_detect(url_text):
        fail("#66 flagged a single-script-run URL / hyphen compound")
    if run_clean(url_text) != url_text.strip():
        fail("--clean corrupted genuine non-Latin runs in a mixed token")
    ok("#66 leaves single-script runs (URLs, compounds) untouched")

    attack = "The pаyment sсript runs silently."
    if "66_homoglyphs" not in run_detect(attack):
        fail("#66 missed confusables embedded inside Latin letter runs")
    if "payment script" not in run_clean(attack):
        fail("--clean did not fold embedded confusables back to ASCII")
    ok("#66 still folds confusables embedded in Latin runs")

    typeset = ("In the summer of 1943, the works committee reviewed the ledgers. "
               "“We cannot say,” the chairman wrote, “whether the shortfall was "
               "crucial or merely careless.” The audit of 1939-1945 records took four "
               "months; the landscape of wartime accounting offered no easy answers. It was "
               "a slow business. Clerks checked each entry twice, and the committee met on "
               "Thursdays.")
    ts = run_detect(typeset)["_metrics"]
    if ts["ai_tell_score"] > 20:
        fail(f"typeset human prose scored {ts['ai_tell_score']}: #60/#61 still "
             "carry score weight or vocab term saturates")
    ok(f"typeset human prose stays clean: {ts['ai_tell_score']} ({ts['ai_tell_band']})")

    leaky = ("Please see the report [Your Name] here: "
             "https://example.com?utm_source=chatgpt.com citeturn0search0")
    lk = run_detect(leaky)["_metrics"]
    if lk["ai_tell_score"] < 65:
        fail(f"two+ decisive leaks scored only {lk['ai_tell_score']}: decisive floor missing")
    ok(f"decisive floor holds: leak trio scores {lk['ai_tell_score']}")

    zig = ("Short comes first. Then a much longer sentence follows it with extra clauses "
           "attached. Brief again. After that another extended sentence stretches out across "
           "many additional words here. Tiny one. Following it one more lengthy sentence "
           "continues the mechanical pattern onward again. Small next. Then the final extended "
           "sentence completes the alternating rhythm perfectly once more.")
    if "41_mechanical_alternation" not in run_detect(zig):
        fail("#41 missed a perfect short-long-short zigzag")
    if "41_mechanical_alternation" in run_detect(HUMAN_SAMPLE):
        fail("#41 false-positive on irregular human rhythm")
    ok("#41 catches mechanical alternation, ignores irregular rhythm")

    if "2_model_dialect" in run_detect("A genuinely useful tool for editing."):
        fail("#2 fired on a single common dialect word")
    dialect = run_detect("This genuinely fascinating tool is a game-changer that will "
                         "supercharge your workflow.")
    if "2_model_dialect" not in dialect:
        fail("#2 missed a multi-hit dialect passage")
    if not any("claude-dialect" in s for s in dialect["2_model_dialect"]["samples"]):
        fail("#2 samples lack dialect attribution")
    ok("#2 model-dialect: 2+ hit gate and attribution work")


    if "51_copula_avoidance" in run_detect("Advanced features are one menu deep."):
        fail("#51 false-positive on the plural noun 'features'")
    for s in ("The gallery features four rooms.", "The museum features a new wing."):
        if "51_copula_avoidance" not in run_detect(s):
            fail(f"#51 stopped catching verb-'features': {s!r}")
    ok("#51 distinguishes verb 'features' from the plural noun")

    if "1_ai_vocabulary" in run_detect("They target carbon capture at industrial scale."):
        fail("#1 false-positive on the technical noun 'carbon capture'")
    if "1_ai_vocabulary" not in run_detect("The film captures the essence of the era."):
        fail("#1 stopped catching 'captures the essence'")
    ok("#1 flags 'captures the essence', not 'carbon capture'")

    for s in ("Unlock the full potential of your team.",
              "We navigate the complexities of tax law.",
              "This is a testament to the power of teamwork.",
              "Stay ahead of the curve with our platform.",
              "Whether you are a beginner or a pro, read on.",
              "The key takeaway is that testing saves time.",
              "Turn challenges into opportunities today."):
        if "69_canonical_slop" not in run_detect(s):
            fail(f"#69 missed a canonical slop phrase: {s!r}")
    for s in ("The plumber replaced the washer and the leak stopped.",
              "I unlocked the door and went inside.",
              "She integrated the survey data into the report."):
        if "69_canonical_slop" in run_detect(s):
            fail(f"#69 false-positive on ordinary human prose: {s!r}")
    ok("#69 catches canonical slop phrases, leaves ordinary prose alone")


    if "64_chatbot_ref_markup" in run_detect("The navlistview renders contentReferences."):
        fail("#64 false-positive on 'navlistview' / 'contentReferences'")
    ok("#64 does not fire on ordinary words containing the token")

    if "63_placeholder_text" in run_detect("See [1] and the [date] of birth field [link]."):
        fail("#63 false-positive on '[date]' / '[link]' / numeric citation '[1]'")
    ok("#63 does not fire on ordinary brackets / numeric citations")

    if "63_placeholder_text" in run_detect(
            "Use [RAID](https://github.com/liamdugan/raid), licensed [MIT][1]."):
        fail("#63 false-positive on markdown links '[RAID](...)' / '[MIT][1]'")
    if "63_placeholder_text" not in run_detect("Sincerely, [Your Name]"):
        fail("#63 stopped catching a genuine placeholder slot")
    ok("#63 ignores markdown links but still catches real placeholder slots")

    if "65_ai_tracking_params" in run_detect("Visit utm_source=chatgpt.community today."):
        fail("#65 false-positive on 'chatgpt.community'")
    ok("#65 right-bounded: 'chatgpt.community' does not match")

    big = "not only " + "a" * 80000 + " but also"
    t0 = time.time()
    run_detect(big)
    if time.time() - t0 > SCAN_BUDGET_S:
        fail(f"scanner too slow on long unpunctuated input: O(n^2) regression "
             f"({time.time() - t0:.1f}s against a {SCAN_BUDGET_S}s budget)")
    ok("long unpunctuated input scans quickly (no O(n^2) freeze)")

    for label, payload in (
        ("fenced code", "```x\n" * 20000),
        ("bare newlines", "text" + "\n" * 100000),
        ("table rows", "| a | b |\n" * 60000),
        ("badge lines", "[![x](y)](z)\n" * 40000),
        ("inline headers", "- **X:** y\n" * 40000),
        ("comma flood", "a, " * 180000),
        ("word-and flood", "big and " * 90000),
    ):
        t0 = time.time()
        run_detect(payload)
        if time.time() - t0 > SCAN_BUDGET_S:
            fail(f"scanner too slow on repetitive {label}: O(n^2) regression "
                 f"({time.time() - t0:.1f}s against a {SCAN_BUDGET_S}s budget)")
    ok("repetitive fences/newlines/tables/badges/headers scan without a quadratic blow-up")

    for text in (AI_SAMPLE, HUMAN_SAMPLE, SHORT_SLOP):
        results = {json.dumps(run_detect(text), sort_keys=True) for _ in range(5)}
        if len(results) != 1:
            fail("scan is non-deterministic: same input gave different output")
    ok("scan is deterministic across repeated runs")

    for k, v in ai.items():
        if k.startswith("_"):
            continue
        keys = set(v.keys())
        expected = {"label", "count", "samples"}
        if keys != expected:
            fail(f"entry {k} has keys {keys}, expected {expected}")
    ok("output schema is consistent across all entries")

    metrics = ai.get("_metrics")
    if not isinstance(metrics, dict):
        fail("_metrics block missing from output")
    for key in ("sentences", "length_cv", "has_short_sentence", "patterns_flagged"):
        if key not in metrics:
            fail(f"_metrics missing key '{key}'")
    ok(f"_metrics block well-formed: {metrics}")

    print()
    print("All detector tests passed.")
    return 0


def test_detector_suite():
    assert main() == 0


if __name__ == "__main__":
    sys.exit(main())
