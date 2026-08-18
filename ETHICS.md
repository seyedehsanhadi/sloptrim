# Ethics

## What it is

Sloptrim is a local prose-pattern linter. It reports patterns documented in
`references/patterns.md`, scores their density, and helps revise flagged spans.
Its five bands—`clean`, `light tells`, `mixed`, `heavy tells`, and
`pervasive tells`—describe the prose. The hooks render the same ranges as
`reads clean`, `reads mostly clean`, `reads with some AI tells`, `reads with
heavy AI tells`, and `reads with pervasive AI tells`.

## What it cannot establish

Sloptrim is not an authorship classifier. A high score does not prove that a
model wrote a document, and a low score does not prove that a person did. Formal,
edited, translated, and non-native-English prose can contain catalogue patterns;
any writer can also edit them out.

The public matched benchmark shows useful score ranking on its five named arms,
but its threshold sensitivity varies substantially by arm. ROC-AUC is a ranking
measure, not per-document accuracy. Do not use a score to accuse, discipline, or
make decisions about a student, colleague, applicant, or author.

## Responsible use

Use Sloptrim to improve prose, not to conceal its origin. If an institution,
publisher, employer, or client requires disclosure of AI assistance, using this
tool does not remove that obligation.

The project does not consult or optimize against third-party authorship,
plagiarism, or integrity detectors. Contributions aimed at passing those systems
are out of scope. The implemented rules and weights remain inspectable in this
repository.

## Privacy

Document analysis is local. The runtime contains no network client or telemetry.
It stores a one-word mode flag and a per-session ledger containing each prose
file's base name, score, band, and up to five pattern labels—never the document
text or its full path. Ledgers older than one week are removed at the next
session start.

`detect.py --clean` removes invisible and zero-width characters, normalizes
non-standard spaces, folds mixed-script lookalikes, and trims stray whitespace.
This is generic character cleanup, not a provider-specific watermark feature.
Do not use it to conceal required provenance information.

## Reporting misuse

If this project is advertised as a detector-bypass service, open an issue. That
is not its purpose and no such claim is supported here.
