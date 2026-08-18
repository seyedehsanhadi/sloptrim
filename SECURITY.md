# Security

## Reporting

Report privately through [GitHub's advisory form](https://github.com/seyedehsanhadi/sloptrim/security/advisories/new). Please do not open a public issue for a vulnerability.

Expect an acknowledgement within a week.

## What is in scope

The tool runs on your machine, reads files you point it at, and reaches no network. That shapes what a vulnerability looks like here.

- **A crafted document that exhausts time or memory.** The guard limits detector
  execution to 8 seconds for piped text and 15 seconds for archive or notebook paths.
- **A crafted document that escapes the reader.** Path traversal, unsafe archive
  handling, or unsafe XML processing is in scope.
- **The hooks doing something outside their remit.** They read a mode flag, run the detector, and write a session ledger. Anything that writes elsewhere, executes input, or sends data anywhere is a bug and a serious one. `/sloptrim init` is the one command that writes into your project, by request: `./AGENTS.md` and `./.cursor/rules/sloptrim.mdc`.
- **`--clean` corrupting content.** It removes invisible characters and folds homoglyphs. Damaging legitimate text, or failing to remove what it claims to remove, is in scope.

## What is not

- **A document that scores wrongly.** A false positive or a false negative is an accuracy defect, not a vulnerability. Open an issue; those are welcome.
- **Anything requiring an attacker who already runs code as you.** They can edit the detector.

## What the tool holds

A one-word mode flag, and a per-session ledger written with owner-only permissions: for each prose file, its base name, the score, the band, and up to five pattern labels. Never the text of your documents, and never a path outside the base name. Ledgers older than a week are deleted at the next session start.

Nothing leaves the machine. `tests/test_no_network.py` enforces that by scanning every Python, JavaScript, PowerShell and shell file in the repository for a way to open a socket. The public benchmark harness reads a user-supplied local dataset and opens no socket.
