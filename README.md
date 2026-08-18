<div align="center">

<h1>
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/sloptrim-logo-dark.svg">
    <img src="assets/sloptrim-logo.svg" width="358" alt="sloptrim">
  </picture>
</h1>

**A local detector for AI-writing patterns. It scores the first 256 KB of extracted
prose in files saved through supported file-edit tools—accepting plain text up to
512 KB and supported archives up to 4 MB—and asks for the flagged spans to be fixed.**
Python standard library only, no network, no model. Prose only, never code.

[![test](https://github.com/seyedehsanhadi/sloptrim/actions/workflows/test.yml/badge.svg)](https://github.com/seyedehsanhadi/sloptrim/actions/workflows/test.yml)
[![Version](https://img.shields.io/badge/version-0.9.2-blue)](CHANGELOG.md)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue)](LICENSE.txt)
[![Dependencies](https://img.shields.io/badge/dependencies-none-blue)](scripts/detect.py)
[![Tests](https://img.shields.io/badge/tests-180-blue)](tests/)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](scripts/detect.py)

[Install](#install) &middot; [What it does](#what-it-does) &middot; [Measured](#measured) &middot; [Limits](#what-it-cannot-do) &middot; [Patterns](references/patterns.md) &middot; [Ethics](ETHICS.md)

</div>

> [!IMPORTANT]
> **This is a command-line tool and an agent plugin. There is no website and no hosted version.**
> Nothing you write is uploaded, there is no account, and no text ever leaves your machine.
> Any site offering a service under this name is unrelated to this project.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/demo-dark.svg">
  <img src="assets/demo-light.svg" width="800" alt="A recorded session. The contract arrives at session start, again on the prompt, and again inside a subagent. A saved file scores 45 and its patterns are named. After the fix the next read is clean at 15. The same text saved as a .docx scores the same, read out of the zip. Every hook latency is measured.">
</picture>

<div align="center"><sub>A recorded session, not a mock-up. <a href="record/session_capture.py">record/session_capture.py</a> fires the real hooks with the payloads Claude Code sends and writes <a href="record/session.json">record/session.json</a>; <a href="record/anim.py">record/anim.py</a> draws it. The hook lines, the scores and the milliseconds come from that capture; the grey labels beside them are narration. The prose being scored is <a href="record/draft.md">record/draft.md</a>, a short piece written for the recording.</sub></div>

---

## Install

Paste into Claude Code, Codex, Cursor, or any coding agent:

```text
Install the sloptrim plugin from https://github.com/seyedehsanhadi/sloptrim
```

Restart, then run `/sloptrim doctor`. It answers with four `[OK]` lines.

<details>
<summary>Explicit commands, and installing without the marketplace</summary>

```
/plugin marketplace add seyedehsanhadi/sloptrim
/plugin install sloptrim@sloptrim
```

```bash
git clone https://github.com/seyedehsanhadi/sloptrim.git ~/.claude/skills/sloptrim
mkdir -p ~/.claude/commands
cp ~/.claude/skills/sloptrim/install/sloptrim-command.md ~/.claude/commands/sloptrim.md
```

Do not skip the `mkdir`. On a fresh machine `~/.claude/commands` does not exist yet
and the copy fails with "No such file or directory". In PowerShell the last two lines
are `New-Item -ItemType Directory -Force $HOME/.claude/commands` and `Copy-Item`.
The copy puts `/sloptrim` in the `/` menu, because Claude Code does not scan a skill
folder's own `commands/`. A marketplace install needs no such step. Either way the
router also answers to `/sloptrim:sloptrim`.

</details>

## What it does

The score is 0-100 against 71 documented patterns. 62 of them have a detector; the
other 9 need a reading and are worked during the rewrite. Of the 62, 50 can move the
score and 12 are reported as writing advice and count for nothing: most of them because
measurement showed they mark formal register rather than machine authorship, the rest
because they are typographic habits.

| | |
|---|---|
| Formats | 20, including `.docx`, `.pptx`, `.xlsx`, OpenDocument, `.epub`, `.ipynb`, LaTeX; the first 256 KB of extracted prose is scored |
| Runs in | Claude Code, on save. Other agents via `/sloptrim init`, which writes the contract to `AGENTS.md`, and `.cursor/rules/` |
| Needs | Node for the hooks, Python 3.9 or newer for the detector, nothing else |
| Suite | 108 Python tests and 72 hook checks, green in CI on Linux, Windows and macOS, against Python 3.9 and 3.13 (macOS on 3.13) |
| Does not see | A file written by a `Bash` command, which reaches disk without passing `Write` or `Edit` |

| Command | Effect |
|---|---|
| `/sloptrim full` | Contract + guard *(default)* |
| `/sloptrim strict` | Flags at 20 instead of 40, and asks for a character scrub |
| `/sloptrim lite` / `off` | Contract only / nothing |
| `/sloptrim check <file>` | Score a file, name the tells, no rewrite |
| `/sloptrim init` | Write the contract to `./AGENTS.md` and a Cursor rule to `./.cursor/rules/` |
| `/sloptrim doctor` | Diagnose the install |

```bash
python scripts/detect.py draft.docx    # JSON: patterns, metrics, 0-100 score
```

A score lands in one of five bands: `clean`, `light tells`, `mixed`, `heavy tells`,
`pervasive tells`. The guard nudges above 40, or above 20 in strict mode.

## Measured

Sloptrim's public matched benchmark uses five separate 30-human/30-machine arms
from the [Human Detectors](https://github.com/jenna-russell/human_detectors)
release, pinned at commit `afcf03d`. Each arm is matched by prompt and scored
separately. AUC is a ranking measure, not accuracy at Sloptrim's guard threshold.

| machine arm | ROC-AUC | bootstrap 95% CI | default TPR / FPR |
|---|---:|---:|---:|
| GPT-4o | **0.946** | 0.876–0.992 | 46.7% / 0% |
| Claude 3.5 Sonnet | **0.842** | 0.729–0.936 | 3.3% / 0% |
| o1-pro | **0.877** | 0.771–0.957 | 23.3% / 6.7% |
| paraphrased GPT-4o | **0.837** | 0.733–0.927 | 6.7% / 3.3% |
| humanized o1-pro | **0.762** | 0.648–0.871 | 0% / 3.3% |

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/detection-dark.svg">
  <img src="assets/detection-light.svg" width="756" alt="Public matched benchmark ROC-AUC: GPT-4o 0.946, Claude 3.5 Sonnet 0.842, o1-pro 0.877, paraphrased GPT-4o 0.837, humanized o1-pro 0.762.">
</picture>

Across these arms, Sloptrim achieved ROC-AUC **0.762–0.946**. Confidence intervals
use 10,000 paired prompt-cluster bootstrap resamples. The public
[result record](docs/research/frontier-benchmark-results.json) pins the source hash;
the harness refuses any other file. The benchmark texts are not redistributed here.

```bash
git clone https://github.com/jenna-russell/human_detectors.git
git -C human_detectors checkout afcf03d14d2da4a038d8d0fafa5ec779dd858181
python scripts/benchmark_frontier.py PATH_TO_HUMAN_DETECTORS_JSON
```

## What it cannot do

**It cannot prove whether a model wrote something.** The public arms show that the
score often ranks these machine samples above matched human samples. The threshold
results show why that is not the same as a dependable yes/no classifier: sensitivity
changes sharply with model, prompt, formatting and threshold.

**It is not an authorship classifier and must not be used as one.** A score says
something about writing, never about a person. Read [ETHICS.md](ETHICS.md).

## License

Apache-2.0 ([full text](LICENSE.txt), [NOTICE](NOTICE)). Cite with
[CITATION.cff](CITATION.cff).
