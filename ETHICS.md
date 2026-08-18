# Ethics

## What it is

A writing-quality instrument. It scores prose against a documented catalogue and
rewrites what it flags.

**It is not an authorship classifier**, and the names it prints were chosen so
that no part of the output says otherwise. `scripts/detect.py` puts a score in
one of five bands, `clean`, `light tells`, `mixed`, `heavy tells` and
`pervasive tells`, and the hooks print the same cut-offs as `reads clean`,
`reads mostly clean`, `reads with some AI tells`, `reads with heavy AI tells` and
`reads with pervasive AI tells`. Every one of those ten names describes the
prose. None of them names an author, a writer, a tool or an origin.

What a band asserts is the density of documented patterns in the text, and
nothing beyond it. Behind a band there is a weighted count of the patterns in
`references/patterns.md` and no model, no probability and no comparison against
any authored sample. `pervasive tells` says the document carries a lot of what
the catalogue lists. It does not say a machine produced it, it does not say a
person did. The benchmark further down shows both score separation and poor
threshold sensitivity, which is exactly why a band cannot settle authorship.
Never use a band to accuse anyone.

## What it is not

It is not a detector-evasion tool, and the distinction is structural rather than
rhetorical.

It does optimise against a score: its own. The contract asks for a rewrite when
`detect.py` flags a span, and the skill re-scores its own output. That loop is
the product, and pretending otherwise would be the dishonest version of this
paragraph.

Its own score is published and inspectable: every rule is in
`references/patterns.md` and every implemented rule is in `scripts/detect.py`.
Optimising against a published rulebook is editing. Optimising against someone
else's authorship classifier would be evasion.

No third-party detector is in this repository. Nothing here bundles, clones,
downloads or calls one, no threshold, weight or rule here is derived from one,
and no verdict of any other engine is adopted. The only programs this tool ever
starts are a Python interpreter running `scripts/detect.py` and Node running
`hooks/sloptrim-stats.js`, both of which ship here.

The honest qualification is about history rather than about this tree. The
benchmark that produced the measurements cited below is held privately and is
not published with the tool; inside it, rewrites were also scored by two
open-source rule-based writing checkers, read after the fact as a corroboration
column. Lowering this engine's own score is trivial, so an improvement only this
engine could see would have been a fitted regex rather than better writing. That
column was never a target and nothing was fed back from it into calibration. It
is not runnable here, and no part of it ships.

These will not be added, and pull requests implementing them will be closed: a
third-party detector consulted at runtime, whether bundled or called; any
objective, threshold or rule tuned against one's score; any feature whose purpose
is passing a plagiarism, integrity or authorship check; any benchmark reporting
"detectors defeated" as success.

The tool reaches no network at all, enforced by `tests/test_no_network.py`, which
walks every `.py`, `.js`, `.mjs`, `.cjs`, `.ps1` and `.sh` file in the repository
rather than a fixed list, and fails if any of them gains the capability. That
includes `hooks/sloptrim-statusline.ps1`, which ships but which nothing
registers: it is an optional PowerShell statusline for Windows, pointed at by
Claude Code's `statusLine` setting if you want one, and it prints the level
sloptrim is running at. The claim fails the build rather than sitting in a
README.

## The tension, stated

Rewriting prose so it reads better will, as a side effect, lower the score an AI
detector assigns it. Detectors key on the markers of machine-flavoured writing,
so removing those markers reduces detectability. This is unavoidable.

It was measured rather than assumed, in the benchmark held privately, and it
split in two. The always-on contract showed nothing: across twenty
transcript-verified pairs, mean change +2.25 with a bootstrap 95% CI of -5.65 to
+9.90 and a sign test at p = 0.27, which is 20 pairs against the 40 the protocol
asks for, so unresolved rather than settled. The rewrite is where the effect is
real: in one run drawn from corpora the phrase lists never saw, an independent
rule engine's score fell on seven of the eight machine documents, three of them
by more than 40 points. Those numbers are reported because a reader is owed the
cost, not because the fall is an achievement. Nothing in this repository
recomputes any of them.

## Academic use

If your institution requires disclosure of AI assistance, this tool does not
remove that requirement. It changes how a draft reads, not who wrote it. Using it
to conceal assistance where disclosure is required is misuse: the licence permits
it, this document says do not.

The legitimate uses are ordinary. Cleaning a draft you wrote with AI assistance
and will disclose. Editing a translated or non-native-English manuscript into
more natural prose. Teaching what the markers actually are.

## On accusing people

Do not use the score to decide whether a student, colleague or applicant used AI.
It cannot answer that question, and here is the specific shape of what it cannot
do.

**It cannot identify current frontier model output reliably.** In a public
matched benchmark its score achieved ROC-AUC 0.762–0.946 across five GPT-4o,
Claude 3.5 Sonnet and o1-pro arms. In a separate 30-pair GPT-5.6 Sol run it
achieved ROC-AUC 0.965, yet the normal product threshold flagged none of the
generated articles; strict mode flagged 12 of 30. A ranking statistic and a
threshold decision answer different questions, and neither proves origin.

**It does not track machine authorship even on old models.** Base-model output
scored like human writing, with three unaligned models averaging 14.6 to 15.3
against a human 13.1 and none of them flagged, while the instruction-tuned
variant of one averaged 28.3. What the instrument appears to measure is a writing
register that alignment training produces, not who or what produced the text.

**A low score is not evidence of anything.** Any writer who edits for the
patterns in the catalogue lands in `clean`, whatever wrote the first draft, which
is the entire purpose of the tool.

**A high score is not evidence either.** Formal, edited, translated and
non-native English prose carries several of these markers for reasons that have
nothing to do with a model.

The current measurements, protocol, source revisions, hashes, confidence
intervals and limitations are recorded in
[`docs/research/frontier-benchmark-results.md`](docs/research/frontier-benchmark-results.md).
Private legacy measurements are not used as evidence for the current product
claim.

## The three counts

Three different numbers describe this catalogue and they are easy to confuse, so
all three are stated here and all three are measured in this repository.

`references/patterns.md` documents **71 patterns**. **62** of them have a
detector in `scripts/detect.py` and the remaining **9** need a reading, which
happens during the rewrite. Of the 62, **50 can move the score** and **12** are
reported as writing advice and count for nothing.

Thirteen detector rules are demoted out of the score, 11 to report-only and 2 to
style-only. They land on thirteen catalogue numbers, but only twelve patterns end
up advice-only, because number 17 carries two rules and keeps the one that still
scores.

Why those rules were demoted is half measurement and half argument, and the two
halves deserve different weight.

Measured, in the private benchmark: per-rule lift on two independent corpora. A
scored rule that fires more often on human prose than on machine prose is a
defect whatever it does for recall. Several of the demoted rules fired hardest on
edited academic prose, which avoids contractions, stacks hyphenated compounds and
uses em-dashes more than machines do rather than less. Demoting them took false
positives on American textbook passages from 3.90% to 0.85%.

A judgment, not a finding: that the same rules taxed writers working in a second
language hardest of all. It is a reasonable reading of what those rules key on,
and nothing measures it. No corpus of non-native English was benchmarked. Treat
that part as reasoning from the academic arm rather than as a result.

The threshold is set conservatively for the same reason. On prose that predates
any public language model, false positives were 0.00% of 529 PubMed abstracts and
0.00% of 939 arXiv abstracts.

## Privacy

Nothing leaves your machine. No network code, no telemetry, no accounts. The only
state on disk is a one-word mode flag and a small per-session ledger holding file
names and scores, never your text, swept after a week.

## Provenance marking

`detect.py --clean` removes zero-width and non-printing characters and folds
mixed-script lookalike letters back to Latin. Mostly these are copy-paste
artefacts, and the scrub is written for those.

No watermarking scheme is targeted, and the honest version of that sentence needs
a qualification. The rule is a character class, not a signature: anything the
Unicode database marks format, control or default-ignorable, plus the tag and
variation-selector planes. Anything hidden in those planes is removed along with
the debris, because a category-driven rule cannot tell the two apart and is not
asked to try. Nothing in the detector knows what any provider's marking looks
like, no marking is reverse-engineered, and no output is checked for one.
Statistical watermarks such as SynthID-Text live in token choice rather than in
stray characters and are untouched by all of this.

The label the detector prints says what it does. It reads
"Invisible / zero-width characters (strip)". Stripping a provider's
machine-readable AI marking to disguise synthetic content may carry obligations
under the EU AI Act, which is a further reason no feature aimed at one will be
added here.

## Reporting misuse

If you find this project used or advertised as a detection-bypass service, open
an issue. That is a use the maintainer will publicly disown.
