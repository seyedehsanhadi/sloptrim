# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.9.1] - 2026-08-17

Fixes found by an external review and by an adversarial pass over the 0.9.0 line. No rule
was added, removed or reweighted. Every document scores exactly what it scored before,
verified key by key over 1,211 documents, so any figure measured against 0.9.0 still
stands.

### Fixed

- The detector is found on Windows installs where the Microsoft Store alias answers to
  `python`. A change late in the 0.9.0 line stopped the launcher search at the first name
  that ran and failed, so on those machines nothing was scored and `doctor` reported the
  detector broken. It now stops only on a timeout and otherwise keeps trying the next
  name. `tests/interp.js` fails if that is undone.
- `/sloptrim check` accepts a quoted path. Windows "Copy as path" wraps the path in
  quotes, and the quotes became part of the filename, so the file was reported unreadable
  and the error echoed a path that was correct all along. A leading `@` from file
  completion is stripped for the same reason.
- `/sloptrim init` writes a portable contract. It had been baking the detector's absolute
  path into `AGENTS.md`, which is a file people commit: it carried the author's home
  directory and account name to anyone who read the repository, and pointed a teammate's
  agent at a path that does not exist on their machine. The written contract now names
  `$CLAUDE_PLUGIN_ROOT` instead.
- Instruction files are exempt by exact name again. Widening the exemption to the filename
  stem, so that `SKILL.pdf` would be skipped like `SKILL.md`, also stopped `agents.txt`,
  `memory.txt` and `claude.rst` being scored at all. The stem now applies only outside the
  prose extensions, where `SKILL.pdf` lives and no ordinary draft does.
- A file whose name merely contains `node_modules`, such as `node_modules.md`, is scored.
  Only a real `node_modules` directory is skipped.
- Two paths on the command line scan the first and say so on standard error. It had been a
  hard error, which broke a shell glob that used to work.
- The guard says when a score covers only the first 256 KB of a longer file. The scan stops
  there while the guard accepts up to 512 KB, and the nudge had reported the score as
  though it covered the whole document.
- The status line validates `SLOPTRIM_DEFAULT_MODE` the way the hooks do, so an
  unrecognised value cannot hide the status segment while the hooks run at full.
- A session already running when the plugin updates keeps reading its existing ledger
  rather than starting empty.
- Records written before this release carry no flag for whether they were over the
  threshold. `/sloptrim show` had been describing them as under it whatever they scored,
  and now says only that tells were found.

### Added

- A welcome shown once on first run: what the tool does, the four commands, and that there
  is no website, no account and no upload.
- Expanded Python and hook regression suites.

### Changed

- `--clean` removes every run of whitespace at the end of a line, including the two spaces
  that write a Markdown hard break, and rule 68 counts them again. Sparing them was tried
  and reverted: it made the rule depend on how a file renders, which the text alone does
  not settle, and it spared the same two spaces in `.txt` and `.rst`, where they are only
  debris. This restores the 0.9.0 release behaviour exactly. A Markdown file whose only
  finding is a hard break will report trailing whitespace; no score moves, because that
  rule reports and does not weigh.

## [0.9.0] - 2026-08-11

First release. Pre-1.0: the command surface and the score calibration may still move.

### Added

- A writing contract, injected at session start and into every subagent, that shapes prose as the agent writes it. Prose only; code, config and commits are untouched.
- A guard on prose saved through supported file-edit tools, up to 512 KB for plain text and 4 MB for supported archives. It scores the file 0 to 100 against a catalogue of 71 documented patterns, names the ones that fired, and asks for the flagged spans to be fixed.
- The catalogue itself, in `references/patterns.md`, with a worked Before and After for every entry. 62 of the 71 have a detector in `scripts/detect.py`; the other 9 need a reading and are worked during the rewrite.
- Thirteen detector rules held out of the score, as markers of formal register or of typesetting rather than of machine authorship. They fall on 13 catalogue numbers, but number 17 keeps a second rule that still scores, so 12 numbers carry no weight and 50 still do.
- Five bands over the score: `clean` (0-20), `light tells` (21-40), `mixed` (41-60), `heavy tells` (61-80), `pervasive tells` (81-100). Each band describes the prose. None of them names an author.
- `scripts/detect.py`, the detector behind both the contract and the guard. Deterministic, Python standard library only, no model, no telemetry, and no socket: `tests/test_no_network.py` walks every script in the repository and fails if one gains the capability.
- Twenty formats read with no dependencies: ten zip-based (docx, docm, pptx, pptm, xlsx, xlsm, odt, odp, ods, epub), Jupyter notebooks, and nine plain-text including LaTeX and reStructuredText.
- `--clean`, which strips invisible characters, normalises non-standard spaces, folds homoglyphs to ASCII and trims stray whitespace, leaving visible content alone. `--ci` adds a resampled interval to the score.
- `/sloptrim` commands for the level, a one-file check, the install diagnosis, and writing the contract to `AGENTS.md`. A rule file for Cursor, generated from the same contract the hook injects and pinned to it by a test.
- A Python suite and a hook suite. Both run offline.
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

[0.9.1]: https://github.com/seyedehsanhadi/sloptrim/releases/tag/v0.9.1
[0.9.0]: https://github.com/seyedehsanhadi/sloptrim/releases/tag/v0.9.0
