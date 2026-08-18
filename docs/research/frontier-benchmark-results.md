# Frontier re-benchmark record

Research date: 2026-08-18  
Sloptrim revision tested: `cf3074322c8e220c5f3ae792bf0dd832b2040ea1`

## Verdict

The available evidence does not reproduce or support the original categorical
claim that Sloptrim is at chance on frontier-model prose. A private benchmark
archive records the old Claude Opus 5 ROC-AUC 0.551 aggregate and its sample
counts, but its own claim ledger says that frontier arm was never committed.
The texts, prompts, score vector, seed and confidence interval remain
unavailable, so the result cannot be re-derived. The
[source audit](frontier-benchmark-sources.md) gives the full provenance review.

The replacement measurements show useful score ranking on these samples, but
low and model-dependent sensitivity at the thresholds the product actually
uses. Sloptrim remains a prose-pattern linter, not an authorship classifier.

## Public matched benchmark

The source is Russell, Karpinska and Iyyer, *People who frequently use ChatGPT
for writing tasks are accurate and robust detectors of AI-generated text*
(ACL 2025): [paper](https://arxiv.org/html/2501.15654v2),
[dataset repository](https://github.com/jenna-russell/human_detectors).
The released dataset contains five experiments, each with 30 human and 30
machine articles matched by title, subtitle, target length and publication
style.

- Repository revision: `afcf03d14d2da4a038d8d0fafa5ec779dd858181`
- `human_detectors.json` SHA-256:
  `7ee1dc56d71b7cc5a185286f71818060a93ca20c4e93a90520ca78a0109619b5`
- Score: Sloptrim's document `ai_tell_score`; higher ranks as more catalogue
  patterns.
- AUC ties: half credit.
- Interval: paired prompt-cluster percentile bootstrap, 10,000 resamples,
  master seed `20260818`; each arm receives a deterministic derived seed.
- Normal flag: score greater than 40 with confidence other than `none`.
- Strict flag: score greater than 20 with confidence other than `none`.

| Machine arm | Human / machine | ROC-AUC | Bootstrap 95% CI | Normal TPR / FPR |
|---|---:|---:|---:|---:|
| GPT-4o | 30 / 30 | 0.946 | 0.876–0.992 | 46.7% / 0% |
| Claude 3.5 Sonnet | 30 / 30 | 0.842 | 0.729–0.936 | 3.3% / 0% |
| o1-pro | 30 / 30 | 0.877 | 0.771–0.957 | 23.3% / 6.7% |
| Paraphrased GPT-4o | 30 / 30 | 0.837 | 0.733–0.928 | 6.7% / 3.3% |
| Humanized o1-pro | 30 / 30 | 0.762 | 0.648–0.871 | 0% / 3.3% |

Run the committed offline harness after obtaining the upstream dataset:

```bash
python scripts/benchmark_frontier.py DATASET_JSON
```

The harness checks the dataset hash and exact five-arm balance before scoring.
It uses only the Python standard library and the committed detector.

## Current-model paired run

Thirty articles were generated in one structured batch through Codex CLI
0.147.0 with OpenAI `gpt-5.6-sol`, reasoning effort `none`, on 2026-08-18.
OpenAI documents GPT-5.6 Sol as its frontier agentic coding model:
[model page](https://developers.openai.com/api/docs/models/gpt-5.6-sol),
[release](https://openai.com/index/gpt-5-6/).

The prompt reused 30 title, subtitle, section and publication records from the
Claude arm of the public dataset and requested ordinary 280–320-word
nonfiction. Each generated article and its paired human article was truncated,
preserving paragraphs, to the same 296–300-word prefix to remove length as a
pairwise confound.

| Measure | Result |
|---|---:|
| Human / machine | 30 / 30 |
| ROC-AUC | 0.965 |
| Bootstrap 95% CI | 0.913–1.000 |
| Machine score above paired human | 28 / 30 |
| Median score, human / machine | 0 / 17.5 |
| Normal TPR / FPR | 0% / 0% |
| Strict TPR / FPR | 40% / 0% |

Generation prompt SHA-256:
`890db0b920ac06acf36704d83741b64f2090ce7f298c0a2d1f6701f8ea4d140b`.
Raw structured output SHA-256:
`55e24809b97cbd75a7d213ef34b8a45728dbe272a562894879959f1626c53419`.

Uniform paragraph length fired on 29 of 30 generated articles and none of the
human articles. Removing that rule and its paragraph-variation term reduced
ROC-AUC to 0.728 (95% CI 0.594–0.850). Some signal remains, but the headline
0.965 is strongly dependent on this prompt and formatting setup.

This arm is date-stamped and self-generated. It is not an independent public
dataset, not an Opus 5 reproduction, and not a claim about every frontier model.
The hashes identify the exact retained audit artifacts but do not substitute
for publishing them.

## Interpretation

ROC-AUC is the probability that a randomly chosen positive example receives a
higher score than a randomly chosen negative example. It does not state the
accuracy, recall or false-positive rate at Sloptrim's threshold, and it is not a
probability that any particular document was machine-written.

The old 0.551 result therefore did not mean “55.1% accurate” or a literal 50/50
decision. The new 0.965 result likewise does not mean “96.5% accurate”: in that
same run, normal-mode recall was zero. Both ranking and operating-threshold
metrics must be reported, with the model, sample, prompt and domain.
