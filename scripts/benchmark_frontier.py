"""Reproduce the public Human Detectors benchmark reported in README.md.

The third-party dataset is not bundled. Download human_detectors.json from the
pinned upstream revision, then pass its path here. Output is JSON on stdout.
"""

import argparse
import hashlib
import importlib.util
import json
import math
import random
import statistics
from pathlib import Path


DATASET_COMMIT = "afcf03d14d2da4a038d8d0fafa5ec779dd858181"
DATASET_SHA256 = "7ee1dc56d71b7cc5a185286f71818060a93ca20c4e93a90520ca78a0109619b5"
ARMS = {
    "claude",
    "gpt-4o",
    "humanized_o1-pro",
    "o1-pro",
    "paraphrased_gpt-4o",
}
SEED = 20260818


def load_detector():
    path = Path(__file__).with_name("detect.py")
    spec = importlib.util.spec_from_file_location("sloptrim_benchmark_detect", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def auc(positive, negative):
    if not positive or not negative:
        raise ValueError("AUC requires both positive and negative scores")
    wins = 0.0
    for pos in positive:
        for neg in negative:
            wins += 1.0 if pos > neg else 0.5 if pos == neg else 0.0
    return wins / (len(positive) * len(negative))


def percentile(ordered, quantile):
    index = (len(ordered) - 1) * quantile
    low, high = math.floor(index), math.ceil(index)
    if low == high:
        return ordered[low]
    return ordered[low] * (high - index) + ordered[high] * (index - low)


def clustered_bootstrap_auc(rows, resamples, seed):
    if resamples < 1:
        raise ValueError("resamples must be positive")
    clusters = {}
    for row in rows:
        clusters.setdefault(row["prompt_id"], []).append(row)
    if any({row["label"] for row in cluster} != {0, 1}
           for cluster in clusters.values()):
        raise ValueError("each prompt cluster must contain both labels")
    rng = random.Random(seed)
    values = []
    for _ in range(resamples):
        sampled = [rng.choice(list(clusters.values())) for _ in clusters]
        pos = [row["score"] for cluster in sampled for row in cluster
               if row["label"] == 1]
        neg = [row["score"] for cluster in sampled for row in cluster
               if row["label"] == 0]
        values.append(auc(pos, neg))
    values.sort()
    return [round(percentile(values, 0.025), 4),
            round(percentile(values, 0.975), 4)]


def is_flagged(score, confidence, threshold):
    return score > threshold and confidence != "none"


def summarize(rows, resamples, seed):
    positive = [row["score"] for row in rows if row["label"] == 1]
    negative = [row["score"] for row in rows if row["label"] == 0]
    default_tp = sum(row["default"] for row in rows if row["label"] == 1)
    default_fp = sum(row["default"] for row in rows if row["label"] == 0)
    strict_tp = sum(row["strict"] for row in rows if row["label"] == 1)
    strict_fp = sum(row["strict"] for row in rows if row["label"] == 0)
    return {
        "human_n": len(negative),
        "machine_n": len(positive),
        "roc_auc": round(auc(positive, negative), 4),
        "roc_auc_bootstrap_95ci": clustered_bootstrap_auc(
            rows, resamples, seed),
        "human_score_median": statistics.median(negative),
        "machine_score_median": statistics.median(positive),
        "default_tpr": round(default_tp / len(positive), 4),
        "default_fpr": round(default_fp / len(negative), 4),
        "strict_tpr": round(strict_tp / len(positive), 4),
        "strict_fpr": round(strict_fp / len(negative), 4),
    }


def run(dataset_path, resamples=10_000):
    if resamples < 1:
        raise ValueError("resamples must be positive")
    raw = Path(dataset_path).read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != DATASET_SHA256:
        raise ValueError("dataset SHA-256 is %s, expected %s" %
                         (digest, DATASET_SHA256))
    source = json.loads(raw)
    entries = list(source.values())
    arms = {entry["generation_model"] for entry in entries}
    if arms != ARMS:
        raise ValueError("dataset arms are %r, expected %r" %
                         (sorted(arms), sorted(ARMS)))

    detector = load_detector()
    rows = []
    for entry in entries:
        result = detector.scan(entry["article"])
        metrics = result["_metrics"]
        score, confidence = metrics["ai_tell_score"], metrics["confidence"]
        rows.append({
            "arm": entry["generation_model"],
            "prompt_id": entry["prompt_id"],
            "label": 1 if entry["ground_truth"] == "AI-generated" else 0,
            "score": score,
            "default": is_flagged(score, confidence, 40),
            "strict": is_flagged(score, confidence, 20),
        })

    for arm in ARMS:
        arm_rows = [row for row in rows if row["arm"] == arm]
        counts = [sum(row["label"] == label for row in arm_rows)
                  for label in (0, 1)]
        if counts != [30, 30]:
            raise ValueError("arm %s has human/machine counts %r" % (arm, counts))

    by_arm = {
        arm: summarize([row for row in rows if row["arm"] == arm],
                       resamples, SEED + index)
        for index, arm in enumerate(sorted(ARMS))
    }
    return {
        "method": {
            "dataset_commit": DATASET_COMMIT,
            "dataset_sha256": digest,
            "score": "Sloptrim ai_tell_score",
            "auc_ties": "0.5 credit",
            "ci": "paired prompt-cluster percentile bootstrap, %d resamples" % resamples,
            "seed": SEED,
            "default_flag": "score > 40 and confidence != none",
            "strict_flag": "score > 20 and confidence != none",
        },
        "by_arm": by_arm,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--resamples", type=int, default=10_000)
    args = parser.parse_args()
    if args.resamples < 1:
        parser.error("--resamples must be positive")
    print(json.dumps(run(args.dataset, args.resamples), indent=2))


if __name__ == "__main__":
    main()
