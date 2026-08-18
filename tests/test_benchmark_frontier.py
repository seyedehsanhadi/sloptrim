import importlib.util
import hashlib
import json
from pathlib import Path


PATH = Path(__file__).parents[1] / "scripts" / "benchmark_frontier.py"
SPEC = importlib.util.spec_from_file_location("benchmark_frontier", PATH)
BENCHMARK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BENCHMARK)


def test_auc_counts_order_and_ties():
    assert BENCHMARK.auc([3, 2], [1, 0]) == 1.0
    assert BENCHMARK.auc([1], [1]) == 0.5
    assert BENCHMARK.auc([0], [1]) == 0.0


def test_product_thresholds_are_strict_and_require_confidence():
    assert not BENCHMARK.is_flagged(20, "high", 20)
    assert BENCHMARK.is_flagged(21, "high", 20)
    assert not BENCHMARK.is_flagged(40, "high", 40)
    assert BENCHMARK.is_flagged(41, "high", 40)
    assert not BENCHMARK.is_flagged(100, "none", 40)


def test_paired_bootstrap_is_seeded_and_bounded():
    rows = [
        {"prompt_id": 1, "label": 0, "score": 0},
        {"prompt_id": 1, "label": 1, "score": 2},
        {"prompt_id": 2, "label": 0, "score": 1},
        {"prompt_id": 2, "label": 1, "score": 3},
    ]
    first = BENCHMARK.clustered_bootstrap_auc(rows, 20, 7)
    second = BENCHMARK.clustered_bootstrap_auc(rows, 20, 7)
    assert first == second == [1.0, 1.0]


def test_paired_bootstrap_rejects_bad_inputs():
    rows = [{"prompt_id": 1, "label": 0, "score": 0}]
    try:
        BENCHMARK.clustered_bootstrap_auc(rows, 20, 7)
    except ValueError as error:
        assert "both labels" in str(error)
    else:
        raise AssertionError("one-label cluster was accepted")

    try:
        BENCHMARK.clustered_bootstrap_auc([], 0, 7)
    except ValueError as error:
        assert "positive" in str(error)
    else:
        raise AssertionError("zero resamples were accepted")


def test_run_rejects_wrong_hash_and_unbalanced_arms(tmp_path, monkeypatch):
    dataset = tmp_path / "benchmark.json"
    dataset.write_text("{}", encoding="utf-8")
    try:
        BENCHMARK.run(dataset, 1)
    except ValueError as error:
        assert "SHA-256" in str(error)
    else:
        raise AssertionError("wrong dataset hash was accepted")

    source = {}
    for arm in BENCHMARK.ARMS:
        for label in ("Human-written", "AI-generated"):
            key = "%s-%s" % (arm, label)
            source[key] = {
                "generation_model": arm,
                "prompt_id": 1,
                "ground_truth": label,
                "article": "One ordinary sentence for the benchmark fixture.",
            }
    raw = json.dumps(source).encode("utf-8")
    dataset.write_bytes(raw)
    monkeypatch.setattr(BENCHMARK, "DATASET_SHA256",
                        hashlib.sha256(raw).hexdigest())
    try:
        BENCHMARK.run(dataset, 1)
    except ValueError as error:
        assert "counts" in str(error)
    else:
        raise AssertionError("unbalanced arms were accepted")
