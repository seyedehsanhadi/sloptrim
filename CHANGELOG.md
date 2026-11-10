# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Fixed

- A lone zero-width character or a bare `xxx` no longer lifts a document to 45. A zero-width space often rides along when text is copied from a web page, and `xxx` is how people redact a name. Invisible characters now count as decisive evidence from three up, and `xxx` counts only beside a real template slot. One of them still adds its ordinary points, is still reported and is still removed by `--clean`. Other markers, such as `[Your Name]`, an AI tracking link or a chatbot citation token, behave as before.
- Double spaces, tabs and non-breaking spaces between words no longer hide phrase patterns. They fold to one space before matching, and the character layer still reports them.
- An all-caps bracket counts as a template slot only when it names one, such as `[COMPANY]`, `[YOUR NAME]` or `[XX]`. Citation keys and labels such as `[RFC2119]`, `[UNICODE]` and `[USEPA]` were read as slots before, and each one lifted its document to 45. Of 250 human-written RFCs, 189 were flagged at the default threshold; 2 are now. Mixed-case slots such as `[Your Name]` are unchanged.

## [0.9.6] - 2026-10-22

### Added

- `SLOPTRIM_MODE` sets the level for one run: `off`, `lite`, `full` or `strict`. It beats the saved level and is never written back. Before this, a headless code job could only skip the prose contract (about 1,100 tokens at session start and 900 per subagent) by disabling the plugin, because the first session saves its level and the saved level always won. While it is set, `/sloptrim status`, `doctor` and level changes say so. With the variable unset, every hook behaves exactly as in 0.9.5.

## [0.9.5] - 2026-10-22

### Fixed

- Curly apostrophes match like straight ones. `Let’s dive in`, `it’s worth noting` and `don’t` were missed before, and `it’s` counted as two words. Across the 341 bench documents that use `’`, the score now equals the straight-apostrophe version.
- Signposting catches every phrase the catalogue lists, including "bear with me", "let's unpack this" and "what follows is".
- "Great news!", "Ever wanted to ...?" and "Fundamentally," could never match, because punctuation stood before a word boundary. They match now.
- "In recent years," is no longer listed under compulsive intro hooks. It never matched, and turning it on lifted human research abstracts from clean to light tells.

### Changed

- The public benchmark was re-run with this detector. ROC-AUC moved from 0.946 to 0.943 for GPT-4o, from 0.838 to 0.832 for paraphrased GPT-4o and from 0.762 to 0.783 for humanized o1-pro; Claude 3.5 Sonnet and o1-pro are unchanged. Default flag rates (above 40) are unchanged on every arm. In strict mode (above 20), 5 of GPT-4o's 30 human articles are flagged instead of 3: one quotes a source saying "It's not just the heat, it's the flavors", the other writes "Let's break it down". Both used curly apostrophes, and their straight-apostrophe versions were already flagged before. Strict mode also catches one more humanized o1-pro article (13 of 30). The chart's paraphrased GPT-4o bar had been drawn at 0.837 and now matches its label.

## [0.9.4] - 2026-10-05

### Fixed

- Code is protected everywhere: Markdown fences, indented blocks and inline spans stay out of scoring, character checks and `--clean`, byte for byte.
- LaTeX gets its own lexer. Math, comments, preambles, citation keys, `verbatim` and inline listings are skipped; body text and `\textbf{}` contents are still read.
- Word code is skipped when it carries an explicit code style (`Code`, `SourceCode`, `HTMLPreformatted`, ...). Plain monospace prose is still read.
- A short quote inside your own text no longer counts against you. A draft written entirely as blockquotes still does.
- The file guard and `/sloptrim check` pass the real path, so `.tex` files get TeX handling.
- `/sloptrim doctor` no longer implies the host has loaded the hooks.
- Catalogue examples stop adding facts their Before text never had.

## [0.9.3] - 2026-09-05

### Fixed

- Long invisible-tag and whitespace runs no longer exhaust the saved-file guard's timeout.
- Markdown fences and indented code stay out of prose scoring.
- Spreadsheet extraction follows cell references and preserves cell boundaries.
- OpenDocument extraction preserves linked text and explicit whitespace.
- Native mixed-script names remain unflagged; homoglyph checks respect the scan window.
- Malformed notebooks return a clean error.
- Saved-file hooks resolve relative paths against the supplied working directory and record failed checks.
- Exporting while switched off writes no files; portable contracts explain how to locate the detector.
- Coverage messages identify the scan limit as 262,144 characters.
- Windows test runners use the same Bash environment they probe.

## [0.9.2] - 2026-08-18

### Fixed

- Codex `apply_patch` payloads reach the saved-file guard.
- Inline strings in `.xlsx` and `.xlsm` files are extracted.
- EPUB extraction keeps word boundaries and reading order, and excludes
  navigation, style and script content.
- EPUB chapters using an undeclared namespace prefix are read.
- Archive members are size-checked before they are read.
- Confidence counts distinct scored pattern families rather than detector keys.
- The diversity term counts each catalogue family once.
- Zero-confidence results do not trigger the guard.
- A single decisive pattern raises the score floor only at confidence above
  `low`. Two distinct decisive families still raise it.
- `47_chatbot_artifacts` and `48_sycophantic` no longer overlap.
- `17_negative_parallelism` is report-only in one place rather than two.
- The 256 KB scan window applies to the character rules as well.
- Oversized files are reported as skipped or partially scored.
- Ordinary prose containing “a great question in …” does not trigger the
  chatbot-response rule.
- The vocabulary rule covers every word the writing contract bans.
- Guard child processes carry a timeout, an output cap and a fan-out limit.
- The Windows documentation check selects a Bash installation that can run Node.

### Changed

- Published a reproducible five-arm matched benchmark with pinned source revision,
  file hash, confidence intervals, threshold rates, aggregate results, and an
  offline standard-library harness. ROC-AUC is described as ranking, not accuracy.
- Narrowed the vocabulary rule to a compact project-maintained core set and
  regenerated the affected benchmark and recorded-demo evidence.

## [0.9.1] - 2026-08-17

### Fixed

- Improved Python discovery on Windows and quoted-path handling in
  `/sloptrim check`.
- Made `/sloptrim init` contracts portable across machines.
- Corrected instruction-file, `node_modules`, multi-path, status-line, session
  ledger, and pre-release record handling.
- Restored consistent trailing-whitespace cleanup across supported text formats.

### Added

- Added a first-run welcome and expanded Python and hook regression coverage.

## [0.9.0] - 2026-08-11

First public release. Pre-1.0 interfaces and score calibration may still change.

### Added

- An always-on writing contract for prose, injected at session start and into
  subagents without affecting code, configuration, or commits.
- A local saved-file guard covering 20 formats and scoring the first 256 KB
  of extracted text.
- A catalogue of 71 documented patterns with worked Before and After examples.
  Sixty-two patterns have automated checks; the remaining nine need a reading.
- A deterministic standard-library detector with no model, telemetry, or network
  access.
- Five bands: `clean` (0-20), `light tells` (21-40), `mixed`
  (41-60), `heavy tells` (61-80), and `pervasive tells` (81-100).
- Generic character cleanup, resampled score intervals, agent commands, Cursor
  integration, offline tests, and the recorded-session demo.

### Limits

- The score describes prose patterns and does not establish authorship, truth, or
  overall writing quality.
- English prose is the supported scope. PDF and RTF are logged but not read, and
  files written through shell commands do not pass saved-file hooks.

[0.9.6]: https://github.com/seyedehsanhadi/sloptrim/releases/tag/v0.9.6
[0.9.5]: https://github.com/seyedehsanhadi/sloptrim/releases/tag/v0.9.5
[0.9.4]: https://github.com/seyedehsanhadi/sloptrim/releases/tag/v0.9.4
[0.9.3]: https://github.com/seyedehsanhadi/sloptrim/releases/tag/v0.9.3
[0.9.2]: https://github.com/seyedehsanhadi/sloptrim/releases/tag/v0.9.2
[0.9.1]: https://github.com/seyedehsanhadi/sloptrim/releases/tag/v0.9.1
[0.9.0]: https://github.com/seyedehsanhadi/sloptrim/releases/tag/v0.9.0
