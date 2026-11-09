"""Shared data access, splits and virtual-screening metrics for the DPN benchmark.

Metrics follow early-recognition conventions from virtual screening: ROC-AUC is
reported for comparability, but BEDROC (Truchon & Bayly, J Chem Inf Model 2007,
eq. 36) and enrichment factors carry the weight, because on a panel with
0.02-3.8 % positives the top of the ranking is the only part anyone acts on.
"""
import json
import numpy as np, pandas as pd
from scipy import sparse
from sklearn.metrics import roc_auc_score, average_precision_score, matthews_corrcoef

D = "/home/claude/dpn/data"
R = "/home/claude/dpn/results"

MIN_TEST_POS = 40   # tasks with enough held-out positives for a stable ranking metric


def load():
    M = pd.read_parquet(f"{D}/dpn_panel_clean.parquet")
    X = sparse.load_npz(f"{D}/X_ecfp4.npz").astype(np.float32)
    Dsc = np.load(f"{D}/X_desc.npy")
    meta = json.load(open(f"{D}/panel_meta.json"))
    return M, X, Dsc, meta


def eval_tasks(M, meta):
    return [t for t in meta
            if int((M.loc[M.split == "test", t] == 1).sum()) >= MIN_TEST_POS]


def split_idx(M):
    return {s: np.where(M["split"].to_numpy() == s)[0] for s in ("train", "validation", "test")}


def task_idx(M, idx, task):
    """Rows within `idx` with a non-missing label for `task`, plus those labels."""
    y = M[task].to_numpy()[idx]
    keep = ~pd.isna(y)
    return idx[keep], y[keep].astype(np.int8)


# ----------------------------------------------------------------------------
# virtual-screening metrics
# ----------------------------------------------------------------------------
def enrichment_factor(y, s, frac=0.01):
    """Fold-enrichment of actives in the top `frac` of the ranking over random."""
    n = len(y)
    k = max(1, int(round(n * frac)))
    order = np.argsort(-s, kind="stable")
    hits = float(y[order[:k]].sum())
    base = y.sum() / n
    return (hits / k) / base if base > 0 else np.nan


def bedroc(y, s, alpha=80.5):
    """Boltzmann-Enhanced Discrimination of ROC; alpha=80.5 -> top ~2 % dominates.

    1.0 for a perfect ranking, 0.0 for the worst. Truchon & Bayly (2007) eq. 36.
    """
    y = np.asarray(y).astype(int)
    s = np.asarray(s, dtype=float)
    N = len(y)
    n = int(y.sum())
    if n == 0 or n == N:
        return float("nan")
    order = np.argsort(-s, kind="stable")
    ranks = np.flatnonzero(y[order] == 1) + 1          # 1-based ranks of actives
    Ra = n / N

    sum_exp = np.sum(np.exp(-alpha * ranks / N))
    rie_denom = n * (1 - np.exp(-alpha)) / (N * (np.exp(alpha / N) - 1))
    rie = sum_exp / rie_denom

    scale = Ra * np.sinh(alpha / 2) / (np.cosh(alpha / 2) - np.cosh(alpha / 2 - alpha * Ra))
    offset = 1.0 / (1 - np.exp(alpha * (1 - Ra)))
    return float(rie * scale + offset)


def metrics(y, s):
    y = np.asarray(y).astype(int)
    s = np.asarray(s, dtype=float)
    prev = float(y.mean())
    ap = average_precision_score(y, s)
    thr = np.quantile(s, 1 - max(prev, 1e-6))   # predict as many positives as truly exist
    return {
        "n": int(len(y)), "n_pos": int(y.sum()), "prevalence": prev,
        "ROC_AUC": float(roc_auc_score(y, s)),
        "PR_AUC": float(ap),
        "dPR_AUC": float(ap - prev),
        "BEDROC": bedroc(y, s),
        "EF_1pct": float(enrichment_factor(y, s, 0.01)),
        "EF_5pct": float(enrichment_factor(y, s, 0.05)),
        "MCC_at_prev": float(matthews_corrcoef(y, (s >= thr).astype(int))),
    }
