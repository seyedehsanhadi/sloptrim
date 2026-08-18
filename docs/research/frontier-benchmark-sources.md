# Frontier-model benchmark sources

Research date: 2026-08-18

## Verdict on the reported `0.551`

Claude Opus 5 is a real model. Anthropic's official release notes say it launched
on 2026-07-24 with API identifier `claude-opus-5`, so an experiment reported in
Sloptrim's 2026-08-13 public release is chronologically possible:
[Anthropic release notes](https://platform.claude.com/docs/en/release-notes/overview#july-24-2026),
[model documentation](https://platform.claude.com/docs/en/about-claude/models/whats-new-opus-5).

The specific Sloptrim result, however, has **no reproducible public basis** in
the published repository or in a primary public source found during this
review.

A separate private benchmark archive was also inspected after the initial
public-source review. It contains the broader benchmark code and corpora, but
its own claim ledger records only the aggregate for this arm—48 Claude
Opus 5 documents against 860 human documents—and explicitly says the generated
frontier arm was never committed. The archive therefore confirms that a
private benchmark project exists while also confirming that this particular
result cannot be re-derived from it.

- The 0.9.0 `README.md`, `ETHICS.md` and `CITATION.cff` reported ROC-AUC 0.551
  while stating that the corpora and harness were private and unavailable.
- The 0.9.0 `CHANGELOG.md` and `NOTICE` repeated that the figures, corpora and
  harness could not be re-derived from the public tree.
- `tests/validation_corpus.py` contains only a small fixed calibration fixture.
  Its module documentation explicitly disclaims general authorship evidence,
  and it does not calculate ROC-AUC.
- Full Git history of the published repository contains one introduction of `0.551`: root commit
  `9e46f9ed829874ca09f0b9f4144e5a51458f46c5` (`sloptrim 0.9.0`,
  2026-08-13). No deleted benchmark artifact exists in that history.

The public tree supplies none of the items needed to check the number: human
texts, Opus outputs, labels, prompts, request settings, sample size, score
vector, AUC code, seed, or uncertainty interval. Exact public searches for
`"Claude Opus 5" "0.551"`, `"frontier model" "ROC-AUC 0.551"`, and
`"0.551" "sloptrim" benchmark` found no independent paper, repository, or data
record supporting it. That absence search is not proof that no private run
occurred; it means the number should be described as **author-reported,
private, and independently unverified**, not as an established project metric.

The official [LMArena leaderboard dataset](https://huggingface.co/datasets/lmarena-ai/leaderboard-dataset)
contains ratings for Claude Opus 5, but its schema contains aggregate ratings,
confidence bounds, ranks, and vote counts—not response text or a matched human
arm. It cannot reproduce Sloptrim's claim.

## What ROC-AUC 0.551 does and does not mean

ROC-AUC measures ranking across thresholds. Google's metric reference defines
it as the probability that a randomly chosen positive example is ranked above
a randomly chosen negative example:
[ROC and AUC](https://developers.google.com/machine-learning/crash-course/classification/roc-and-auc).

Therefore, `0.551` does **not** mean that a document is classified correctly
55.1% of the time, that any individual document has a 55.1% probability of
being AI-written, or that the tool literally makes a 50/50 decision. On the
undisclosed sample, it would mean approximately 55.1% pairwise ranking
separation. Without class counts, paired-sample structure, and a confidence
interval, it is impossible to determine whether 0.551 is statistically
distinguishable from 0.5. Even statistical significance would not by itself
make the discrimination practically useful.

## Public data sources

No public dataset found here contains both matched human prose and Claude Opus
5 outputs. The following sources can test older or adjacent model families, or
can form the public human arm of a new Opus 5 benchmark.

| Source | Raw text access | Models and date coverage | Human comparison | License / use constraint | Fit for the claim |
|---|---|---|---|---|---|
| [Human Detectors](https://github.com/jenna-russell/human_detectors) | Direct Git clone; one 300-row JSON release | GPT-4o, Claude 3.5 Sonnet, o1-pro, paraphrased GPT-4o and humanized o1-pro | Yes; five 30/30 experiments matched by prompt ID, article brief and target publication | Repository release is MIT; underlying human articles come from third-party publications, so do not assume the repository license grants redistribution rights to those texts | **Selected public matched benchmark; not Opus 5** |
| [HART](https://github.com/baoguangsheng/truth-mirror) | Direct Git clone; 16 JSON files under `benchmark/hart/` | Exact IDs in the released data include GPT-3.5 Turbo 0125, GPT-4o 2024-11-20, Claude 3.5 Sonnet 2024-10-22, Gemini 1.5 Pro 002, Llama 3.3 70B Instruct, and Qwen 2.5 72B Instruct | Yes; matched domains and equal human, AI-polished, AI-generated, and humanized arms | Repository has an MIT license, but the human source corpora retain their own rights; verify before redistributing a derivative corpus | **Best immediately downloadable robustness benchmark; not Opus 5** |
| [EvoBench](https://github.com/happy-Moer/EvoBench) | Direct Git clone; each `*.raw_data.json` contains `original` and `sampled` arrays | 30 versions across Claude, GPT-4/4o, Gemini, Llama, and Qwen; latest Claude files are Claude 3.5 Sonnet/Haiku 2024-10-22 | Yes; 150 originals and 150 generated texts per inspected model/domain file | README says MIT, but audited commit has no `LICENSE` file and underlying dataset terms are not resolved | Excellent version-drift A/B corpus; **not Opus 5**, license needs clarification |
| [PAN 2025 Voight-Kampff](https://pan.webis.de/clef25/pan25-web/generated-content-analysis.html) | Gated Zenodo download after TIRA registration | Fourteen generators through early 2025, including GPT-4.5 preview, o1/o1-mini/o3-mini, Gemini 2.0 Flash, DeepSeek R1, Llama 3.3, and others; no Claude in the main generation arm | Yes; fiction, essays, and news, with obfuscated variants | Copyrighted; research use only; no redistribution; test labels/data remain controlled | Strong shared-task benchmark, but not a freely redistributable Opus benchmark |
| [APT-Eval](https://huggingface.co/datasets/smksaha/apt-eval) | Hugging Face or repository CSV/JSON | GPT-4o, DeepSeek-V3, Llama 3.1 70B, Llama 3 8B, and Llama 2 7B; released 2025 | 300 original human texts and 15,004 polished variants | Hugging Face data card: MIT | Best test of lightly AI-polished human prose; not pure Opus generation |
| [AuthorAwareDetectionBench](https://huggingface.co/datasets/PKU-ONELab/AuthorAwareDetectionBench) | AI arm is direct JSONL/Hugging Face; human arm requires ICNALE separately | Qwen 2.5 0.5B through 72B, Llama 3.1/3.2, and Mistral Small 2409; ACL 2025 | Parallel learner-profile essays, but original ICNALE text is not redistributed | AI text/metadata CC BY-NC 4.0; human text under [ICNALE terms](https://language.sakura.ne.jp/icnale/) | Useful fairness and non-native-English stress test; models are not current proprietary frontier |
| [BLUFF](https://github.com/jsl5710/BLUFF) | Hugging Face download script or `snapshot_download` (~3.9 GB) | 19 models including GPT-4.1, OpenAI o1, Gemini 1.5/2.0, Llama 3.3/4, Mistral Large, Phi-4, DeepSeek-R1, and QwQ; released as a 2026 under-review dataset | 122,836 human and 79,000+ generated samples across 79 languages | Data CC BY-NC-SA 4.0; code MIT; held-out test is controlled | Newest broad source, but heavily shifted toward fake-news/manipulation and contains no Claude |
| [OpenStax](https://openstax.org/subjects) | Free online view and per-title PDF download | Human textbooks only | Human-only source suitable for a new matched generation arm | License is stated in each title's front matter and varies by title/edition; record it per book | Best direct replacement for the private “American textbooks” human corpus, not a ready-made detector benchmark |

### 1. Human Detectors: selected matched benchmark

Primary sources:
[paper](https://arxiv.org/html/2501.15654v2),
[repository](https://github.com/jenna-russell/human_detectors).

The paper and repository release five experiments. Each experiment has 30
human and 30 machine articles sharing `prompt_id`, title, subtitle, section,
target length and target publication. The JSON fields used here are
`generation_model`, `prompt_id`, `article` and `ground_truth`; the five exact
arm values are `gpt-4o`, `claude`, `o1-pro`, `paraphrased_gpt-4o` and
`humanized_o1-pro`. The same 30 human articles recur across arms, so arm-level
confidence intervals resample matched prompt clusters and no pooled interval is
reported.

Pinned during this audit at commit
`afcf03d14d2da4a038d8d0fafa5ec779dd858181`; `human_detectors.json` SHA-256 is
`7ee1dc56d71b7cc5a185286f71818060a93ca20c4e93a90520ca78a0109619b5`.
The repository release carries an MIT license. Its human articles originate in
third-party publications, however, so that repository license should not be
read as permission to redistribute the underlying texts. Sloptrim distributes
only a harness, hash and aggregate results, not the corpus.

Access:

```text
git clone https://github.com/jenna-russell/human_detectors.git
python scripts/benchmark_frontier.py DATASET_JSON
```

### 2. HART: recommended broader robustness run

Primary sources:
[paper](https://arxiv.org/abs/2503.00258),
[raw benchmark directory](https://github.com/baoguangsheng/truth-mirror/tree/main/benchmark/hart).

The paper constructs four equal authorship types from student essays, arXiv
introductions, WritingPrompts stories, and Common Crawl news. News is also
provided in Chinese, French, Spanish, and Arabic. Each domain/language has
2,000 development and 2,000 test rows; the checked repository therefore holds
32,000 rows in 16 JSON files. Rows retain model provenance in
`content_source`, `language_source`, and `process_records`, including prompts
and sampling parameters. The paper reports the six model families; the raw
files preserve the more useful exact model IDs.

Access:

```text
git clone https://github.com/baoguangsheng/truth-mirror.git
cd truth-mirror/benchmark/hart
```

Pinned during this audit at commit
`3adce1bb596be8eada8b81c38e940cea8b21f8ae`. The repository license is MIT,
but human inputs originate in ASAP 2.0, arXiv, WritingPrompts, and Common
Crawl. The repository license should not be assumed to override those source
terms.

### 3. EvoBench: recommended model-version drift run

Primary source: [official repository](https://github.com/happy-Moer/EvoBench).

EvoBench spans XSum news summarization, WritingPrompts creative writing,
PubMed question answering, PeerRead academic writing, and paraphrased social
media. Each raw file inspected has two equal arrays, `original` and `sampled`,
with 150 texts in each. Relevant exact Claude files cover:

- `claude-3-opus-20240229`
- `claude-3-sonnet-20240229`
- `claude-3-haiku-20240307`
- `claude-3-5-sonnet-20240620`
- `claude-3-5-sonnet-20241022`
- `claude-3-5-haiku-20241022`

Access:

```text
git clone https://github.com/happy-Moer/EvoBench.git
cd EvoBench
```

Pinned during this audit at commit
`4c866cd211499744d21d34cbf2f32594064047c0`. Caveats: the repository's
README declares MIT, but that commit does not actually contain the linked
`LICENSE` file; generation-argument files are incomplete; and the human source
licenses are not documented well enough to bless redistribution. It is still
usable for an internal A/B measurement, but a published derivative should
resolve those points first.

### 4. PAN 2025: strongest controlled shared task

Primary sources:
[task page](https://pan.webis.de/clef25/pan25-web/generated-content-analysis.html),
[overview paper](https://ceur-ws.org/Vol-4038/paper_277.pdf),
[Zenodo record](https://zenodo.org/records/14962653).

The task used 9,185 Project Gutenberg fiction chunks plus human essays and
PAN 2024 news. Its fourteen main generators were GPT-3.5 Turbo, GPT-4o,
GPT-4o-mini, GPT-4.5-preview, OpenAI o1, o1-mini, o3-mini, Gemini 1.5 Pro,
Gemini 2.0 Flash, DeepSeek-R1-Qwen-32B, Falcon3-10B, Llama 3.1-8B,
Llama 3.3-70B, and Ministral-8B-2410. The published split counts are:

| Split | Human | LLM |
|---|---:|---:|
| Train | 9,101 | 14,606 |
| Validation | 1,277 | 2,312 |
| Test | 1,497 | 2,216 |

Access requires registering at [TIRA](https://www.tira.io/) and requesting
Zenodo access with the same email. Training/validation rows are JSONL with
`id`, `text`, `model`, `label`, and `genre`. The organizers prohibit
redistribution and reserve the controlled test data. Small adversarial
ELOQUENT submissions used Claude 3.5 Sonnet, but Claude is not one of the
fourteen main generation arms and there is no Opus 5 arm.

### 5. APT-Eval: AI-polishing stress test

Primary sources:
[official repository](https://github.com/ShoumikSaha/ai-polished-text),
[ACL 2025 paper](https://aclanthology.org/2025.findings-acl.1303/),
[Hugging Face data card](https://huggingface.co/datasets/smksaha/apt-eval).

The six human domains are blogs, email, game reviews, news, paper abstracts,
and speeches. Load both the polished and original human arms with:

```python
from datasets import load_dataset

dataset = load_dataset(
    "smksaha/apt-eval",
    data_files={
        "test": "merged_apt_eval_dataset.csv",
        "original": "original.csv",
    },
)
```

This is the best public source here for testing whether Sloptrim penalizes
small edits to genuinely human prose. It does not test fully generated Opus 5
text.

### 6. AuthorAwareDetectionBench: fairness stress test

Primary sources:
[official repository](https://github.com/PKU-ONELab/AuthorAwareDetection),
[ACL 2025 paper](https://aclanthology.org/2025.acl-long.1292/),
[data card](https://huggingface.co/datasets/PKU-ONELab/AuthorAwareDetectionBench).

The public AI arm has 61,700 rows and fields for model, prompt, CEFR level,
sex, academic genre, language environment, and the matching human code:

```python
from datasets import load_dataset

ai = load_dataset(
    "PKU-ONELab/AuthorAwareDetectionBench",
    split="train",
)
```

For a true human-vs-machine comparison, separately obtain ICNALE Written
Essays v2.6 and run the merge command documented in the upstream repository,
using its human metadata and generated-text files.

This source is important for false-positive and demographic analysis, not for
substantiating a current-frontier claim.

### 7. BLUFF: newest multilingual source, high domain shift

Primary sources:
[official repository](https://github.com/jsl5710/BLUFF),
[Hugging Face dataset](https://huggingface.co/datasets/jsl5710/BLUFF).

Access either with the upstream download script after cloning, or:

```python
from huggingface_hub import snapshot_download

snapshot_download(
    repo_id="jsl5710/BLUFF",
    repo_type="dataset",
    local_dir="./data",
)
```

Use BLUFF only as a separately reported fake-news/manipulation arm. Pooling it
with essays or textbooks would make an AUC difficult to interpret because
authorship would be confounded with topic, translation, and manipulation.

## A defensible Opus 5 reproduction

Public existing data can benchmark Sloptrim today, but it cannot verify the
exact Opus 5 claim. No replacement is publicly reproducible yet; producing one
requires a newly generated arm:

1. Freeze a legally usable human corpus. For textbooks, record the exact
   OpenStax title, edition, chapter/section, URL, license, extraction rule, and
   SHA-256 of every passage. Add at least two unlike domains so a textbook
   register is not mistaken for a universal result.
2. Generate a matched text for each human item with exact model ID
   `claude-opus-5`. Match topic, task, genre, and target length. Save the full
   system/user prompts, request date, all accepted API parameters, response
   metadata, refusals, and raw output.
3. Freeze the Sloptrim commit and save one score per document before computing
   metrics. Keep the score vector, labels, source IDs, and evaluation script.
4. Report ROC-AUC **per domain and per model arm**, with sample counts and a
   group/paired bootstrap 95% confidence interval. Also report false-positive
   and true-positive rates at the actual product thresholds. Do not replace
   these with one pooled headline.
5. Publish the manifest, prompts, hashes, scores, seed, code, and raw texts
   where source and provider terms allow. If raw redistribution is forbidden,
   say exactly what remains inaccessible; do not call the run independently
   reproducible.

Until that exists, the most accurate public wording is:

> An author-reported private benchmark against Claude Opus 5 produced ROC-AUC
> 0.551. The sample, scores, harness, sample size, and confidence interval are
> not public, so the result is not independently reproducible.

The categorical statement that Sloptrim “cannot” distinguish current frontier
output is stronger than the available evidence. The product can still state
the sounder and independently supported limitation: its score is a writing-
pattern signal, not proof of human or machine authorship.
