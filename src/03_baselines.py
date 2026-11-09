"""Single-task baselines on ECFP4: LightGBM, L2 logistic regression, Tanimoto-kNN.

Run as:  python3 03_baselines.py <task_name> [...]
Writes one JSON per (model, task) into results/baselines/ so the panel can be
built up across several short runs.
"""
import json, os, sys, time
import numpy as np, pandas as pd
from scipy import sparse
import lightgbm as lgb
from sklearn.linear_model import LogisticRegression
sys.path.insert(0, os.path.dirname(__file__))
from dpn_common import load, split_idx, task_idx, metrics, R

OUT = f"{R}/baselines"
os.makedirs(OUT, exist_ok=True)
SEED = 20260101
N_NEG = 40_000   # negatives retained per task for the GBM


def tanimoto_knn(Xtr, ytr, Xte, k=5, pos_only=True):
    """Similarity-search control: max/mean Tanimoto to the k nearest training actives.

    This is the baseline every QSAR model must beat - if a model cannot outscore
    'find the most similar known active', it has learned nothing beyond lookup.
    """
    ref = Xtr[ytr == 1] if pos_only else Xtr
    a = np.asarray(ref.sum(axis=1)).ravel()          # popcount per reference
    b = np.asarray(Xte.sum(axis=1)).ravel()
    scores = np.zeros(Xte.shape[0], dtype=np.float32)
    step = 2000
    for i in range(0, Xte.shape[0], step):
        blk = Xte[i:i + step]
        inter = (blk @ ref.T).toarray()              # |A and B|
        union = b[i:i + step, None] + a[None, :] - inter
        tan = inter / np.maximum(union, 1e-9)
        kk = min(k, tan.shape[1])
        part = np.partition(tan, -kk, axis=1)[:, -kk:]
        scores[i:i + step] = part.mean(axis=1)
    return scores


def run_task(task, M, X, idx):
    res = {}
    tr_i, ytr = task_idx(M, idx["train"], task)
    va_i, yva = task_idx(M, idx["validation"], task)
    te_i, yte = task_idx(M, idx["test"], task)
    Xtr, Xva, Xte = X[tr_i], X[va_i], X[te_i]
    print(f"  train {Xtr.shape} pos={ytr.sum()} | test {Xte.shape} pos={yte.sum()}", flush=True)

    # ---- LightGBM -----------------------------------------------------------
    # Negatives are subsampled to N_NEG per task. On this panel that is both
    # ~8x faster and measurably *better* than training on all ~300k negatives
    # (NRF2: ROC-AUC 0.867 vs 0.796, EF1% 27.8 vs 19.5), because the effective
    # positive:negative ratio stops starving the split criterion.
    t = time.time()
    rng = np.random.default_rng(SEED)
    neg, pos = np.flatnonzero(ytr == 0), np.flatnonzero(ytr == 1)
    sel = np.concatenate([pos, rng.choice(neg, min(N_NEG, len(neg)), replace=False)])
    sel.sort()
    Xs, ys = Xtr[sel], ytr[sel]
    spw = float((ys == 0).sum() / max((ys == 1).sum(), 1))
    clf = lgb.LGBMClassifier(
        n_estimators=600, learning_rate=0.05, num_leaves=48, max_depth=-1,
        min_child_samples=20, feature_fraction=0.30, bagging_fraction=0.80,
        bagging_freq=1, scale_pos_weight=spw, n_jobs=1, verbose=-1,
        random_state=SEED)
    clf.fit(Xs, ys)
    s = clf.predict_proba(Xte)[:, 1]
    res["LightGBM_ECFP4"] = metrics(yte, s)
    res["LightGBM_ECFP4"]["n_train_used"] = int(len(ys))
    res["LightGBM_ECFP4"]["fit_sec"] = round(time.time() - t, 1)
    np.save(f"{OUT}/pred_LightGBM_{task}.npy", s)
    np.save(f"{OUT}/predval_LightGBM_{task}.npy", clf.predict_proba(Xva)[:, 1])
    print(f"  LightGBM  AUC={res['LightGBM_ECFP4']['ROC_AUC']:.3f} "
          f"BEDROC={res['LightGBM_ECFP4']['BEDROC']:.3f} "
          f"EF1%={res['LightGBM_ECFP4']['EF_1pct']:.1f} ({time.time()-t:.0f}s)", flush=True)

    # ---- logistic regression ------------------------------------------------
    t = time.time()
    lr = LogisticRegression(C=0.1, max_iter=400, class_weight="balanced",
                            solver="liblinear", random_state=SEED)
    lr.fit(Xtr, ytr)
    s = lr.decision_function(Xte)
    np.save(f"{OUT}/pred_LogReg_{task}.npy", s)
    res["LogReg_ECFP4"] = metrics(yte, s)
    res["LogReg_ECFP4"]["fit_sec"] = round(time.time() - t, 1)
    print(f"  LogReg    AUC={res['LogReg_ECFP4']['ROC_AUC']:.3f} "
          f"BEDROC={res['LogReg_ECFP4']['BEDROC']:.3f} ({time.time()-t:.0f}s)", flush=True)

    # ---- Tanimoto similarity search ----------------------------------------
    t = time.time()
    s = tanimoto_knn(Xtr, ytr, Xte, k=5)
    np.save(f"{OUT}/pred_TanimotoKNN_{task}.npy", s)
    res["TanimotoKNN"] = metrics(yte, s)
    res["TanimotoKNN"]["fit_sec"] = round(time.time() - t, 1)
    print(f"  TaniKNN   AUC={res['TanimotoKNN']['ROC_AUC']:.3f} "
          f"BEDROC={res['TanimotoKNN']['BEDROC']:.3f} ({time.time()-t:.0f}s)", flush=True)
    return res


if __name__ == "__main__":
    M, X, Dsc, meta = load()
    idx = split_idx(M)
    for task in sys.argv[1:]:
        print(f"== {task} ({meta[task]['arm']})", flush=True)
        r = run_task(task, M, X, idx)
        json.dump(r, open(f"{OUT}/{task}.json", "w"), indent=2)
