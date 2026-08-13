# Contributing

The most useful thing you can send is **a document this scores wrongly**: human writing it flags, or machine writing it misses. Attach the text, or a way to reproduce it. Disagreeing with the method is just as welcome.

## Running the checks

```bash
python -m pytest tests/ -q      # 97 tests
bash tests/test_hooks.sh        # 49 hook checks
python scripts/detect.py FILE   # JSON: patterns, metrics, the 0-100 score and its band
```

Both suites are offline and need no fixture beyond the repository. CI runs them, and the documentation checker, on Linux, Windows and macOS for every push and pull request; run them yourself before you send anything.

## Before a change to the detector

Two rules govern the scoring set, and neither one can be checked from here.

**A scored pattern may not fire more on human writing than on machine writing.** A rule that argues against its own conclusion is worse than no rule. Thirteen detector rules are held out of the score, most of them for failing that test and the rest for measuring typesetting instead of authorship. The measurements behind the demotions sit in the comments around `_SCORE_REPORT_ONLY` in `scripts/detect.py`.

**A scoring change must hold on a corpus this project tuned on and one it has never seen.** A change that helps one and hurts the other is overfitting.

The harness that measures both, and every corpus it reads, is held privately and is not part of this repository. Nothing here re-derives a published figure, so a proposal that turns on one has to arrive with its own measurement, or wait for the maintainer to run it.

## Conventions

- **Python standard library only** in `scripts/` and `hooks/`, and no network anywhere. `tests/test_no_network.py` walks every `.py`, `.js`, `.mjs`, `.cjs`, `.ps1` and `.sh` in the tree and fails on the first socket.
- **Comments are for a decision a reader would otherwise undo**, usually a measurement. The reason behind a fix belongs in the test that pins it.
- Section rules in `scripts/detect.py` are a dashed line ending at column 78 with the section name at the end, so they scan as a column down the file.
- Line endings are LF, enforced by `.gitattributes`.
- The Cursor rule is generated from the contract in `hooks/sloptrim-lib.js`, not written by hand. `tests/test_reach.py` fails if the two copies drift, so edit the hook and regenerate.

## Adding a pattern

A pattern needs a number, not an impression. Put it in `references/patterns.md` with a real Before and After, wire it into `scripts/detect.py`, then report what it measures. If it fires more on human prose than on machine prose it goes in `_SCORE_REPORT_ONLY`, where it is reported as writing advice and contributes nothing to the score. Eleven keys live there today; with the two typesetting rules in `_SCORE_STYLE_ONLY`, 12 of the 71 catalogue numbers carry no weight and 50 still do.

Worked examples must not invent facts, and must not name a real company, person, regulator or journal. Filling a template slot with a plausible name and address, or repairing a vague attribution by inventing a survey, is the exact failure the catalogue tells writers to avoid. `tests/test_catalogue.py` runs the detector over every After example in the catalogue and every Before example against its own pattern, so a new entry has to survive its own rule in both directions.

## Regenerating the recorded session

```bash
python record/anim.py           # redraws assets/demo-light.svg and assets/demo-dark.svg
```

It draws from `record/session.json`, which `record/session_capture.py` writes by firing the real hooks with the payloads Claude Code sends. `anim.py` refuses to write if a run it is asked to draw is missing from the capture, or if a narration label strays out of its grey. Redraw before you change either script, so the diff shows only what you meant to change.
