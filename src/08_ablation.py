"""Single-task vs multi-task ablation.

The benchmark's one claim to priority is that multi-task learning over a
mechanism-anchored panel beats single-task learning. Comparing MTL-FCNN against
LightGBM confounds "multi-task helps" with "neural network helps", so this
script trains the IDENTICAL architecture and hyper-parameters with a single head
on a single task's labelled rows, and compares it to the corresponding head of
the trained multi-task model on the same test rows.

Usage:  python3 08_ablation.py TRPV1_agonist NRF2_activator ...
"""
import json, os, sys, time
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
from dpn_common import load, split_idx, task_idx, metrics, R, D
exec(open(os.path.join(os.path.dirname(__file__), "04_mtl.py")).read().split("def main(")[0])

OUT = f"{R}/ablation"
os.makedirs(OUT, exist_ok=True)
EPOCHS = 13          # same budget at which the multi-task model peaked
SEED = 20260101


def train_single(X, Dz, rows, y, va_rows, yva, d_in):
    """Same trunk, same optimiser, one head."""
    rng = np.random.default_rng(SEED)
    P = init_params(d_in, 1, rng)
    mAd = {k: np.zeros_like(v) for k, v in P.items()}
    vAd = {k: np.zeros_like(v) for k, v in P.items()}
    b1, b2, epsA = 0.9, 0.999, 1e-8
    step = 0
    pos_w = np.array([np.clip((y == 0).sum() / max((y == 1).sum(), 1), 1, 200)], np.float32)
    Y = y.astype(np.float32).reshape(-1, 1)
    Mk = np.ones_like(Y)

    best, best_P = -np.inf, {k: v.copy() for k, v in P.items()}
    for ep in range(EPOCHS):
        order = rng.permutation(len(rows))
        for i in range(0, len(order) - BATCH + 1, BATCH):
            sel = order[i:i + BATCH]
            Xb = batch_dense(X, Dz, rows[sel])
            logits, cache = forward(P, Xb, train=True, rng=rng)
            loss, dl = masked_bce(logits, Y[sel], Mk[sel], pos_w)
            G = backward(P, cache, dl)
            step += 1
            for k in P:
                mAd[k] = b1 * mAd[k] + (1 - b1) * G[k]
                vAd[k] = b2 * vAd[k] + (1 - b2) * G[k] ** 2
                P[k] -= (LR * (mAd[k] / (1 - b1 ** step)) /
                         (np.sqrt(vAd[k] / (1 - b2 ** step)) + epsA)).astype(np.float32)
        s = predict(P, X, Dz, va_rows)[:, 0]
        dpr = metrics(yva, s)["dPR_AUC"]
        if dpr > best:
            best, best_P = dpr, {k: v.copy() for k, v in P.items()}
    return best_P, best


if __name__ == "__main__":
    M, X, Dsc, meta = load()
    idx = split_idx(M)
    tasks = list(meta)
    mu, sd = np.load(f"{D}/desc_scaler.npy")
    Dz = ((Dsc - mu) / sd).astype(np.float32)
    d_in = X.shape[1] + Dz.shape[1]
    mtl_logits = np.load(f"{R}/mtl_test_logits.npy")

    for task in sys.argv[1:]:
        t0 = time.time()
        j = tasks.index(task)
        tr, ytr = task_idx(M, idx["train"], task)
        va, yva = task_idx(M, idx["validation"], task)
        te, yte = task_idx(M, idx["test"], task)
        print(f"== {task}: train {len(tr)} (pos {ytr.sum()}), test {len(te)} (pos {yte.sum()})", flush=True)

        P, bestval = train_single(X, Dz, tr, ytr, va, yva, d_in)
        s_st = predict(P, X, Dz, te)[:, 0]
        m_st = metrics(yte, s_st)

        # multi-task head on exactly the same test rows
        keep = np.isin(idx["test"], te)
        m_mt = metrics(yte, mtl_logits[keep, j])

        rec = {"task": task, "arm": meta[task]["arm"],
               "single_task": m_st, "multi_task": m_mt,
               "epochs": EPOCHS, "fit_sec": round(time.time() - t0, 1)}
        json.dump(rec, open(f"{OUT}/{task}.json", "w"), indent=2)
        print(f"   single-task  AUC={m_st['ROC_AUC']:.3f} BEDROC={m_st['BEDROC']:.3f} EF1%={m_st['EF_1pct']:.1f}")
        print(f"   multi-task   AUC={m_mt['ROC_AUC']:.3f} BEDROC={m_mt['BEDROC']:.3f} EF1%={m_mt['EF_1pct']:.1f}")
        print(f"   delta BEDROC = {m_mt['BEDROC'] - m_st['BEDROC']:+.3f}   ({time.time()-t0:.0f}s)", flush=True)
