# Security

## Reporting

Report privately through [GitHub's advisory form](https://github.com/seyedehsanhadi/sloptrim/security/advisories/new). Please do not open a public issue for a vulnerability.

Expect an acknowledgement within a week.

## What is in scope

The tool runs on your machine, reads files you point it at, and reaches no network. That shapes what a vulnerability looks like here.

- **A crafted document that hangs the detector.** The guard gives the detector 8 seconds on text it pipes in, and 15 seconds when it hands over a path for a zip-based or notebook format. `tests/test_detect.py` throws eight pathological inputs at the scanner, and the slowest of them lands near 7 seconds on an ordinary laptop, so the margin under that 8-second ceiling is thin and an input outside those eight could cross it. A regular expression that backtracks catastrophically is the likely shape.
- **A crafted document that escapes the reader.** The zip formats are opened with `zipfile` and parsed with `xml.etree`. A path traversal out of the extraction, or an XML entity expansion, would count.
- **The hooks doing something outside their remit.** They read a mode flag, run the detector, and write a session ledger. Anything that writes elsewhere, executes input, or sends data anywhere is a bug and a serious one.
- **`--clean` corrupting content.** It removes invisible characters and folds homoglyphs. Damaging legitimate text, or failing to remove what it claims to remove, is in scope.

## What is not

- **A document that scores wrongly.** A false positive or a false negative is an accuracy defect, not a vulnerability. Open an issue; those are welcome.
- **Anything requiring an attacker who already runs code as you.** They can edit the detector.

## What the tool holds

A one-word mode flag, and a per-session ledger written with owner-only permissions: for each prose file, its base name, the score, the band, and up to five pattern labels. Never the text of your documents, and never a path outside the base name. Ledgers older than a week are deleted at the next session start.

Nothing leaves the machine. `tests/test_no_network.py` enforces that by scanning every Python, JavaScript, PowerShell and shell file in the repository for a way to open a socket, and it fails the build rather than asserting it in prose. The benchmark that carried the one network dependency this project ever had is not published here.
