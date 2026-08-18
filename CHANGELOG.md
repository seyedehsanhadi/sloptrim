# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.9.2] - 2026-08-18

### Fixed

- Codex `apply_patch` payloads now reach the saved-file guard.
- Inline strings in `.xlsx` and `.xlsm` files are extracted.
- Formatted EPUB text keeps word boundaries and excludes navigation, style, and
  script content.
- Confidence counts distinct scored pattern families rather than aliases.
- Zero-confidence results cannot trigger the guard.
- Oversized accepted files are reported as skipped or partially scored instead
  of disappearing or appearing fully covered.
- Ordinary prose ending in “a great question in …” no longer triggers the
  standalone chatbot-response rule.
- The Windows documentation check selects a Bash installation that can run Node.

### Changed

- Published a reproducible five-arm matched benchmark with pinned source revision,
  file hash, confidence intervals, threshold rates, aggregate results, and an
  offline standard-library harness. ROC-AUC is described as ranking, not accuracy.

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

[0.9.2]: https://github.com/seyedehsanhadi/sloptrim/releases/tag/v0.9.2
[0.9.1]: https://github.com/seyedehsanhadi/sloptrim/releases/tag/v0.9.1
[0.9.0]: https://github.com/seyedehsanhadi/sloptrim/releases/tag/v0.9.0
