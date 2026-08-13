# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.9.0] - 2026-08-11

First release. Pre-1.0: the command surface and the score calibration may still move.

### Added

- A writing contract, injected at session start and into every subagent, that shapes prose as the agent writes it. Prose only; code, config and commits are untouched.
- A guard on every prose file the agent saves. It scores the file 0 to 100 against a catalogue of 71 documented patterns, names the ones that fired, and asks for the flagged spans to be fixed.
- The catalogue itself, in `references/patterns.md`, with a worked Before and After for every entry. 62 of the 71 have a detector in `scripts/detect.py`; the other 9 need a reading and are worked during the rewrite.
- Thirteen detector rules held out of the score, as markers of formal register or of typesetting rather than of machine authorship. They fall on 13 catalogue numbers, but number 17 keeps a second rule that still scores, so 12 numbers carry no weight and 50 still do.
- Five bands over the score: `clean` (0-20), `light tells` (21-40), `mixed` (41-60), `heavy tells` (61-80), `pervasive tells` (81-100). Each band describes the prose. None of them names an author.
- `scripts/detect.py`, the detector behind both the contract and the guard. Deterministic, Python standard library only, no model, no telemetry, and no socket: `tests/test_no_network.py` walks every script in the repository and fails if one gains the capability.
- Twenty formats read with no dependencies: ten zip-based (docx, docm, pptx, pptm, xlsx, xlsm, odt, odp, ods, epub), Jupyter notebooks, and nine plain-text including LaTeX and reStructuredText.
- `--clean`, which strips invisible characters, normalises non-standard spaces, folds homoglyphs to ASCII and trims stray whitespace, leaving visible content alone. `--ci` adds a resampled interval to the score.
- `/sloptrim` commands for the level, a one-file check, the install diagnosis, and writing the contract to `AGENTS.md`. A rule file for Cursor, generated from the same contract the hook injects and pinned to it by a test.
- 97 Python tests and 53 hook checks. Both suites run offline.
- The recorded session in the README, and the two scripts behind it: `record/session_capture.py` fires the real hooks with the payloads Claude Code sends and writes `record/session.json`, and `record/anim.py` draws the two SVGs from that capture.

### Where the measurements come from

The figures quoted in [README.md](README.md), in [CITATION.cff](CITATION.cff) and in the comments inside `scripts/detect.py` were measured in a benchmark the author holds privately. Neither that harness nor any corpus is part of this repository, nothing here recomputes any of them, and no command in this release re-derives one. They are cited as results obtained elsewhere, and that is the only standing they have here.

### What it does not do

- It does not say who or what wrote a document. It is not an authorship classifier and must not be used as one. See [ETHICS.md](ETHICS.md).
- It cannot tell you whether a current frontier model wrote something. Measured against one, the separation was close to chance.
- It does not judge whether a document is true, or whether it is any good. It counts documented patterns and reports the count.
- The score is document-level and moves with length. Splitting one file in two can put the halves in a different band from the whole.
- Dense formal exposition carries several of the catalogue patterns as ordinary register, which is why 13 rules are held out of the score and why `strict` will flag a good deal of careful human writing.
- The writing contract has no measured effect beyond its banned-word list, on the one model it was tested against, in a test half the size the protocol asked for. Open rather than settled.
- English only.
- A file written by a `Bash` command reaches disk without passing `Write` or `Edit`, so the guard never sees it. PDF and RTF are recognised and noted in the session ledger, never read.
- A template holding a merge field cannot clear the guard. `[Name]` raises a decisive rule and floors the score at 45, and filling the slot would mean inventing a name.

[0.9.0]: https://github.com/seyedehsanhadi/sloptrim/releases/tag/v0.9.0
