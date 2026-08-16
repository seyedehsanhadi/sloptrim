#!/usr/bin/env python3
"""detect.py: deterministic scan for sloptrim's AI-writing patterns. Reads stdin or a file argument, emits JSON, or scrubbed text with --clean."""

from __future__ import annotations
import json
import os
import collections
import re
import statistics
import sys
import unicodedata

MAX_SAMPLES = 3

# ----------------------------------------------------------- lexical patterns
AI_VOCAB = (
    r"\b(?:delve|"
    r"delves|delving|tapestry|pivotal|vibrant|meticulous|meticulously|"
    r"testament|underscore|underscores|underscoring|intricate|intricacies|"
    r"interplay|garner|garners|garnered|bolster|bolsters|bolstered|foster|"
    r"fosters|fostered|fostering|showcase|showcases|showcasing|emphasize|"
    r"emphasizes|emphasizing|enduring|crucial|enhance|enhances|enhancing|"
    r"renowned|groundbreaking|profound|multifaceted|leverage|leverages|"
    r"leveraging|utilize|utilizes|utilizing|facilitate|facilitates|"
    r"encompasses|encompassing|spearhead|spearheads|harness|harnesses|"
    r"elevate|elevates|streamline|streamlines|robust|seamless|seamlessly|"
    r"effortless|effortlessly|revolutionize|revolutionizes|revolutionizing|"
    r"game-changing|buzzworthy|"
    r"holistic|synergy|paradigm|transformative|unprecedented|myriad|plethora|"
    r"endeavor|endeavors|navigate|navigates|embark|embarks|embarked|"
    r"kaleidoscope|symphony|realm|landscape|journey|quest|odyssey|roadmap|"
    r"reimagine|reimagines|reimagining|unleash|unleashes|unlock|unlocks|"
    r"unravel|unravels|weave|weaves|weaving|illuminate|illuminates|"
    r"illuminating|elucidate|elucidates|transcend|transcends|transcending|"
    r"resonate|resonates|resonating|reverberate|reverberates|reverberating|"
    r"embody|embodies|embodying|grapple|grapples|grappling|empower|empowers|"
    r"empowering|deepen|deepens|deepening|cultivate|cultivates|cultivating|"
    r"captures? the (?:essence|spirit|imagination|heart|magic)|"
    r"capturing the (?:essence|spirit|imagination|heart|magic)|"
    r"curate|curates|curated|craft|crafts|"
    r"crafted|crafting)\b"
)

ING_TAIL = (
    r",\s+(?:highlighting|reflecting|symbolizing|emphasizing|underscoring|"
    r"showcasing|fostering|cultivating|encompassing|signaling|demonstrating|"
    r"illustrating|representing|suggesting|indicating|reinforcing|leveraging|"
    r"aligning|embodying|exemplifying|epitomizing)\b"
)

PROMO = (
    r"\b(?:nestled|breathtaking|must-visit|stunning|picturesque|charming|"
    r"idyllic|vibrant community|rich cultural heritage|in the heart of|"
    r"world-class|top-tier|unparalleled|premier|leading|"
    r"esteemed organization|valuable asset|passion for excellence|"
    r"proven track record|results-oriented|wealth of experience|"
    r"dynamic team|fast-paced environment|deeply passionate|"
    r"perfectly situated|(?:close|tight)-knit team|"
    r"i am excited to (?:apply|bring)|uniquely positioned to)\b"
)

DIFF_ANCHORED = (
    r"\b(?:unlike the (?:previous|prior|old|earlier) (?:version|release|"
    r"implementation|approach)|"
    r"(?:the|this) (?:latest |new )?(?:update|release|version|change|patch|"
    r"design|redesign) "
    r"(?:adds|introduces|brings|delivers|includes|provides|improves)|"
    r"(?:has|have) been (?:updated|refactored|improved|enhanced|changed) to|"
    r"(?:previously|formerly),? (?:the|this|it|users?) [^.,\n]{0,40} "
    r"(?:now|but now)|"
    r"(?:wasn'?t|weren'?t) there before|"
    r"we(?:'ve| have) (?:now )?(?:added|removed|replaced|refactored|migrated))\b"
)

VAGUE_ATTR = (
    r"\b(?:experts (?:argue|believe|say|claim|note|suggest)|"
    r"industry (?:reports|observers|analysts)|"
    r"observers have (?:cited|noted)|some critics argue|"
    r"researchers have found|studies suggest|it is widely believed)\b"
)

CHALLENGES = (
    r"\b(?:despite (?:these|its|the) (?:challenges|obstacles)|"
    r"challenges? (?:and|&) (?:future )?(?:prospects?|outlook|legacy)|"
    r"continues? to thrive|typical of (?:emerging|urban|modern)|"
    r"faces (?:several|many|numerous) challenges)\b"
)

COPULA_AVOID = (
    r"\b(?:serves as|stands as|functions as|acts as|represents (?:a|the)|"
    r"marks (?:a|the)|boasts|"
    r"features (?:a|an|the|\d+|one|two|three|four|five|six|seven|eight|nine|"
    r"ten|several|multiple|numerous|over|more than)\b|"
    r"offers a|refers to)\b"
)

NEG_PARALLEL = (
    r"\b(?:it'?s not (?:just|merely) (?:about|a|an)|"
    r"not only [^.\n]{2,40}? but (?:also )?|"
    r"it doesn'?t just [^.,]{2,40} it)\b"
)
TAILING_NEG = r",\s+no (?:guessing|waste|wasted motion|hassle|fluff|stress|jargon)\b"

# -------------------------------------------------------- formatting patterns
BOLD = r"\*\*[^*\n]{1,60}\*\*"

INLINE_HEADER = r"(?:^|\n)[ \t*\-]*\*\*[^*]+(?::\*\*|\*\*[ \t]*:)"

TITLE_CASE_HEADING = re.compile(
    r"^(#{1,6})\s+([A-Z][^\n]+)$", re.MULTILINE
)

EMOJI = re.compile(r"[\U0001F1E6-\U0001F1FF\U0001F300-\U0001FAFF☀-➿]")

CURLY = r"[‘’“”]"

# -------------------------------------------------------- assistant artefacts
CHATBOT = (
    r"\b(?:I hope this helps|great question|certainly(?=!)|of course(?=!)|"
    r"you(?:'?re| are) absolutely right|let me know if you|would you like me to|"
    r"feel free to (?:ask|reach out)|happy to help(?=[!.]|$)|"
    r"(?:here|below) is (?:a|an|the)?\s*(?:overview|summary|rundown|recap|brief(?!\s+\w))|"
    r"here (?:are|'?s) (?:a few|three|two|some) (?:options|drafts|versions|variations)|"
    r"here (?:is|'?s) a draft(?: you can use)?|"
    r"depending on the (?:vibe|tone|style) (?:of|you)|"
    r"i hope (?:this email )?finds you well|"
    r"as an? (?:AI|LLM|AI assistant|AI language model|"
    r"large language model|language model))\b"
)

CUTOFF = (
    r"\b(?:as of my (?:last )?(?:training|knowledge)|up to my (?:last )?"
    r"(?:training|knowledge)|while specific details are (?:limited|scarce|"
    r"not (?:extensively|widely) documented)|based on (?:the )?available "
    r"information|as of my (?:knowledge )?cutoff)\b"
)

SYCOPHANTIC = (
    r"\b(?:you(?:'?re| are) absolutely right\b|"
    r"(?:great question|excellent point|"
    r"what a (?:thoughtful|great|wonderful|fantastic) question|"
    r"that'?s an? (?:great|wonderful|fantastic|brilliant|excellent) "
    r"(?:point|question))[!.,])"
)

FILLER = (
    r"\b(?:in order to|due to the fact that|at this point in time|"
    r"in the event that|has the ability to|it is important to note that|"
    r"it should be mentioned that|needless to say)\b"
)

HEDGES = (
    r"\b(?:may|might|could|possibly|potentially|arguably|perhaps|"
    r"seems?(?:\s+(?:to|like))?|appears?\s+to|somewhat|relatively|fairly|"
    r"kind of|sort of)\b"
)

GENERIC_END = (
    r"\b(?:the future looks bright|exciting times lie ahead|"
    r"journey toward excellence|step in the right direction|"
    r"(?:the )?(?:outlook|future)(?: for [^.\n]{0,50})? (?:is|looks|remains) bright|"
    r"well[ -]positioned for (?:whatever comes next|the future|the road ahead))\b"
)

HYPHEN_CLICHE = (
    r"\b(?:mission-critical|battle-tested|out-of-the-box|enterprise-grade|"
    r"best-of-breed|plug-and-play|industry-leading|purpose-built|"
    r"bleeding-edge|turn-key|value-added|first-class|laser-focused|"
    r"tried-and-true|ready-made|best-in-class|future-proof|cutting-edge|"
    r"results-driven|customer-centric|state-of-the-art|next-generation|"
    r"forward-thinking|user-friendly|data-driven|cross-functional|"
    r"client-facing|end-to-end)\b"
)

AUTHORITY_TROPE = (
    r"\b(?:here'?s the thing|make no mistake|the truth is|let'?s be honest|"
    r"the simple fact is|at its core|what really matters|more than anything|"
    r"at the end of the day|the bottom line is|in reality|fundamentally,|"
    r"the real question is|the heart of the matter|the deeper issue|"
    r"when you get down to it|when all is said and done)\b"
)

SIGNPOSTING = (
    r"\b(?:let'?s (?:dive|delve|explore)|let'?s break (?:this|it) down|"
    r"here'?s what you need to know|without further ado|now let'?s look at|"
    r"buckle up|stay with me|"
    r"(?:are you )?ready to dive in(?:to)?)\b"
)

CATALOG_LEADIN = (
    r"\b(?:used|uses|employs?|employed|relied? on|utilizes?)\s+"
    r"(?:several|various|a\s+number\s+of|multiple|different|many|numerous)"
    r"\s+\w+"
)
CATALOG_PIVOT = (
    r"\bThese\s+(?:\w+\s+)?(?:provide|offer|give|reveal|show|allow|enable|help)"
    r"\s+(?:information|insight|understanding|details|data)\b"
)

EMPTY_PIVOT = (
    r"\b(?:it'?s worth noting that|it'?s worth mentioning that|"
    r"it bears (?:noting|mentioning) that|"
    r"one thing to (?:consider|keep in mind) is|"
    r"it is interesting to note that|a key consideration is|"
    r"a point to highlight is)\b"
)

COMPULSIVE_CONCLUSION = (
    r"(?:^|\n)[ \t]*(?:in conclusion|overall|in summary|to summarize|"
    r"to conclude|all in all|in essence|ultimately)[,\s]"
)

OUTCOME_SPECULATION = (
    r",\s+(?:raising questions about|prompting reflection on|"
    r"sparking debate about|with broader implications for|"
    r"reshaping our understanding of|paving the way for|"
    r"signaling a shift toward)\b"
)

SIMPLE_YET = (
    r"\bsimple yet (?:effective|powerful|profound|elegant|"
    r"transformative|sophisticated|beautiful)\b"
)

# Multi-word significance inflation (catalogue section 10). The single words
# live in AI_VOCAB; these are the closed collocations, which age more slowly.
# ------------------------------------------------ significance and notability
SIGNIFICANCE_INFLATION = (
    r"\b(?:stands|serves|stood|served) as (?:a |an |the )?"
    r"(?:testament|reminder|symbol|beacon|cornerstone|bridge|gateway|hallmark)\b"
    r"|\b(?:underscor|highlight|emphasis)(?:es|ing|ed) (?:its|the|their|his|her) "
    r"(?:importance|significance|enduring|central|vital|crucial|pivotal|key) ?\w*\b"
    r"|\breflect(?:s|ing|ed)? (?:a )?broader (?:trend|shift|pattern|movement|change)\b"
    r"|\bmark(?:s|ing|ed) a (?:turning point|milestone|watershed|new (?:chapter|era))\b"
    r"|\bsymboliz(?:es|ing)|\bsymbolis(?:es|ing)\b(?=[^.]{0,40}\b(?:ongoing|enduring|lasting)\b)"
    r"|\bset(?:s|ting)? the stage for\b"
    r"|\bleft? an indelible mark\b"
    r"|\bplay(?:s|ed|ing)? (?:a |an )(?:crucial|pivotal|vital|key|central|significant) role\b"
    r"|\b(?:has|have) (?:shaped|sparked|come to (?:define|symbolize|symbolise))\b"
)

# Notability name-dropping (catalogue section 11): a credit verb plus two or
# more named outlets in one breath, or a raw follower count as evidence.
NOTABILITY_LIST = (
    r"\b(?:featured|profiled|covered|cited|mentioned|highlighted|showcased) "
    r"(?:in|by)\b[^.]{0,120}?,[^.]{0,120}?\band\b[^.]{0,60}?[A-Z]"
    r"|\bactive (?:social media|online|digital) presence\b"
    r"|\bstrong (?:digital|online|social) presence\b"
    r"|\b(?:more than |over |upwards of )?[\d,.]+[KkMm]? followers\b"
    r"|\bwidely (?:covered|reported|featured) (?:by|in)\b"
    r"|\bindependent coverage\b"
)

# Closed collocations that survive vocabulary rotation, grouped by the move they
# make rather than by the words they use.
# -------------------------------------------------------- closed collocations
FAUX_INSIGHT = (
    r"\bhere(?:'s| is) what (?:nobody|no one|most people|they don't)\b"
    r"|\bwhat (?:most|so many) people get wrong\b"
    r"|\bthe (?:part|thing|bit) (?:that )?(?:everyone|most people|nobody) (?:misses|gets wrong|overlooks)\b"
    r"|\bnobody (?:talks|tells you) about\b"
    r"|\bthe (?:dirty )?secret (?:that )?(?:nobody|no one) (?:tells|mentions)\b"
    r"|\bhere(?:'s| is) the (?:uncomfortable|inconvenient|hard) (?:truth|part)\b"
)

DEFINITIONAL_METAPHOR = (
    r"\b(?:is|are|was|were|remains|becomes) (?:the |a )?"
    r"(?:language|currency|architecture|heartbeat|lifeblood|DNA|backbone|bedrock|"
    r"engine|scaffolding|connective tissue) of\b"
)

COLON_REVEAL = (
    # Line-local whitespace only. A \s* here would cross newlines and retry at
    # every position, which is quadratic on newline-heavy input.
    r"(?m)^[ \t]{0,8}(?:The (?:best part|kicker|catch|twist|result|"
    r"real (?:reason|problem|question))|Plot twist|Here(?:'s| is) the thing|"
    r"The bottom line)[ \t]{0,4}:"
)

CHAT_RESIDUE = (
    r"\bto (?:answer|address) your question\b"
    r"|\bin (?:response|answer) to your question\b"
    r"|\byour question (?:about|regarding|concerning)\b"
    r"|\bas (?:you )?(?:requested|asked)\b, here"
    r"|\bhere(?:'s| is) (?:a |the )?(?:draft|first pass|revised version) (?:of|for) your\b"
)

PRIVACY_FILLER = (
    r"\bmaintains? a (?:relatively )?low(?:-key)? (?:public )?profile\b"
    r"|\bkeeps? (?:his|her|their) personal life private\b"
    r"|\bprefers? to keep (?:his|her|their) (?:personal )?life out of the (?:public eye|spotlight)\b"
    r"|\blittle is publicly known about (?:his|her|their) personal life\b"
)

# False ranges (catalogue section 15): "from X to Y" where the poles are not on
# a shared scale. Only the two closed forms, which is where the tell is safe.
FALSE_RANGE = (
    r"\bfrom the (?:dawn|birth|earliest days|inception|advent|emergence|humble)\b"
    r"[^.]{0,80}?\bto the (?:modern|present|current|contemporary|digital|"
    r"future|mighty|vanished|towering)\b"
    r"|\bfrom (?:the )?humble\b[^.]{0,60}?\bto (?:the )?(?:mighty|towering|grand|sprawling)\b"
)

QA_RHETORICAL = (
    r"\b(?:is|are|was|were|will|does|do|did|can|could|should|would|"
    r"has|have|had)\s+[^.?!\n]{2,40}\?\s+(?:yes|no|absolutely|never|"
    r"definitely|certainly|maybe|probably|possibly|rarely|always|"
    r"hardly|nope|nah|sure|exactly|sometimes)[.!]"
)

SELF_THOROUGHNESS = (
    r"\b(?:this comprehensive (?:guide|overview|analysis)|"
    r"this in-depth (?:analysis|look|examination)|"
    r"this complete (?:guide|overview)|"
    r"a thorough examination of|everything you need to know about)\b"
)

EDITORIAL_INTERJECTION = (
    r"\b(?:it'?s important to (?:remember|note|understand|recognize)|"
    r"it is important to (?:remember|note|understand|recognize)|"
    r"one must note that|it is worth pointing out|"
    r"it cannot be overstated that|it must be emphasized that)\b"
)


# ------------------------------------------------------------ character layer
_EXTRA_INVISIBLE: set = {
    0x034F,
    0x115F, 0x1160,
    0x17B4, 0x17B5,
    0x180B, 0x180C, 0x180D, 0x180F,
    0x3164,
    0xFFA0,
    0x2065,
}
_EXTRA_INVISIBLE |= set(range(0xFFF0, 0xFFF9))
_EXTRA_INVISIBLE |= set(range(0xE0100, 0xE01F0))

# These three were kept unconditionally because they are load-bearing in Arabic,
# Indic scripts and emoji. That also made them the one channel a payload could
# ride through untouched, so they are now decided by context like everything
# else: kept beside the scripts that need them, dropped between Latin letters,
# where they do nothing at all.
_CONTEXTUAL_INVISIBLE = {0x200C, 0x200D} | set(range(0xFE00, 0xFE10))

# A codepoint is debris only where it has no job. The same character can be a
# watermark in English and load-bearing three words later, so context decides.
# Each rule below exists because removing it blind destroyed real text: the
# England flag became a black flag, a Japanese name lost its variant, Arabic
# changed reading order, Thai lost every line-break opportunity.
_SPACELESS = (
    (0x0E00, 0x0E7F),      # Thai
    (0x0E80, 0x0EFF),      # Lao
    (0x1780, 0x17FF),      # Khmer
    (0x1000, 0x109F),      # Myanmar
    (0x3040, 0x30FF),      # kana
    (0x3400, 0x4DBF), (0x4E00, 0x9FFF), (0xF900, 0xFAFF),   # CJK
)
_RTL = ((0x0590, 0x08FF), (0xFB1D, 0xFDFF), (0xFE70, 0xFEFF),
        (0x10800, 0x10FFF), (0x1E800, 0x1EFFF))
_MONGOLIAN = ((0x1800, 0x18AF),)
_KHMER = ((0x1780, 0x17FF),)
_CJK = ((0x3400, 0x4DBF), (0x4E00, 0x9FFF), (0xF900, 0xFAFF), (0x20000, 0x2FA1F))
# Scripts where a joiner or non-joiner changes how a word is written.
_JOINING = ((0x0590, 0x08FF), (0x0900, 0x0DFF), (0xFB1D, 0xFDFF), (0xFE70, 0xFEFF),
            (0x1000, 0x109F), (0x1780, 0x17FF))
_SYMBOL = ((0x2190, 0x2BFF), (0x1F000, 0x1FAFF), (0xFE0F, 0xFE0F), (0x20E3, 0x20E3))


def _emoji_ish(ch: str) -> bool:
    if not ch:
        return False
    return _in(ch, _SYMBOL) or unicodedata.category(ch) == "So"


def _in(ch: str, ranges) -> bool:
    if not ch:
        return False
    cp = ord(ch)
    return any(a <= cp <= b for a, b in ranges)


_RTL_RE = re.compile("[%s]" % "".join("\\U%08x-\\U%08x" % (a, b) for a, b in _RTL))


def _has_rtl(text: str) -> bool:
    """Whether the document contains right-to-left script.

    A regex, because this is asked once per scan over the whole document and
    the Python loop it replaced put a 540 KB file within a second of the
    guard's 8-second timeout.
    """
    return _RTL_RE.search(text) is not None


def _tag_sequence(text: str, i: int) -> bool:
    """A tag character belongs to an emoji flag only if the run it sits in
    starts at a black-flag base. Testing the neighbour alone is not enough:
    each character of a smuggled payload would vouch for the next one."""
    j = i
    while j > 0 and 0xE0020 <= ord(text[j - 1]) <= 0xE007F:
        j -= 1
    return j > 0 and text[j - 1] == "\U0001F3F4"


def _keeps_function(ch: str, prev: str, nxt: str, rtl_doc: bool,
                    text: str = "", idx: int = -1) -> bool:
    """True when this invisible character is doing a job here."""
    cp = ord(ch)
    # Emoji tag sequences: the subdivision flags are a base plus tag letters
    # ending in U+E007F. Stripping the tags leaves a plain black flag.
    if 0xE0020 <= cp <= 0xE007F:
        return idx >= 0 and _tag_sequence(text, idx)
    # Ideographic variation sequences select the right form of a kanji, which
    # is how names and places are written correctly.
    if 0xE0100 <= cp <= 0xE01EF:
        return _in(prev, _CJK)
    # Scripts written without spaces use ZWSP to mark where a line may break.
    if cp == 0x200B:
        return _in(prev, _SPACELESS) or _in(nxt, _SPACELESS)
    # A soft hyphen between two letters is a hyphenation point an author chose.
    if cp == 0x00AD:
        return bool(prev) and bool(nxt) and prev.isalpha() and nxt.isalpha()
    # Bidi controls order visible text; only meaningless where nothing is RTL.
    if cp in (0x200E, 0x200F, 0x061C) or 0x202A <= cp <= 0x202E or 0x2066 <= cp <= 0x2069:
        return rtl_doc
    if 0x180B <= cp <= 0x180F:
        return _in(prev, _MONGOLIAN)
    if cp in (0x17B4, 0x17B5):
        return _in(prev, _KHMER) or _in(nxt, _KHMER)
    # Joiner and non-joiner: real work in Arabic, Indic and emoji sequences,
    # nothing whatever between two Latin letters.
    if cp in (0x200C, 0x200D):
        return (_in(prev, _JOINING) or _in(nxt, _JOINING)
                or _emoji_ish(prev) or _emoji_ish(nxt))
    # A variation selector chooses a glyph form; with no glyph in front of it
    # there is no form to choose.
    if 0xFE00 <= cp <= 0xFE0F:
        # A keycap is digit + VS16 + U+20E3, so the base is behind and the
        # enclosing mark ahead; looking only backwards broke "press 1".
        return _emoji_ish(prev) or _in(prev, _CJK) or (nxt and ord(nxt) == 0x20E3)
    return False


_SUSPECT = re.compile(r"[^\t\n\r\x20-\x7E]")


def _is_invisible(ch: str) -> bool:
    if ch in "\t\n\r":
        return False
    cp = ord(ch)
    if cp in _CONTEXTUAL_INVISIBLE:
        return True
    if unicodedata.category(ch) in ("Cf", "Cc", "Zl", "Zp"):
        return True
    if cp in _EXTRA_INVISIBLE:
        return True
    return 0xE0000 <= cp <= 0xE0FFF


def _is_nonstandard_space(ch: str) -> bool:
    return ch != " " and unicodedata.category(ch) == "Zs"


def _char_name(cp: int) -> str:
    try:
        name = unicodedata.name(chr(cp))
    except (ValueError, OverflowError):
        name = ""
    if not name:
        if 0xE0000 <= cp <= 0xE0FFF:
            return "reserved tag/VS plane (invisible)"
        if cp <= 0x001F or 0x007F <= cp <= 0x009F:
            return "CONTROL"
        return "reserved / default-ignorable"
    return f"{name} [TAG block]" if 0xE0000 <= cp <= 0xE007F else name

NOT_X_JUST_Y = (
    r"\b(?:"
    r"(?:no|not)\s+\w+,\s+(?:just|only|simply)\s+\w+"
    r"|(?:(?:is|are|was|were)n'?t|not)\s+(?:just|merely)\s+(?:a |an |the )?\w+\s*[,—–-]\s*"
    r"(?:it'?s|it is|it was|they'?re|they are|they were|that'?s|but)\b"
    r")"
)

COMPULSIVE_INTRO = (
    r"\b(?:in today['’]?s (?:[\w-]+ ){0,2}(?:world|landscape|environment|market)\b|"
    r"in a world where|in an era of|"
    r"in recent years,|more than ever before|we live in a (?:time|world) when|"
    r"(?:great|exciting|big) news[!:]|"
    r"ever (?:wanted|wondered|dreamed|wished) to [^?\n]{3,60}\?|"
    r"in an increasingly (?:interconnected|digital|competitive|complex) world)\b"
)

ARTICLE_TITLE_NOUN = (
    r"\bThe (?:List|Index|Compilation|Collection|Catalogue|Guide|Overview) of "
    r"[A-Z][\w\s]{3,60}\s+is (?:a|an|the)\b"
)

HYPHEN_RANGE = re.compile(
    r"(?<![\w-])(\d{4})-(\d{4})(?![\w-])"
)
_YEAR_MIN, _YEAR_MAX = 1500, 2999

CONCRETE_EVIDENCE = (
    r"\b(?:without concrete evidence|do you have concrete evidence|"
    r"i (?:would )?need concrete (?:evidence|examples) to|"
    r"absent concrete proof|provide concrete evidence)\b"
)

ECOSYSTEM_PADDING = (
    r"\b(?:plays a (?:vital|crucial|key|significant) role in (?:its|the) "
    r"ecosystem|conservation efforts are (?:underway|ongoing|in place)|"
    r"serves as an indicator species|contributes to biodiversity)\b"
)

CANONICAL_SLOP = (
    r"unlock(?:ing)? (?:the |your |its )?full potential|"
    r"navigat(?:e|ing) the complexit(?:y|ies)|"
    r"a testament to the (?:\w+ ){0,2}(?:power|importance|spirit|resilience)\b|"
    r"stay(?:ing)? ahead of the curve|"
    r"turn(?:ing)? (?:challenges|obstacles) into opportunit(?:y|ies)|"
    r"the future is (?:full of possibilit(?:y|ies)|bright)|"
    r"something for everyone|"
    r"whether you (?:'?re|are) an? (?:beginner|novice|seasoned|professional|expert|pro|"
    r"student|newcomer|veteran)\b|"
    r"the key takeaway|"
    r"seamlessly integrat(?:e|es|ed|ing|ion)|"
    r"take (?:it|your \w+|things|productivity) to the next level|"
    r"work(?:ing)? smarter,? not harder|"
    r"more important than ever|"
    r"in an? (?:increasingly|ever-)\w|"
    r"drive(?:s|n)? (?:meaningful|real|tangible|transformative) (?:impact|change|results|value)|"
    r"stay(?:ing)? one step ahead|"
    r"harness(?:ing)? the power of|"
    r"pave(?:s|d)? the way for|"
    r"from startups to enterprises|"
    r"meet(?:s|ing)? you where(?:ver)? you are|"
    r"whether you'?re (?:a |an )?[\w-]+ or (?:just )?[\w-]+ing(?: out)?|"
    r"embark(?:s|ed|ing)? on an? (?:exciting|incredible|transformative) journey|"
    r"reimagin(?:e|es|ing) what'?s possible|"
    r"buckle up[,!]|"
    r"unlock(?:s|ing)? (?:new|endless|infinite) possibilit(?:y|ies)|"
    r"empower(?:s|ing)? (?:our|your|their) (?:\w+ )?(?:community|teams?|people|users)\b|"
    r"deeply passionate about|"
    r"wealth of (?:experience|knowledge|expertise)|"
    r"results?-(?:oriented|driven) (?:team|professional|approach|culture)|"
    r"cultivat(?:e|es|ing) a culture of|"
    r"culture of (?:relentless )?(?:excellence|innovation)|"
    r"nestled (?:in the heart of|at the intersection of)|"
    r"at the intersection of \w+ and \w+|"
    r"(?:bold|forward-thinking|shared) vision (?:of|for|to)\b|"
    r"working (?:hard )?behind the scenes|"
    r"packed with (?:powerful|exciting|amazing) (?:new )?features|"
    r"streamlines? your workflow|"
    r"(?:a|the) (?:brighter|better),? more \w+ (?:future|tomorrow|world)|"
    r"those who (?:dare to|embrace) \w+ will|"
    r"say (?:goodbye|hello) to|"
    r"stop [\w-]+ing[.,!]? (?:and )?start [\w-]+ing|"
    r"reclaim your [\w-]+|"
    r"transform your (?:life|business|workflow|day|home|routine) with|"
    r"power(?:s|ing)? the future of|"
    r"the ultimate (?:tool|solution|guide|companion|destination) for|"
    r"(?:start|begin) your [\w-]+ journey|"
    r"(?:^|[.!?]\s+)escape to (?:serenity|tranquility|the|our|this|your)\b|"
    r"blend(?:s|ing)? (?:[\w-]+ ){0,3}(?:charm|craftsmanship|tradition|simplicity|"
    r"heritage|flavors?) (?:with|and)|"
    r"we'?(?:re| are) (?:excited|thrilled|delighted|proud) to "
    r"(?:announce|introduce|launch|share|unveil)|"
    r"whether you'?re (?:aiming|looking|chasing|trying|hoping|seeking) to|"
    r"imagine a world where|"
    r"adventure awaits|"
    r"experience the magic of|"
    r"step into the world of|"
    r"gateway to (?:the world of|a world)|"
    r"nothing short of (?:amazing|extraordinary|explosive|remarkable|spectacular)|"
    r"it'?s time (?:we|to) (?:stop|rethink|embrace|move beyond)|"
    r"like never before|"
    r"you have the power to|"
    r"(?:the )?perfect blend of|"
    r"if you blinked[^.,\n]{0,24},? you (?:might have |probably )?missed"
)

PLACEHOLDER = (
    r"(?:\[(?:your|insert|add|enter|company name|client name|placeholder|todo|"
    r"tbd|tk|source url)\b[^\]\n]{0,40}\](?![(\[])|"
    r"\[(?:startup |company |client |journal |first |last |full )?name\](?![(\[])|"
    r"\[city, ?state\](?![(\[])|"
    r"\[(?:manuscript id|lead vc firm|editor'?s last name|date of submission)"
    r"(?: [^\]\n]{0,20})?\](?![(\[])|"
    # An all-caps bracket is usually a slot, [COMPANY] or [XX]. It is also how
    # physics writes a forbidden emission line and how mathematics labels a
    # term, so [NII], [O III], [CM1] and [N/2] are excluded. Every human
    # document this rule wrongly flagged, all eight of them, was one of those,
    # and the rule is decisive, so each was floored at 45.
    r"(?-i:\[(?![A-Z][a-z]? ?(?:I{1,3}|IV|VI{0,3}|IX)\])"
    r"(?![A-Z]{1,3}[0-9/][A-Z0-9/]{0,2}\])"
    r"[A-Z][A-Z0-9 ._/-]{1,30}\])(?![(\[])|"
    # The double-brace form. Without it a rewrite could turn [Name] into
    # {{first_name}}, watch this rule stop firing, and read that as progress.
    r"\{\{ ?[a-z][a-z0-9 ._-]{1,30} ?\}\}|"
    r"\bx{3,}\b|\blorem ipsum\b)"
)

CHATBOT_REF_MARKUP = (
    r"(?:\bcite(?:turn|start|nav)\w*|\boai_citation\w*|\bcontentReference\b|"
    r"\bnavlist\b|【\d+†[^】]*】)"
)

AI_UTM = (
    r"utm_source=(?:chatgpt\.com|chat\.openai\.com|perplexity\.ai|claude\.ai|"
    r"gemini\.google\.com|copilot\.microsoft\.com|poe\.com)(?![\w]|\.\w)"
)

MODEL_DIALECT_CLAUDE = (
    r"\b(?:genuinely|fascinating|nuanced|thoughtfully|refreshingly|"
    r"strikingly|compellingly|quietly (?:powerful|profound|radical)|"
    r"deeply (?:human|personal|felt|unsettling)|resonates? deeply)\b"
)
MODEL_DIALECT_GPT = (
    r"\b(?:game-chang\w+|supercharge\w*|skyrocket\w*|turbocharge\w*|"
    r"revolutioniz\w+|double down on|dive deep(?:er)? into|"
    r"unlock(?:ing|s)? (?:the )?(?:power|potential|value)|"
    r"take[sn]? [^.,\n]{0,25} to the next level)\b"
)

PASSIVE_VOICE = re.compile(
    r"\b(?:is|are|was|were|been|being|be)\s+(?:\w+ly\s+)?(\w+(?:ed|en))\b",
    re.IGNORECASE,
)
_PASSIVE_STOP = {
    "red", "bed", "fed", "led", "wed", "sacred", "hundred", "kindred",
    "oxen", "wooden", "golden", "sudden", "hidden", "garden", "wicked",
    "naked", "linen", "kitchen", "sacred", "blessed", "rugged", "tired",
}

CONFUSABLES: dict[int, str] = {
    0x0430: "a", 0x03F2: "c", 0x0441: "c", 0x0501: "d", 0x0435: "e",
    0x0562: "g", 0x0456: "i", 0x0458: "j", 0x0578: "n",
    0x03BF: "o", 0x043E: "o", 0x0440: "p", 0x0455: "s", 0x057E: "u",
    0xFEAA: "v", 0x051D: "w", 0x0445: "x", 0x0443: "y", 0x04BB: "h",
    0x0410: "A", 0x0412: "B", 0x0415: "E", 0x041A: "K", 0x041C: "M",
    0x041D: "H", 0x041E: "O", 0x0420: "P", 0x0421: "C", 0x0422: "T",
    0x0423: "Y", 0x0425: "X", 0x0406: "I", 0x0408: "J", 0x0405: "S",
    0x0391: "A", 0x0392: "B", 0x0395: "E", 0x0396: "Z", 0x0397: "H",
    0x0399: "I", 0x039A: "K", 0x039C: "M", 0x039D: "N", 0x039F: "O",
    0x03A1: "P", 0x03A4: "T", 0x03A5: "Y", 0x03A7: "X",
}


_ALPHA_RUN = re.compile(r"[^\W\d_]+")


# ---------------------------------------------------------- homoglyph folding
def _native(ch: str) -> bool:
    """A letter that is not ASCII and not a lookalike: someone's real script."""
    return ch.isalpha() and ord(ch) > 127 and ord(ch) not in CONFUSABLES


def _is_mixed_run(run: str) -> bool:
    has_latin = any("a" <= c.lower() <= "z" and ord(c) < 128 for c in run)
    has_confusable = any(ord(c) in CONFUSABLES for c in run)
    return has_latin and has_confusable


def _fold_run(run: str) -> str:
    """Fold the lookalikes that are surrounded by Latin, and only those.

    `Сбер` glued to `Bank` used to come out as `Cбep`, because the run held
    both Latin and confusables. Three real Cyrillic letters were rewritten in a
    Russian word. A lookalike is only an attack when the letters beside it are
    ASCII; beside its own script it is simply that script.
    """
    if any(_native(c) for c in run):
        return run
    return "".join(CONFUSABLES.get(ord(c), c) for c in run)


def _fold_homoglyphs(token: str) -> str:
    return _ALPHA_RUN.sub(
        lambda m: _fold_run(m.group(0)) if _is_mixed_run(m.group(0)) else m.group(0),
        token,
    )


def _is_mixed_script_confusable(token: str) -> bool:
    return any(_is_mixed_run(m.group(0)) for m in _ALPHA_RUN.finditer(token))


def detect_homoglyphs(text: str) -> list[str]:
    hits: list[str] = []
    for tok in re.findall(r"\S+", text):
        if _is_mixed_script_confusable(tok):
            hits.append(tok)
    return hits


def fold_mixed_script(text: str) -> str:
    return re.sub(
        r"\S+",
        lambda m: _fold_homoglyphs(m.group(0))
        if _is_mixed_script_confusable(m.group(0))
        else m.group(0),
        text,
    )


_INWORD_ZERO_WIDTH = re.compile(r"(?<=[A-Za-z])[​‌‍⁠﻿]+(?=[A-Za-z])")


def defuse_evasion(text: str) -> tuple:
    hits = _INWORD_ZERO_WIDTH.findall(text)
    return fold_mixed_script(_INWORD_ZERO_WIDTH.sub("", text)), sum(len(h) for h in hits)


_QUOTE_MARK = re.compile(r"^[ \t]{0,3}>[ \t]?")


def strip_quoted_spans(text: str) -> str:
    lines = text.split("\n")
    quoted = [bool(_QUOTE_MARK.match(ln)) for ln in lines]
    out = []
    for i, ln in enumerate(lines):
        run = quoted[i] and ((i and quoted[i - 1]) or (i + 1 < len(quoted) and quoted[i + 1]))
        out.append(" " * len(ln) if run else ln)
    return "\n".join(out)

TRANSITION_OPENERS = re.compile(
    r"(?:^|\n|[.!?]\s+)(Additionally|Furthermore|Moreover|However|Nevertheless|"
    r"Consequently|Subsequently|Notably)\b",
    re.MULTILINE,
)

CONTRACTABLE = re.compile(
    r"\b(?:it is|do not|does not|did not|is not|are not|was not|were not|"
    r"will not|would not|could not|should not|cannot|i am|you are|"
    r"we are|they are|i have|you have|we have|they have|i will|you will)\b",
    re.IGNORECASE,
)

CONTRACTIONS = re.compile(
    r"\b(?:it'?s|don'?t|doesn'?t|didn'?t|isn'?t|aren'?t|wasn'?t|weren'?t|"
    r"won'?t|wouldn'?t|couldn'?t|shouldn'?t|can'?t|i'?m|you'?re|we'?re|"
    r"they'?re|i'?ve|you'?ve|we'?ve|they'?ve|i'?ll|you'?ll)\b",
    re.IGNORECASE,
)

FIRST_PERSON = re.compile(
    r"\b(?:i|me|my|mine|we|us|our|ours)\b",
    re.IGNORECASE,
)

ABBREV = {
    "mr.", "mrs.", "ms.", "dr.", "prof.", "vs.", "etc.", "e.g.", "i.e.",
    "u.s.", "u.k.", "fig.", "no.", "vol.", "pp.", "st.", "ed.", "eds.",
    "inc.", "ltd.", "corp.", "co.", "sr.", "jr.", "ave.", "blvd.", "rd.",
}


# ------------------------------------------------------------- text structure
def split_sentences(text: str) -> list[str]:
    placeholder = ""
    text = text.replace(placeholder, "")
    protected = re.sub(r"(\d)\.(\d)", rf"\1{placeholder}\2", text)
    protected = re.sub(
        r"\b([a-z]{1,2})\.([a-z]{1,2})\.",
        lambda m: f"{m.group(1)}{placeholder}{m.group(2)}{placeholder}",
        protected,
        flags=re.IGNORECASE,
    )
    out: list[str] = []
    buf = ""
    for m in re.finditer(r"[^.!?]+(?:[.!?]+|$)", protected):
        chunk = m.group(0)
        if not chunk.strip():
            continue
        buf += chunk
        tail = chunk.strip().lower()
        base = ""
        if tail.endswith("."):
            toks = tail.split()
            if toks:
                base = re.sub(r"[^\w.]", "", toks[-1]).rstrip(".")
        if base and ((base + ".") in ABBREV or re.fullmatch(r"[a-z]", base)):
            buf += " "
            continue
        out.append(buf.strip())
        buf = ""
    if buf.strip():
        out.append(buf.strip())
    return [s.replace(placeholder, ".") for s in out]


def count_words(s: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", s))


def first_two_words(s: str) -> str:
    words = re.findall(r"\b[\w'-]+\b", s.lower())
    return " ".join(words[:2]) if len(words) >= 2 else ""


def split_paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]



# A model that loses the thread repeats itself. Not the way a person repeats a
# term of art, which is what academic prose does constantly, but by emitting the
# same span until the window closes: "is caused in part by - at least in the US -
# is caused in part by in part by a shortage of a". Nothing else in the catalogue
# looks for it, and it is the only tell present in small-model continuations,
# which carry none of the marketing vocabulary the rest of the rules are built
# around.
#
# The measure is the share of six-gram positions whose six-gram occurs more than
# once. It has to clear a high bar because legitimate repetition is common:
# 15.1% of PubMed abstracts and 10.5% of textbook passages exceed 2%, and no
# human corpus measured reaches 0.13 at the 99th percentile. Degeneration is an
# order of magnitude worse, with machine SQuAD and writing-prompt continuations
# at 0.62 and 0.63 at the 90th. At 0.20 the rule fires on 0.0% of PubMed,
# textbook and every MAGE human arm, on 0.2% of arXiv abstracts, and on 18.6% of
# machine SQuAD and 32.3% of machine writing prompts.
_REP_WORD = re.compile(r"[A-Za-z0-9']+")
_REP_N = 6
_REP_MIN_WORDS = _REP_N * 3
_REP_THRESHOLD = 0.20


def detect_degenerate_repetition(text: str) -> dict:
    """Share of six-gram positions whose six-gram appears more than once."""
    words = [w.lower() for w in _REP_WORD.findall(text)]
    if len(words) < _REP_MIN_WORDS:
        return {"ratio": 0.0, "degenerate": False, "worst": None}
    grams = [tuple(words[i:i + _REP_N]) for i in range(len(words) - _REP_N + 1)]
    counts = collections.Counter(grams)
    dup = sum(c for g, c in counts.items() if c > 1)
    ratio = dup / float(len(grams))
    worst = max(counts.items(), key=lambda kv: kv[1]) if counts else None
    return {
        "ratio": round(ratio, 4),
        "degenerate": ratio > _REP_THRESHOLD,
        "worst": (" ".join(worst[0]), worst[1]) if worst and worst[1] > 1 else None,
    }

def detect_opener_repetition(text: str) -> list[dict]:
    hits: list[dict] = []
    for p_i, para in enumerate(split_paragraphs(text)):
        sentences = split_sentences(para)
        if len(sentences) < 3:
            continue
        openers = [first_two_words(s) for s in sentences if s]
        counter: dict[str, int] = {}
        for o in openers:
            if not o:
                continue
            counter[o] = counter.get(o, 0) + 1
        for opener, count in counter.items():
            if count >= 3:
                hits.append({"paragraph": p_i + 1, "opener": opener, "repeats": count})
    return hits


def detect_burstiness(text: str) -> dict:
    sentences = split_sentences(text)
    if len(sentences) < 3:
        return {"sentences": len(sentences), "cv": None, "monotonous": False, "has_short": True}
    lengths = [count_words(s) for s in sentences if count_words(s) > 0]
    if len(lengths) < 3:
        return {"sentences": len(sentences), "cv": None, "monotonous": False, "has_short": True}
    mean = statistics.mean(lengths)
    stdev = statistics.pstdev(lengths)
    cv = stdev / mean if mean else 0
    has_short = any(n < 10 for n in lengths)
    return {
        "sentences": len(sentences),
        "cv": round(cv, 3),
        "monotonous": cv < 0.35,
        "has_short": has_short,
    }


def detect_paragraph_monotony(text: str) -> dict:
    paragraphs = split_paragraphs(text)
    if len(paragraphs) < 4:
        return {"paragraphs": len(paragraphs), "cv": None, "monotonous": False}
    lengths = [count_words(p) for p in paragraphs if count_words(p) > 0]
    if len(lengths) < 4:
        return {"paragraphs": len(paragraphs), "cv": None, "monotonous": False}
    mean = statistics.mean(lengths)
    stdev = statistics.pstdev(lengths)
    cv = stdev / mean if mean else 0
    return {
        "paragraphs": len(paragraphs),
        "cv": round(cv, 3),
        "monotonous": cv < 0.4,
    }


def detect_hedge_stacking(text: str) -> list[dict]:
    hits: list[dict] = []
    pattern = re.compile(HEDGES)
    for i, sent in enumerate(split_sentences(text)):
        matches = pattern.findall(sent)
        if len(matches) >= 2:
            hits.append({
                "sentence_idx": i,
                "hedges": matches,
                "sample": sent[:120] + ("..." if len(sent) > 120 else ""),
            })
    return hits


def detect_em_dash_overuse(text: str) -> list[dict]:
    hits: list[dict] = []
    for p_i, para in enumerate(split_paragraphs(text)):
        count = para.count("—")
        if count >= 2:
            hits.append({"paragraph": p_i + 1, "em_dash_count": count})
    return hits


def _plural_forms(term: str) -> list[str]:
    parts = term.split(" ")
    last = parts[-1]
    if last.endswith("is") and len(last) > 2:
        plural_last = last[:-2] + "es"
    elif last.endswith("y") and len(last) > 1 and last[-2] not in "aeiou":
        plural_last = last[:-1] + "ies"
    elif last.endswith(("s", "ss", "sh", "ch", "x", "z")):
        plural_last = last + "es"
    else:
        plural_last = last + "s"
    plural = " ".join(parts[:-1] + [plural_last])
    return [term] if plural == term else [term, plural]


def detect_synonym_cycling(text: str) -> list[list[str]]:
    CLUSTERS = [
        ["protagonist", "main character", "central figure", "hero", "heroine"],
        ["company", "firm", "organization", "enterprise", "business"],
        ["author", "writer", "novelist", "scribe"],
        ["report", "study", "analysis", "investigation", "examination"],
        ["technology", "tool", "system", "platform", "solution"],
        ["technique", "method", "approach", "strategy", "tactic"],
        ["challenge", "obstacle", "difficulty", "hurdle", "barrier"],
        ["benefit", "advantage", "upside", "strength"],
    ]
    lower = text.lower()
    hits: list[list[str]] = []
    for cluster in CLUSTERS:
        used: list[str] = []
        for term in cluster:
            forms = _plural_forms(term)
            term_pattern = r"\b(?:" + "|".join(re.escape(f) for f in forms) + r")\b"
            if re.search(term_pattern, lower):
                used.append(term)
        if len(used) >= 3:
            hits.append(used)
    return hits


_CTA_VERBS = {
    "install", "join", "grab", "download", "try", "discover", "experience",
    "escape", "transform", "reclaim", "unlock", "elevate", "boost", "say",
    "imagine", "explore", "meet", "introducing", "upgrade", "claim", "unleash",
    "supercharge", "level", "stop", "start",
}


def detect_imperative_cta(text: str) -> list[str]:
    hits = []
    for s in split_sentences(text):
        w = re.match(r"[^\w]*([A-Za-z][\w'-]*)", s)
        if w and w.group(1).lower() in _CTA_VERBS:
            hits.append(s.strip()[:60])
    return hits if len(hits) >= 3 else []


def detect_fragmented_headers(text: str) -> list[dict]:
    lines = text.split("\n")
    hits: list[dict] = []
    for i, line in enumerate(lines):
        m = re.match(r"^(#{1,6})\s+(.+)$", line)
        if not m:
            continue
        heading_words = set(re.findall(r"\w+", m.group(2).lower()))
        j = i + 1
        while j < len(lines) and not lines[j].strip():
            j += 1
        if j >= len(lines):
            continue
        next_line = lines[j].strip()
        if next_line.startswith("#"):
            continue
        if re.match(r"^(?:[-*+•]|\d+\.|\|)\s", next_line):
            continue
        if count_words(next_line) > 12:
            continue
        next_words = set(re.findall(r"\w+", next_line.lower()))
        if heading_words and len(heading_words & next_words) >= 1 and count_words(next_line) < 8:
            hits.append({
                "heading": m.group(2),
                "filler_line": next_line,
                "line_no": i + 1,
            })
    return hits


def detect_title_case_headings(text: str) -> list[dict]:
    hits: list[dict] = []
    minor = {
        "a", "an", "the", "and", "or", "but", "of", "in", "on", "at",
        "to", "for", "with", "by", "as", "is", "it",
    }
    for m in TITLE_CASE_HEADING.finditer(text):
        heading = m.group(2).strip()
        words = heading.split()
        if len(words) < 3:
            continue
        if re.match(r"^[\d\W]", heading):
            continue
        major_words = [w for w in words if w.lower() not in minor]
        if len(major_words) < 2:
            continue
        all_cap = all(re.match(r"^[A-Z]", w) for w in major_words)
        if all_cap and not heading.isupper():
            hits.append({"heading": heading})
    return hits


def detect_transition_clusters(text: str) -> list[dict]:
    hits: list[dict] = []
    for p_i, para in enumerate(split_paragraphs(text)):
        matches = TRANSITION_OPENERS.findall(para)
        if len(matches) >= 2:
            hits.append({
                "paragraph": p_i + 1,
                "transitions": matches,
                "count": len(matches),
            })
    return hits


_ADJECTIVE_SUFFIXES = (
    "ive", "ous", "able", "ible", "ic", "ical", "ant", "ent", "ful",
    "less", "al", "ial", "ary", "ory", "ish", "ative", "itive",
)
_ADJECTIVE_AI_TELLS = {
    "innovative", "transformative", "groundbreaking", "robust",
    "seamless", "dynamic", "holistic", "scalable", "agile", "elegant",
    "vibrant", "powerful", "comprehensive", "cutting-edge",
    "forward-thinking", "next-generation", "world-class",
}


def detect_stacked_adjectives(text: str) -> list[str]:
    pattern = re.compile(
        r"\b(?:[a-z]+(?:,[ \t]+|[ \t]+and[ \t]+)){3,10}[a-z]+[ \t]+[a-z]+\b",
        re.IGNORECASE,
    )
    hits: list[str] = []
    for m in pattern.finditer(text):
        snippet = m.group(0)
        if not ("," in snippet and len(snippet.split()) <= 12):
            continue
        candidate_words = re.findall(r"[A-Za-z][A-Za-z'-]*", snippet)[:-1]
        has_adj_evidence = any(
            w.lower() in _ADJECTIVE_AI_TELLS
            or any(w.lower().endswith(s) for s in _ADJECTIVE_SUFFIXES)
            for w in candidate_words
        )
        if has_adj_evidence:
            hits.append(snippet)
    return hits[:MAX_SAMPLES * 2]


# ------------------------------------------------------- structural detectors
def detect_decorative_rules(text: str) -> dict:
    """Standalone horizontal rules used as section furniture. Markdown post-training
    leaves them behind; human markdown uses one or none."""
    rules = re.findall(r"(?m)^[ \t]{0,3}(?:-{3,}|\*{3,}|_{3,})[ \t]*$", text)
    lines = len(text.splitlines())
    if len(rules) < 3 or lines < 25:
        return {}
    return {"count": len(rules),
            "samples": ["%d standalone horizontal rules in %d lines" % (len(rules), lines)]}


def detect_mid_essay_bullets(text: str) -> dict:
    structured = bool(re.search(r"^#{1,6}\s+\S", text, re.M))
    paragraphs = split_paragraphs(text)
    bullet_count = 0
    prose_count = 0
    for para in paragraphs:
        lines = [ln for ln in para.split("\n") if ln.strip()]
        if all(re.match(r"^\s*(?:[-*•]|\d+\.)\s+", ln) for ln in lines):
            bullet_count += 1
        else:
            prose_count += 1
    return {
        "bullet_paragraphs": bullet_count,
        "prose_paragraphs": prose_count,
        "structured": structured,
        "mixed": (not structured) and bullet_count >= 1 and prose_count >= 2,
    }


def _codepoint_breakdown(matches: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for c in matches:
        key = f"U+{ord(c):04X}"
        counts[key] = counts.get(key, 0) + 1
    return counts


def _labelled_samples(counts: dict[str, int]) -> list[str]:
    out: list[str] = []
    for key, n in counts.items():
        cp = int(key[2:], 16)
        name = _char_name(cp)
        out.append(f"{key} {name}: {n}" if name else f"{key}: {n}")
    return out


def detect_invisible_chars(text: str) -> dict:
    """Report only what the scrub would remove.

    Detection and cleaning have to agree. When they did not, a variation
    selector doing its job inside an emoji was counted as a watermark, and
    every document with an emoji gained points it had not earned.
    """
    # _SUSPECT finds the handful of non-ASCII positions in C, so the context
    # test runs on those and not on every character. Walking the whole string
    # in Python instead cost 8 seconds on a 540 KB document and tripped the
    # guard's own timeout.
    rtl_doc = _has_rtl(text)
    n = len(text)
    matches = []
    for m in _SUSPECT.finditer(text):
        ch, i = m.group(0), m.start()
        if ch in "\t\n\r" or not _is_invisible(ch):
            continue
        prev = text[i - 1] if i else ""
        nxt = text[i + 1] if i + 1 < n else ""
        if not _keeps_function(ch, prev, nxt, rtl_doc, text, i):
            matches.append(ch)
    if not matches:
        return {"count": 0, "chars": {}}
    return {"count": len(matches), "chars": _codepoint_breakdown(matches)}


def detect_nonstandard_spaces(text: str) -> dict:
    n = len(text)
    matches = []
    for m in _SUSPECT.finditer(text):
        ch, i = m.group(0), m.start()
        if not _is_nonstandard_space(ch):
            continue
        prev = text[i - 1] if i else ""
        nxt = text[i + 1] if i + 1 < n else ""
        if not _space_holds(ch, prev, nxt):
            matches.append(ch)
    if not matches:
        return {"count": 0, "chars": {}}
    return {"count": len(matches), "chars": _codepoint_breakdown(matches)}


# A no-break space earns its place by holding something together: a number to
# its unit, or French punctuation to the word before it. Between two ordinary
# English words it is debris, and that is the common case, so it is normalised
# there rather than everywhere.
_NOBREAK = {0x00A0, 0x202F}
_FRENCH_AFTER = set(":;!?»›%€")
_FRENCH_BEFORE = set("«‹")


def _space_holds(ch: str, prev: str, nxt: str) -> bool:
    if ord(ch) not in _NOBREAK:
        return False
    if prev.isdigit() or nxt.isdigit():
        return True
    return nxt in _FRENCH_AFTER or prev in _FRENCH_BEFORE


def clean_text(text: str) -> str:
    out: list = []
    rtl_doc = _has_rtl(text)
    n = len(text)
    for i, ch in enumerate(text):
        if ch in "\t\n\r":
            out.append(ch)
            continue
        cat = unicodedata.category(ch)
        if cat in ("Zl", "Zp"):
            out.append("\n")
            continue
        if _is_invisible(ch):
            prev = text[i - 1] if i else ""
            nxt = text[i + 1] if i + 1 < n else ""
            if _keeps_function(ch, prev, nxt, rtl_doc, text, i):
                out.append(ch)
            continue
        if cat == "Zs":
            prev = text[i - 1] if i else ""
            nxt = text[i + 1] if i + 1 < n else ""
            out.append(ch if _space_holds(ch, prev, nxt) else " ")
            continue
        out.append(ch)
    cleaned = "".join(out)
    cleaned = fold_mixed_script(cleaned)
    # Every run of whitespace at the end of a line goes, including the two spaces that
    # write a Markdown hard break. Carving the break out was tried and reverted: it made
    # the rule depend on how the file renders, which is not knowable from the text alone,
    # and it spared the same two spaces in .txt and .rst where they are only debris.
    cleaned = re.sub(r"[ \t]+(?=\r?\n)", "", cleaned)
    # Blank leading lines go; the first line's own indentation stays, because
    # four spaces in Markdown is a code block, not stray whitespace.
    cleaned = re.sub(r"\A(?:[ \t]*\r?\n)+", "", cleaned)
    cleaned = re.sub(r"[ \t\r\n]+$", "", cleaned)
    return cleaned


def detect_trailing_whitespace(text: str) -> dict:
    eof = re.search(r"[ \t\r\n]+\Z", text)
    eof_run = eof.group(0) if eof else ""
    trailing_newlines = eof_run.count("\n")
    trailing_blanks = eof_run.count(" ") + eof_run.count("\t")
    lead = re.match(r"[ \t\r\n]+", text)
    leading_ws = len(lead.group(0)) if lead else 0
    eol_spaces = len(re.findall(r"[ \t]+\r?\n", text))
    artifact = (
        trailing_newlines >= 2
        or trailing_blanks > 0
        or eol_spaces > 0
        or leading_ws > 0
    )
    return {
        "trailing_newlines": trailing_newlines,
        "trailing_blanks": trailing_blanks,
        "leading_whitespace": leading_ws,
        "eol_trailing_spaces": eol_spaces,
        "artifact": artifact,
    }


def detect_hyphen_ranges(text: str) -> list[str]:
    hits: list[str] = []
    for m in HYPHEN_RANGE.finditer(text):
        a, b = m.group(1), m.group(2)
        try:
            ai, bi = int(a), int(b)
            if (
                _YEAR_MIN <= ai <= _YEAR_MAX
                and _YEAR_MIN <= bi <= _YEAR_MAX
                and bi > ai
                and bi - ai < 500
            ):
                hits.append(m.group(0))
        except ValueError:
            continue
    return hits


def detect_punctuation_diversity(text: str) -> dict:
    words = count_words(text)
    if words < 500:
        return {"words": words, "checked": False}
    semicolons = text.count(";")
    open_parens = text.count("(")
    close_parens = text.count(")")
    parentheticals = min(open_parens, close_parens)
    per_1k_semi = round(semicolons / words * 1000, 2)
    per_1k_paren = round(parentheticals / words * 1000, 2)
    return {
        "words": words,
        "checked": True,
        "semicolons": semicolons,
        "parentheticals": parentheticals,
        "semicolons_per_1k": per_1k_semi,
        "parentheticals_per_1k": per_1k_paren,
        "underused": semicolons == 0 and parentheticals < 2,
    }


def _count_syllables(word: str) -> int:
    word = word.lower()
    count = 0
    prev_vowel = False
    for c in word:
        is_vowel = c in "aeiouy"
        if is_vowel and not prev_vowel:
            count += 1
        prev_vowel = is_vowel
    if word.endswith("e") and count > 1:
        count -= 1
    return max(count, 1)


def _flesch_kincaid_grade(text: str) -> float | None:
    sentences = split_sentences(text)
    words = re.findall(r"[A-Za-z]+", text)
    if not sentences or not words:
        return None
    syllables = sum(_count_syllables(w) for w in words)
    words_per_sentence = len(words) / len(sentences)
    syllables_per_word = syllables / len(words)
    return 0.39 * words_per_sentence + 11.8 * syllables_per_word - 15.59


def detect_readability_consistency(text: str) -> dict:
    paragraphs = [p for p in split_paragraphs(text) if count_words(p) >= 10]
    if len(paragraphs) < 3:
        return {"paragraphs": len(paragraphs), "fk_stdev": None, "uniform": False}
    grades = [g for g in (_flesch_kincaid_grade(p) for p in paragraphs) if g is not None]
    if len(grades) < 3:
        return {"paragraphs": len(grades), "fk_stdev": None, "uniform": False}
    sd = statistics.pstdev(grades)
    return {"paragraphs": len(grades), "fk_stdev": round(sd, 2), "uniform": sd < 1.5}


def detect_cadence_alternation(text: str) -> dict:
    sentences = split_sentences(text)
    lengths = [count_words(s) for s in sentences if count_words(s) > 0]
    if len(lengths) < 6:
        return {"checked": False, "zigzag": None, "mechanical": False}
    diffs = [b - a for a, b in zip(lengths, lengths[1:])]
    signs = [1 if d > 0 else -1 if d < 0 else 0 for d in diffs]
    pairs = list(zip(signs, signs[1:]))
    if not pairs:
        return {"checked": False, "zigzag": None, "mechanical": False}
    flips = sum(1 for a, b in pairs if a and b and a == -b)
    zigzag = flips / len(pairs)
    mean = statistics.mean(lengths)
    cv = statistics.pstdev(lengths) / mean if mean else 0.0
    return {
        "checked": True,
        "zigzag": round(zigzag, 3),
        "mechanical": zigzag >= 0.85 and cv >= 0.25,
        "sentences": len(lengths),
    }


def detect_passive_voice(text: str) -> dict:
    sentences = split_sentences(text)
    if not sentences:
        return {"count": 0, "ratio": None}
    count = 0
    for s in sentences:
        m = PASSIVE_VOICE.search(s)
        if m and m.group(1).lower() not in _PASSIVE_STOP:
            count += 1
    return {"count": count, "ratio": round(count / len(sentences), 3)}


# -------------------------------------------------------------------- scoring
_SCORE_DECISIVE = {
    "62_invisible_chars", "63_placeholder_text", "64_chatbot_ref_markup",
    "65_ai_tracking_params", "66_homoglyphs", "13_article_title_noun",
    "47_chatbot_artifacts", "50_cutoff_disclaimer", "48_sycophantic",
}
_SCORE_STRONG = {
    "16_ing_tail", "20_empty_pivot_phrase", "21_outcome_speculation",
    "24_self_thoroughness", "18_not_x_just_y", "27_compulsive_intro",
    "30_diff_anchored", "17_negative_parallelism", "5_simple_yet",
    "69_canonical_slop", "71_degenerate_repetition",
}
# Keys listed here that are also demoted below never reach the weight, because the
# scoring loop tests the demoted sets first. Only rules that can score belong here.
_SCORE_SOFT = {
    "37_transition_cluster", "57_emojis", "2_model_dialect",
    "23_editorial_interjection",
}
_SCORE_STYLE_ONLY = {"60_curly_quotes", "61_hyphen_for_en_dash"}
_SCORE_REPORT_ONLY = {
    "4_hyphen_cliche", "19_filler_phrases", "22_authority_trope",
    "41_mechanical_alternation", "55_contraction_absence",
    "68_trailing_whitespace",
    # Both failed the same test the six above failed, on a corpus fetched after
    # the pattern set was frozen: 9,333 documents from 30 real American
    # textbooks. 42_opener_repetition fires on 3.5% of that human prose and 0.2%
    # of machine prose written to imitate it, a lift of 0.06, and it was already
    # only 1.08 on the main corpus at precision 0.68. 54_hedge_stacking is 0.51
    # there and 1.23 on the main corpus; academic prose hedges, which is register
    # rather than authorship. Dropping both cuts textbook false positives from
    # 5.7% to 3.9% and raises main-corpus recall at one false positive from 34.0%
    # to 40.7%, with ROC-AUC unchanged. Measured in the private benchmark, which
    # is not part of this repository, so it cannot be re-derived here.
    "42_opener_repetition", "54_hedge_stacking",
    # Three more, demoted on agreement between two corpora rather than one. Each
    # fires more on human prose than on machine prose on BOTH the textbook corpus
    # and the protocol corpora, which is what separates a real defect from one
    # corpus being unusual.
    #   58_em_dash_overuse       lift 0.30 protocol, 0.70 textbook. It fires on
    #                            19.8% of human documents and 5.9% of machine
    #                            ones. The belief that an em-dash marks machine
    #                            writing is backwards, and scoring it manufactures
    #                            false positives on people who punctuate well.
    #   17_negative_parallelism  0.67 protocol, 0.60 textbook.
    #   46_punctuation_underuse  0.86 protocol, 0.71 textbook. Counting semicolons
    #                            measures house style, not authorship.
    # Textbook false positives fall 3.9% to 1.6%, clearing the 2% line this
    # project set for itself; textbook ROC-AUC rises 0.942 to 0.958 and recall at
    # zero false positives 8.8% to 15.1%. The main corpus pays 1.4 points of
    # recall at zero false positives and gains 0.002 ROC-AUC. Measured in the
    # private benchmark, which is not part of this repository, so it cannot be
    # re-derived here.
    "58_em_dash_overuse", "17_negative_parallelism", "46_punctuation_underuse",
}
_SCORE_RHYTHM = {"40_sentence_monotony", "55_contraction_absence", "41_mechanical_alternation"}
_SCORE_MIN_WORDS = 120
_ESCALATOR_FAMILIES = set(range(1, 40)) | {47, 48, 49, 50, 51, 54, 69}
_RHYTHM_CAP = 18.0
_CONTENT_CAP = 48.0
_VOCAB_CAP = 26.0
_VOCAB_FLOOR = 12.0


def _band(score: float) -> str:
    if score <= 20:
        return "clean"
    if score <= 40:
        return "light tells"
    if score <= 60:
        return "mixed"
    if score <= 80:
        return "heavy tells"
    return "pervasive tells"


def ai_tell_score(result: dict, text: str, burst: dict, para_mono: dict, punct: dict,
                  readability: dict | None = None) -> dict:
    words = max(count_words(text), 1)
    eff = max(words, _SCORE_MIN_WORDS)

    diversity = 0.0
    content_load = 0.0
    rhythm_flags = 0
    for key, val in result.items():
        if key.startswith("_") or not isinstance(val, dict):
            continue
        if key in _SCORE_STYLE_ONLY or key in _SCORE_REPORT_ONLY or key == "1_ai_vocabulary":
            continue
        if key in _SCORE_RHYTHM:
            rhythm_flags += 1
            continue
        count = min(val.get("count", 1), 5)
        weight = 3.0 if key in _SCORE_DECISIVE else 1.0 if key in _SCORE_SOFT else 1.6
        diversity += (
            16.0 if key in _SCORE_DECISIVE
            else 10.0 if key in _SCORE_STRONG
            else 2.5 if key in _SCORE_SOFT
            else 5.0
        )
        content_load += weight * count

    density_bonus = min(10.0, content_load / eff * 1000 * 1.0)
    content_term = min(_CONTENT_CAP, diversity + density_bonus)

    cv = burst.get("cv")
    burst_term = 0.0 if cv is None else max(0.0, min(1.0, (0.45 - cv) / 0.45)) * 10.0
    pcv = para_mono.get("cv")
    mono_term = 0.0 if pcv is None else max(0.0, min(1.0, (0.4 - pcv) / 0.4)) * 8.0
    read_term = 3.0 if (readability or {}).get("uniform") else 0.0
    rhythm_term = min(_RHYTHM_CAP, rhythm_flags * 4.0 + burst_term + mono_term + read_term)

    vocab_count = result.get("1_ai_vocabulary", {}).get("count", 0)
    vocab_rate = vocab_count / eff * 1000
    vocab_term = min(_VOCAB_CAP, max(0.0, vocab_rate - _VOCAB_FLOOR) * 0.45)

    # This fires on exactly the condition that raises 46_punctuation_underuse.
    # When that rule is report-only the main loop skips it, and this term used to
    # deliver its five points anyway. Demoting a rule has to close every route its
    # evidence takes to the score, not just the obvious one.
    punct_term = (5.0 if (punct.get("checked") and punct.get("underused")
                          and "46_punctuation_underuse" not in _SCORE_REPORT_ONLY)
                  else 0.0)

    score = round(min(100.0, content_term + rhythm_term + vocab_term + punct_term))
    decisive_hits = sum(1 for k in result if k in _SCORE_DECISIVE)
    if decisive_hits >= 2:
        score = max(score, 65)
    elif decisive_hits == 1:
        score = max(score, 45)

    # _SCORE_STYLE_ONLY belongs here beside _SCORE_REPORT_ONLY. Without it,
    # 60_curly_quotes counted toward an escalation floor while being excluded
    # from the score itself, and it fires on 68.7% of human documents.
    fams = {int(k.split("_", 1)[0]) for k in result
            if not k.startswith("_") and k not in _SCORE_REPORT_ONLY
            and k not in _SCORE_STYLE_ONLY
            and k.split("_", 1)[0].isdigit()}
    if words < _SCORE_MIN_WORDS:
        content_fams = fams & _ESCALATOR_FAMILIES
        if len(content_fams) >= 3:
            score = max(score, 45)
        elif len(content_fams) >= 2:
            score = max(score, 25)
    elif words >= 400:
        if len(fams) >= 6:
            score = max(score, 45)
        elif len(fams) >= 5:
            score = max(score, 25)
    return {"score": score, "band": _band(score)}


def detect_contraction_absence(text: str) -> dict:
    first_person = len(FIRST_PERSON.findall(text))
    words = max(count_words(text), 1)
    fp_ratio = first_person / words
    if fp_ratio < 0.02:
        return {"opinion_mode": False, "ratio": round(fp_ratio, 3)}
    contractable = len(CONTRACTABLE.findall(text))
    contractions = len(CONTRACTIONS.findall(text))
    total = contractable + contractions
    if total == 0:
        return {"opinion_mode": True, "ratio": round(fp_ratio, 3), "absent": False}
    absent_ratio = contractable / total
    return {
        "opinion_mode": True,
        "first_person_ratio": round(fp_ratio, 3),
        "contractable_forms": contractable,
        "contractions": contractions,
        "absence_ratio": round(absent_ratio, 3),
        "absent": absent_ratio > 0.7,
    }


def regex_count(text: str, pattern: str, flags: int = re.IGNORECASE) -> list[str]:
    matches = re.findall(pattern, text, flags)
    out: list[str] = []
    for m in matches:
        if isinstance(m, tuple):
            out.append(next((x for x in m if x), ""))
        else:
            out.append(m)
    return [m for m in out if m]


def samples(text: str, pattern: str, flags: int = re.IGNORECASE, k: int = MAX_SAMPLES) -> list[str]:
    out: list[str] = []
    for m in re.finditer(pattern, text, flags):
        start = max(0, m.start() - 20)
        end = min(len(text), m.end() + 20)
        snippet = text[start:end].replace("\n", " ").strip()
        out.append(snippet)
        if len(out) >= k:
            break
    return out


_FENCE_OPEN = re.compile(r"^\s*(```|~~~)")
_INLINE_CODE = re.compile(r"`[^`\n]+`")


_TABLE_ROW = re.compile(r"^[ \t]*\|.*\|[ \t]*$", re.M)
_BADGE_LINE = re.compile(r"^[ \t]*(?:\[!\[[^\]]*\]\([^)]*\)\]\([^)]*\)[ \t]*)+$", re.M)
_FRONTMATTER = re.compile(r"\A---\r?\n.*?\r?\n---\r?\n", re.S)


def strip_markdown_furniture(text: str) -> str:
    def blank(m: re.Match) -> str:
        return re.sub(r"[^\n]", " ", m.group(0))
    return _BADGE_LINE.sub(blank, _TABLE_ROW.sub(blank, _FRONTMATTER.sub(blank, text)))


# ----------------------------------------------------------- pre-scan cleanup
def strip_code(text: str) -> str:
    out = []
    fence = None
    for line in text.split("\n"):
        m = _FENCE_OPEN.match(line)
        if fence is None and m:
            fence = m.group(1)
            out.append(" " * len(line))
        elif fence is not None:
            out.append(" " * len(line))
            if line.strip() == fence or line.strip().startswith(fence):
                fence = None
        else:
            out.append(line)
    blanked = "\n".join(out)
    return _INLINE_CODE.sub(lambda m: " " * len(m.group(0)), blanked)


_SCAN_CAP = 262144


def _reading_order(name: str) -> tuple:
    """Sort chapter10 after chapter2. A plain string sort puts a book's tenth chapter
    before its second, which shuffles the document the rhythm rules then read."""
    parts = re.split(r"(\d+)", name)
    return tuple((1, int(p)) if p.isdigit() else (0, p) for p in parts)


# ------------------------------------------------------------------ main scan
def scan(raw_text: str) -> dict:
    result: dict = {}
    text, evasion_defused = defuse_evasion(
        strip_markdown_furniture(strip_quoted_spans(strip_code(raw_text[:_SCAN_CAP])))
    )

    simple = [
        ("16_ing_tail", ING_TAIL, "Superficial -ing tail clauses"),
        ("3_promotional", PROMO, "Promotional language"),
        ("12_vague_attribution", VAGUE_ATTR, "Vague attributions"),
        ("36_challenges_section", CHALLENGES, "Formulaic challenges sections"),
        ("1_ai_vocabulary", AI_VOCAB, "AI vocabulary"),
        ("51_copula_avoidance", COPULA_AVOID, "Copula avoidance"),
        ("17_negative_parallelism", NEG_PARALLEL, "Negative parallelism"),
        ("17_tailing_negation", TAILING_NEG, "Tailing negation"),
        ("56_boldface", BOLD, "Boldface overuse"),
        ("33_inline_header_list", INLINE_HEADER, "Inline-header list"),
        ("60_curly_quotes", CURLY, "Curly quotes"),
        ("47_chatbot_artifacts", CHATBOT, "Chatbot artifacts"),
        ("50_cutoff_disclaimer", CUTOFF, "Knowledge-cutoff disclaimer"),
        ("48_sycophantic", SYCOPHANTIC, "Sycophantic tone"),
        ("19_filler_phrases", FILLER, "Filler phrases"),
        ("39_generic_positive_end", GENERIC_END, "Generic positive conclusion"),
        ("4_hyphen_cliche", HYPHEN_CLICHE, "Hyphenated cliché"),
        ("22_authority_trope", AUTHORITY_TROPE, "Persuasive authority trope"),
        ("31_signposting", SIGNPOSTING, "Signposting"),
        ("32_catalog_leadin", CATALOG_LEADIN, "Cataloguing lead-in"),
        ("32_catalog_pivot", CATALOG_PIVOT, "Cataloguing pivot"),
        ("20_empty_pivot_phrase", EMPTY_PIVOT, "Empty pivot phrase"),
        ("38_compulsive_conclusion", COMPULSIVE_CONCLUSION, "Compulsive conclusion phrase"),
        ("21_outcome_speculation", OUTCOME_SPECULATION, "Outcome speculation tail"),
        ("5_simple_yet", SIMPLE_YET, "Simple yet X cliché"),
        ("10_significance_inflation", SIGNIFICANCE_INFLATION, "Significance inflation"),
        ("11_notability_list", NOTABILITY_LIST, "Notability name-dropping"),
        ("15_false_range", FALSE_RANGE, "False range"),
        ("36_faux_insight", FAUX_INSIGHT, "Faux-insight setup"),
        ("32_definitional_metaphor", DEFINITIONAL_METAPHOR, "Definitional metaphor"),
        ("37_colon_reveal", COLON_REVEAL, "Colon reveal"),
        ("47_chat_residue", CHAT_RESIDUE, "Chat residue in a deliverable"),
        ("50_privacy_filler", PRIVACY_FILLER, "Speculative privacy filler"),
        ("25_question_answer", QA_RHETORICAL, "Question-answer rhetorical pattern"),
        ("24_self_thoroughness", SELF_THOROUGHNESS, "Self-thoroughness phrase"),
        ("23_editorial_interjection", EDITORIAL_INTERJECTION, "Editorial interjection"),
        ("13_article_title_noun", ARTICLE_TITLE_NOUN, "Article-title-as-proper-noun"),
        ("18_not_x_just_y", NOT_X_JUST_Y, "Not X, just Y framing"),
        ("27_compulsive_intro", COMPULSIVE_INTRO, "Compulsive intro hook"),
        ("26_concrete_evidence", CONCRETE_EVIDENCE, "Concrete-evidence defense phrase"),
        ("14_ecosystem_padding", ECOSYSTEM_PADDING, "Conservation / ecosystem padding"),
        ("63_placeholder_text", PLACEHOLDER, "Placeholder / Mad-Libs text"),
        ("64_chatbot_ref_markup", CHATBOT_REF_MARKUP, "Chatbot reference-markup leak"),
        ("65_ai_tracking_params", AI_UTM, "AI tracking params (utm_source)"),
        ("30_diff_anchored", DIFF_ANCHORED, "Diff-anchored writing"),
        ("69_canonical_slop", CANONICAL_SLOP, "Canonical marketing-slop phrase"),
    ]

    flags_re = re.IGNORECASE
    for key, pattern, label in simple:
        matches = regex_count(text, pattern, flags_re)
        if matches:
            result[key] = {
                "label": label,
                "count": len(matches),
                "samples": samples(text, pattern, flags_re),
            }

    emojis = EMOJI.findall(text)
    if emojis:
        result["57_emojis"] = {
            "label": "Emojis",
            "count": len(emojis),
            "samples": list(dict.fromkeys(emojis))[:MAX_SAMPLES],
        }

    tc = detect_title_case_headings(text)
    if tc:
        result["59_title_case_heading"] = {
            "label": "Title case in headings",
            "count": len(tc),
            "samples": [h["heading"] for h in tc[:MAX_SAMPLES]],
        }

    em = detect_em_dash_overuse(text)
    if em:
        result["58_em_dash_overuse"] = {
            "label": "Em-dash overuse (>=2 per paragraph)",
            "count": len(em),
            "samples": em[:MAX_SAMPLES],
        }

    syn = detect_synonym_cycling(text)
    if syn:
        result["8_synonym_cycling"] = {
            "label": "Synonym cycling",
            "count": len(syn),
            "samples": [", ".join(c) for c in syn[:MAX_SAMPLES]],
        }

    hedge = detect_hedge_stacking(text)
    if hedge:
        result["54_hedge_stacking"] = {
            "label": "Hedge stacking",
            "count": len(hedge),
            "samples": [h["sample"] for h in hedge[:MAX_SAMPLES]],
        }

    cta = detect_imperative_cta(text)
    if cta:
        result["3_imperative_cta"] = {
            "label": "Imperative marketing calls-to-action",
            "count": len(cta),
            "samples": cta[:MAX_SAMPLES],
        }

    frag = detect_fragmented_headers(text)
    if frag:
        result["35_fragmented_header"] = {
            "label": "Fragmented headers",
            "count": len(frag),
            "samples": [f"{f['heading']!r} / {f['filler_line']!r}" for f in frag[:MAX_SAMPLES]],
        }

    rep = detect_degenerate_repetition(text)
    if rep["degenerate"]:
        result["71_degenerate_repetition"] = {
            "label": "Degenerate repetition",
            "count": 1,
            "samples": ["%.0f%% of six-word spans repeat%s"
                        % (100 * rep["ratio"],
                           "; worst %r x%d" % rep["worst"] if rep["worst"] else "")],
        }

    op = detect_opener_repetition(text)
    if op:
        result["42_opener_repetition"] = {
            "label": "Opener repetition",
            "count": len(op),
            "samples": [f"para {h['paragraph']}: '{h['opener']}' x{h['repeats']}" for h in op[:MAX_SAMPLES]],
        }

    trans = detect_transition_clusters(text)
    if trans:
        result["37_transition_cluster"] = {
            "label": "Transition cluster overuse",
            "count": len(trans),
            "samples": [f"para {t['paragraph']}: {', '.join(t['transitions'])}" for t in trans[:MAX_SAMPLES]],
        }

    stacked = detect_stacked_adjectives(text)
    if stacked:
        result["6_stacked_adjectives"] = {
            "label": "Stacked adjective chains",
            "count": len(stacked),
            "samples": stacked[:MAX_SAMPLES],
        }

    invisible = detect_invisible_chars(raw_text)
    if invisible["count"]:
        result["62_invisible_chars"] = {
            "label": "Invisible / zero-width characters (strip)",
            "count": invisible["count"],
            "samples": _labelled_samples(invisible["chars"]),
        }

    nbsp = detect_nonstandard_spaces(raw_text)
    if nbsp["count"]:
        result["67_nonstandard_spaces"] = {
            "label": "Non-standard spaces (normalize to U+0020)",
            "count": nbsp["count"],
            "samples": _labelled_samples(nbsp["chars"]),
        }

    trailing = detect_trailing_whitespace(raw_text)
    if trailing["artifact"]:
        tsamples: list[str] = []
        if trailing["leading_whitespace"]:
            tsamples.append(f"{trailing['leading_whitespace']} leading whitespace char(s)")
        if trailing["eol_trailing_spaces"]:
            tsamples.append(f"{trailing['eol_trailing_spaces']} line(s) with trailing spaces/tabs")
        if trailing["trailing_blanks"]:
            tsamples.append(f"{trailing['trailing_blanks']} trailing space/tab char(s) at EOF")
        if trailing["trailing_newlines"] >= 2:
            tsamples.append(f"{trailing['trailing_newlines']} blank trailing newline(s) at EOF")
        result["68_trailing_whitespace"] = {
            "label": "Trailing / stray whitespace (trim)",
            "count": len(tsamples),
            "samples": tsamples,
        }

    rules = detect_decorative_rules(raw_text[:_SCAN_CAP])
    if rules:
        result["70_decorative_rules"] = {
            "label": "Decorative horizontal rules",
            "count": rules["count"],
            "samples": rules["samples"],
        }

    bullets = detect_mid_essay_bullets(text)
    if bullets["mixed"]:
        result["34_mid_essay_bullets"] = {
            "label": "Mid-essay bullet injection",
            "count": bullets["bullet_paragraphs"],
            "samples": [
                f"{bullets['bullet_paragraphs']} bullet block(s) inside "
                f"{bullets['prose_paragraphs']} prose paragraph(s)"
            ],
        }

    para_mono = detect_paragraph_monotony(text)
    if para_mono.get("monotonous"):
        result["44_paragraph_monotony"] = {
            "label": "Uniform paragraph length",
            "count": 1,
            "samples": [f"cv={para_mono['cv']} below 0.4 threshold across {para_mono['paragraphs']} paragraphs"],
        }

    contractions = detect_contraction_absence(text)
    if contractions.get("opinion_mode") and contractions.get("absent"):
        result["55_contraction_absence"] = {
            "label": "Contraction absence (opinion mode)",
            "count": contractions["contractable_forms"],
            "samples": [
                f"{contractions['contractable_forms']} full forms vs "
                f"{contractions['contractions']} contractions "
                f"(absence ratio {contractions['absence_ratio']})"
            ],
        }

    hyphen_ranges = detect_hyphen_ranges(text)
    if hyphen_ranges:
        result["61_hyphen_for_en_dash"] = {
            "label": "Hyphen-for-en-dash in numeric ranges",
            "count": len(hyphen_ranges),
            "samples": hyphen_ranges[:MAX_SAMPLES],
        }

    punct = detect_punctuation_diversity(text)
    if punct.get("checked") and punct.get("underused"):
        result["46_punctuation_underuse"] = {
            "label": "Semicolon and parenthesis underuse",
            "count": 1,
            "samples": [
                f"{punct['semicolons']} semicolons and {punct['parentheticals']} "
                f"parentheticals across {punct['words']} words"
            ],
        }

    homoglyphs = detect_homoglyphs(raw_text)
    if homoglyphs:
        result["66_homoglyphs"] = {
            "label": "Homoglyph / mixed-script confusables (fold to ASCII)",
            "count": len(homoglyphs),
            "samples": homoglyphs[:MAX_SAMPLES],
        }

    burst = detect_burstiness(text)
    if burst["monotonous"]:
        result["40_sentence_monotony"] = {
            "label": "Sentence-length monotony",
            "count": 1,
            "samples": [f"cv={burst['cv']} below 0.35 threshold"],
        }

    cadence = detect_cadence_alternation(text)
    if cadence["mechanical"]:
        result["41_mechanical_alternation"] = {
            "label": "Mechanical sentence-length alternation",
            "count": 1,
            "samples": [
                f"zigzag={cadence['zigzag']} across {cadence['sentences']} sentences"
            ],
        }

    dialect_claude = regex_count(text, MODEL_DIALECT_CLAUDE)
    dialect_gpt = regex_count(text, MODEL_DIALECT_GPT)
    if len(dialect_claude) + len(dialect_gpt) >= 2:
        dsamples: list[str] = []
        if dialect_claude:
            dsamples.append("claude-dialect: " + ", ".join(dict.fromkeys(dialect_claude))[:100])
        if dialect_gpt:
            dsamples.append("gpt-dialect: " + ", ".join(dict.fromkeys(dialect_gpt))[:100])
        result["2_model_dialect"] = {
            "label": "Model-dialect vocabulary",
            "count": len(dialect_claude) + len(dialect_gpt),
            "samples": dsamples,
        }

    readability = detect_readability_consistency(text)
    passive = detect_passive_voice(text)
    score = ai_tell_score(result, text, burst, para_mono, punct, readability)
    result["_metrics"] = {
        "scanned_chars": min(len(raw_text), _SCAN_CAP),
        "truncated": len(raw_text) > _SCAN_CAP,
        "sentences": burst["sentences"],
        "length_cv": burst["cv"],
        "has_short_sentence": burst["has_short"],
        "monotonous": burst["monotonous"],
        "paragraph_cv": para_mono.get("cv"),
        "paragraph_monotonous": para_mono.get("monotonous"),
        "invisible_chars": invisible["count"],
        "evasion_defused": evasion_defused,
        "nonstandard_spaces": nbsp["count"],
        "trailing_newlines": trailing["trailing_newlines"],
        "eol_trailing_spaces": trailing["eol_trailing_spaces"],
        "leading_whitespace": trailing["leading_whitespace"],
        "first_person_ratio": contractions.get("first_person_ratio", contractions.get("ratio")),
        "semicolons_per_1k": punct.get("semicolons_per_1k"),
        "parentheticals_per_1k": punct.get("parentheticals_per_1k"),
        "passive_voice_ratio": passive.get("ratio"),
        "readability_fk_stdev": readability.get("fk_stdev"),
        "readability_uniform": readability.get("uniform"),
        "cadence_zigzag": cadence.get("zigzag"),
        "homoglyphs": len(homoglyphs),
        "ai_tell_score": score["score"],
        "ai_tell_band": score["band"],
        "patterns_flagged": sum(1 for k in result if not k.startswith("_")),
    }
    # Third place the same asymmetry appeared. Style-only rules are excluded
    # from the score, so counting them here inflated the confidence attached to
    # it: a document could be reported as having more independent evidence than
    # any of it had reached the number.
    scored_fams = sum(1 for k in result
                      if not k.startswith("_")
                      and k not in _SCORE_REPORT_ONLY
                      and k not in _SCORE_STYLE_ONLY)
    result["_metrics"].update(score_confidence(count_words(text), scored_fams))

    return result


_CONFIDENCE_FLOOR = 120
_CONFIDENCE_SOLID = 300


# ----------------------------------------------------------------- confidence
def score_confidence(words: int, families: int) -> dict:
    """How much the score is worth. Short text gives the scorer too little to work
    with: a 20-word snippet can cross a band on one phrase. Reported rather than
    hidden, so a caller can decline to act on a number that has not earned it."""
    if words < 40:
        return {"confidence": "none",
                "confidence_reason": "%d words: too short to score. Treat any "
                                     "number here as noise." % words}
    if words < _CONFIDENCE_FLOOR:
        return {"confidence": "low",
                "confidence_reason": "%d words: below the %d-word floor, so one "
                                     "phrase can move the band."
                                     % (words, _CONFIDENCE_FLOOR)}
    if words < _CONFIDENCE_SOLID and families <= 1:
        return {"confidence": "low",
                "confidence_reason": "%d words and %d scored pattern: not enough "
                                     "independent evidence." % (words, families)}
    if words < _CONFIDENCE_SOLID:
        return {"confidence": "moderate",
                "confidence_reason": "%d words: usable, but %d or more is where "
                                     "the score settles." % (words, _CONFIDENCE_SOLID)}
    return {"confidence": "high", "confidence_reason": ""}


# ----------------------------------------------------------- document formats
_ZIP_DOC = {
    ".docx": ("word/document.xml",), ".docm": ("word/document.xml",),
    ".pptx": ("ppt/slides/slide",), ".pptm": ("ppt/slides/slide",),
    ".xlsx": ("xl/sharedStrings.xml",), ".xlsm": ("xl/sharedStrings.xml",),
    ".odt": ("content.xml",), ".odp": ("content.xml",), ".ods": ("content.xml",),
    ".epub": (".xhtml", ".html"),
}
_BLOCK_TAGS = {"p", "h", "br", "tab", "tr", "title", "caption"}
_TEXT_TAGS = {"t", "seg", "span"}


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


_NAMED_ENTITY = re.compile(rb"&([A-Za-z][A-Za-z0-9]{1,30});")
_XML_ENTITY = {b"amp", b"lt", b"gt", b"quot", b"apos"}


def _numeric_entities(data: bytes) -> bytes:
    """XML defines five entity names; EPUB and XHTML use the HTML set. An
    &nbsp; or an &mdash; is a parse error, and the chapter it sits in used to
    be dropped without a word, so the names are rewritten as numeric
    references before the parser sees them."""
    from html.entities import name2codepoint

    def sub(m):
        name = m.group(1)
        if name in _XML_ENTITY:
            return m.group(0)
        cp = name2codepoint.get(name.decode("ascii"))
        return b"&#%d;" % cp if cp else m.group(0)

    return _NAMED_ENTITY.sub(sub, data)


def extract_office_text(path: str) -> str:
    """Pull the visible text out of a zip-based document. Standard library only."""
    import xml.etree.ElementTree as ET
    import zipfile

    ext = os.path.splitext(path)[1].lower()
    wanted = _ZIP_DOC.get(ext)
    if not wanted:
        return ""
    out: list = []
    with zipfile.ZipFile(path) as z:
        names = [n for n in z.namelist() if any(w in n for w in wanted)]
        names.sort(key=_reading_order)
        for name in names:
            try:
                root = ET.fromstring(_numeric_entities(z.read(name)))
            except (ET.ParseError, KeyError):
                continue
            buf: list = []
            for el in root.iter():
                tag = _local(el.tag)
                if tag in _TEXT_TAGS and el.text:
                    buf.append(el.text)
                elif tag in _BLOCK_TAGS:
                    if buf and buf[-1] != "\n":
                        buf.append("\n")
                    if el.text and tag not in _TEXT_TAGS:
                        buf.append(el.text)
                if el.tail and el.tail.strip():
                    buf.append(el.tail)
            chunk = "".join(buf)
            if chunk.strip():
                out.append(chunk)
    text = "\n\n".join(out)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


# ------------------------------------------------------------------ error bar
def score_interval(text: str, resamples: int = 60, seed: int = 11) -> dict:
    """A confidence interval on the score, by resampling the document's own
    sentences with replacement and rescoring. Answers a question no threshold can:
    how much of this number is the document, and how much is which sentences
    happened to be in it. Costs `resamples` extra scans, so it is opt-in."""
    import random

    sents = [s for s in split_sentences(text) if s.strip()]
    if len(sents) < 4:
        return {"score_ci": None,
                "score_ci_note": "fewer than 4 sentences: no interval"}
    rnd = random.Random(seed)
    n = len(sents)
    draws = []
    for _ in range(resamples):
        sample = " ".join(rnd.choice(sents) for _ in range(n))
        draws.append(scan(sample)["_metrics"]["ai_tell_score"])
    draws.sort()
    lo = draws[int(0.025 * resamples)]
    hi = draws[min(resamples - 1, int(0.975 * resamples))]
    return {"score_ci": [lo, hi], "score_ci_resamples": resamples,
            "score_ci_note": "2.5th to 97.5th percentile over %d sentence "
                             "resamples" % resamples}


def extract_notebook_text(path: str) -> str:
    """Markdown cells out of a Jupyter notebook. Code cells and outputs are not
    prose and are left alone, the same way the guard leaves source files alone."""
    try:
        with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
            nb = json.load(f)
    except (OSError, ValueError):
        return ""
    out = []
    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "markdown":
            continue
        src = cell.get("source", "")
        out.append("".join(src) if isinstance(src, list) else str(src))
    return re.sub(r"\n{3,}", "\n\n", "\n\n".join(out)).strip()


_UTF16_BOM = (b"\xff\xfe", b"\xfe\xff")
_UNREADABLE_EXT = {".pdf", ".rtf"}


def _decode_text(data: bytes) -> str:
    """UTF-16 is what PowerShell redirection writes by default. Decoded as
    UTF-8 it becomes one NUL per character, which the character layer then
    reports as thousands of invisible characters in ordinary human prose.
    Anything else holding a NUL byte is not text at all, and the control bytes
    it decodes to would be reported the same invented way, so it reads as
    nothing rather than as a document full of hidden characters."""
    if data[:2] in _UTF16_BOM:
        return data.decode("utf-16", errors="replace")
    if b"\x00" in data:
        return ""
    return data.decode("utf-8-sig", errors="replace")


def read_source(paths: list) -> tuple:
    """The text, plus the line ending it arrived with so --clean can put it
    back. The scanner only ever sees LF, which is what every published number
    was measured on."""
    if paths:
        ext = os.path.splitext(paths[0])[1].lower()
        if ext in _ZIP_DOC:
            return extract_office_text(paths[0]), "\n"
        if ext == ".ipynb":
            return extract_notebook_text(paths[0]), "\n"
        if ext in _UNREADABLE_EXT:
            return "", "\n"
        with open(paths[0], "rb") as f:
            text = _decode_text(f.read())
        newline = "\r\n" if "\r\n" in text else "\n"
        return text.replace("\r\n", "\n").replace("\r", "\n"), newline
    return _decode_text(sys.stdin.buffer.read()), "\n"


def read_input(paths: list) -> str:
    return read_source(paths)[0]


USAGE = """usage: detect.py [--clean] [--ci] [--] [FILE]

Scans FILE, or stdin when no file is given, and prints the findings as JSON.

  --clean   print the scrubbed text instead of the JSON report. For a .docx, .epub,
            .odt or .ipynb this prints the extracted plain text, not a rebuilt
            document, so redirecting it back over the original destroys the file.
  --ci      add a resampled interval to the score
  --        stop reading options, so a FILE may begin with a dash
  --help    this message
"""


def main() -> int:
    import zipfile

    for stream in (sys.stdin, sys.stdout):
        if hasattr(stream, "reconfigure"):
            # newline="" or Windows rewrites every LF in the cleaned text to
            # CRLF, so no document could round-trip byte for byte.
            stream.reconfigure(encoding="utf-8", errors="replace", newline="")
    paths: list = []
    flags: set = set()
    literal = False
    for arg in sys.argv[1:]:
        if literal or not arg.startswith("-"):
            paths.append(arg)
        elif arg == "--":
            literal = True
        elif arg in ("--clean", "--ci"):
            flags.add(arg)
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return 0
        else:
            print(json.dumps({"error": f"unknown option: {arg}. Try --help."}),
                  file=sys.stderr)
            return 2
    if len(paths) > 1:
        # Scanning the first and dropping the rest in silence was the defect. Erroring
        # would break a shell glob that used to work, so say so and carry on.
        print("detect.py: %d files given; scanning %s only, one at a time is supported."
              % (len(paths), paths[0]), file=sys.stderr)
        del paths[1:]
    try:
        text, newline = read_source(paths)
    except (OSError, zipfile.BadZipFile) as e:
        reason = getattr(e, "strerror", None) or e
        print(json.dumps({"error": f"cannot read input: {reason}"}), file=sys.stderr)
        return 1
    if not text.strip():
        print(json.dumps({"error": "empty input"}), file=sys.stderr)
        return 1
    if "--clean" in flags:
        cleaned = clean_text(text)
        # A file that ended in a newline still should.
        if text.endswith("\n"):
            cleaned += "\n"
        sys.stdout.write(cleaned.replace("\n", newline) if newline != "\n" else cleaned)
        return 0
    result = scan(text)
    if "--ci" in flags:
        result["_metrics"].update(score_interval(text))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
