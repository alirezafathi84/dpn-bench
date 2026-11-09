"""Unit tests for the metric implementations and the hand-written backward pass.

These run in CI without the dataset, so a broken metric or gradient is caught
before anyone trusts a benchmark number.
"""
import os, sys
import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from dpn_common import bedroc, enrichment_factor, metrics  # noqa: E402


def _labels(N=10_000, n=100):
    y = np.zeros(N, int)
    y[:n] = 1
    return y


def test_bedroc_perfect_ranking_is_one():
    y = _labels()
    s = np.zeros(len(y)); s[y == 1] = 1.0
    assert bedroc(y, s) == pytest.approx(1.0, abs=1e-6)


def test_bedroc_worst_ranking_is_zero():
    y = _labels()
    s = np.zeros(len(y)); s[y == 1] = -1.0
    assert bedroc(y, s) == pytest.approx(0.0, abs=1e-6)


def test_bedroc_random_is_small():
    y = _labels()
    rng = np.random.default_rng(0)
    vals = [bedroc(y, rng.random(len(y))) for _ in range(20)]
    assert 0.0 < np.mean(vals) < 0.10      # R_a-weighted, not 0.5


def test_bedroc_degenerate_returns_nan():
    assert np.isnan(bedroc(np.zeros(10, int), np.random.random(10)))
    assert np.isnan(bedroc(np.ones(10, int), np.random.random(10)))


def test_enrichment_factor_bounds():
    y = _labels()
    s = np.zeros(len(y)); s[y == 1] = 1.0
    assert enrichment_factor(y, s, 0.01) == pytest.approx(100.0)
    s = np.zeros(len(y)); s[y == 1] = -1.0
    assert enrichment_factor(y, s, 0.01) == pytest.approx(0.0)


def test_metrics_keys_and_ranges():
    y = _labels()
    rng = np.random.default_rng(1)
    s = rng.random(len(y)) + 0.5 * y
    m = metrics(y, s)
    for k in ("ROC_AUC", "PR_AUC", "dPR_AUC", "BEDROC", "EF_1pct", "MCC_at_prev"):
        assert k in m
    assert 0.0 <= m["ROC_AUC"] <= 1.0
    assert m["prevalence"] == pytest.approx(0.01)
    assert m["dPR_AUC"] == pytest.approx(m["PR_AUC"] - m["prevalence"])


def test_mtl_gradients_match_finite_differences():
    """The multi-task backward pass is hand-written; verify it numerically."""
    path = os.path.join(os.path.dirname(__file__), "..", "src", "04_mtl.py")
    src = open(path).read().split("def main(")[0]
    ns = {"__file__": path, "__name__": "mtl_under_test"}
    exec(compile(src, path, "exec"), ns)
    assert ns["gradient_check"]() < 1e-4
