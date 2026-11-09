"""Multi-task feed-forward network over the DPN panel (ECFP4 + physchem).

One shared trunk, 18 sigmoid heads (all panel tasks, including the three too
sparse to evaluate - they are kept purely as auxiliary signal). Loss is a
per-task positive-weighted binary cross-entropy, masked so a molecule only
contributes to heads whose assay actually tested it. This is the standard
"ECFP + multitask FCNN" baseline from MoleculeNet/MolData, implemented directly
in NumPy so the repository has no deep-learning dependency.

Usage:
    python3 04_mtl.py --check            # numerical gradient check only
    python3 04_mtl.py --epochs 4         # train 4 epochs, resuming from checkpoint
"""
import argparse, json, os, sys, time
import numpy as np, pandas as pd
from scipy import sparse
sys.path.insert(0, os.path.dirname(__file__))
from dpn_common import load, split_idx, eval_tasks, metrics, R, D

CKPT = f"{R}/mtl_ckpt.npz"
HIST = f"{R}/mtl_history.json"
HID = (512, 128)
BATCH = 512
LR = 1e-3
DROPOUT = 0.25
SEED = 20260101


# ---------------------------------------------------------------- model ----
def init_params(d_in, n_task, rng):
    sizes = [d_in, *HID, n_task]
    P = {}
    for i in range(len(sizes) - 1):
        fan_in, fan_out = sizes[i], sizes[i + 1]
        P[f"W{i}"] = (rng.standard_normal((fan_in, fan_out)) *
                      np.sqrt(2.0 / fan_in)).astype(np.float32)
        P[f"b{i}"] = np.zeros(fan_out, np.float32)
    return P


def forward(P, X, train=False, rng=None, drop=DROPOUT):
    """Returns logits and the cache needed for the backward pass."""
    nL = len(HID) + 1
    acts, masks = [X], []
    h = X
    for i in range(nL - 1):
        h = np.maximum(h @ P[f"W{i}"] + P[f"b{i}"], 0.0)
        if train and drop > 0:
            m = (rng.random(h.shape) >= drop).astype(np.float32) / (1.0 - drop)
            h = h * m
            masks.append(m)
        else:
            masks.append(None)
        acts.append(h)
    logits = h @ P[f"W{nL-1}"] + P[f"b{nL-1}"]
    return logits, (acts, masks)


def masked_bce(logits, Y, Mk, pos_w):
    """Y in {0,1} (any value where Mk==0 is ignored). Numerically stable."""
    z = logits
    w = np.where(Y > 0.5, pos_w[None, :], 1.0) * Mk
    # log(1+exp(-|z|)) + max(z,0) - z*y   == stable BCE-with-logits
    loss_el = np.maximum(z, 0) - z * Y + np.log1p(np.exp(-np.abs(z)))
    denom = max(w.sum(), 1e-8)
    loss = float((w * loss_el).sum() / denom)
    p = np.where(z >= 0, 1.0 / (1.0 + np.exp(-np.abs(z))), np.exp(-np.abs(z)) / (1.0 + np.exp(-np.abs(z))))
    dlogits = w * (p - Y) / denom
    return loss, (dlogits.astype(np.float32) if logits.dtype == np.float32 else dlogits)


def backward(P, cache, dlogits):
    acts, masks = cache
    nL = len(HID) + 1
    G = {}
    d = dlogits
    for i in range(nL - 1, -1, -1):
        G[f"W{i}"] = acts[i].T @ d
        G[f"b{i}"] = d.sum(axis=0)
        if i > 0:
            d = d @ P[f"W{i}"].T
            if masks[i - 1] is not None:
                d = d * masks[i - 1]
            d = d * (acts[i] > 0)
    return G


# ------------------------------------------------------------ gradcheck ----
def gradient_check():
    rng = np.random.default_rng(0)
    d_in, n_task, n = 12, 4, 7
    # float64 throughout: a central difference with eps=1e-3 needs more than
    # float32's ~1e-7 relative precision or the check is dominated by round-off.
    P = {k: v.astype(np.float64) for k, v in init_params(d_in, n_task, rng).items()}
    X = rng.standard_normal((n, d_in))
    Y = (rng.random((n, n_task)) > 0.6).astype(np.float64)
    Mk = (rng.random((n, n_task)) > 0.3).astype(np.float64)
    pos_w = np.full(n_task, 3.0, np.float64)

    logits, cache = forward(P, X, train=False)
    loss, dl = masked_bce(logits, Y, Mk, pos_w)
    G = backward(P, cache, dl)

    worst = 0.0
    eps = 1e-3
    for k in P:
        flat = P[k].ravel()
        for j in rng.choice(flat.size, min(12, flat.size), replace=False):
            orig = flat[j]
            flat[j] = orig + eps
            l1, _ = masked_bce(forward(P, X)[0], Y, Mk, pos_w)
            flat[j] = orig - eps
            l2, _ = masked_bce(forward(P, X)[0], Y, Mk, pos_w)
            flat[j] = orig
            num = (l1 - l2) / (2 * eps)
            ana = G[k].ravel()[j]
            worst = max(worst, abs(num - ana) / max(abs(num) + abs(ana), 1e-8))
    print(f"gradient check: worst relative error = {worst:.3e}  "
          f"({'PASS' if worst < 1e-4 else 'FAIL'})")
    return worst


# ----------------------------------------------------------------- data ----
def build(M, X, Dsc, meta):
    tasks = list(meta)
    Yall = M[tasks].to_numpy(dtype=np.float32)
    Mk = (~np.isnan(Yall)).astype(np.float32)
    Y = np.nan_to_num(Yall, nan=0.0)
    mu, sd = Dsc.mean(0), Dsc.std(0) + 1e-6
    Dz = ((Dsc - mu) / sd).astype(np.float32)
    np.save(f"{D}/desc_scaler.npy", np.vstack([mu, sd]))
    return tasks, Y, Mk, Dz


def batch_dense(X, Dz, rows):
    return np.hstack([X[rows].toarray(), Dz[rows]]).astype(np.float32)


def predict(P, X, Dz, rows, bs=4096):
    out = []
    for i in range(0, len(rows), bs):
        r = rows[i:i + bs]
        out.append(forward(P, batch_dense(X, Dz, r))[0])
    return np.vstack(out)


# ---------------------------------------------------------------- train ----
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=0)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.check:
        gradient_check()
        return

    M, X, Dsc, meta = load()
    idx = split_idx(M)
    tasks, Y, Mk, Dz = build(M, X, Dsc, meta)
    ev = eval_tasks(M, meta)
    d_in = X.shape[1] + Dz.shape[1]
    rng = np.random.default_rng(SEED)

    tr, va = idx["train"], idx["validation"]
    pos_w = np.zeros(len(tasks), np.float32)
    for j, t in enumerate(tasks):
        m = Mk[tr, j] > 0
        npos = (Y[tr, j][m] == 1).sum()
        pos_w[j] = np.clip((m.sum() - npos) / max(npos, 1), 1, 200)
    print("pos_weight per task:", dict(zip(tasks, pos_w.round(1))), flush=True)

    if os.path.exists(CKPT):
        z = np.load(CKPT)
        P = {k: z[k] for k in z.files if k[0] in "Wb"}
        state = {k: z[f"m_{k}"] for k in P}, {k: z[f"v_{k}"] for k in P}
        step = int(z["step"])
        hist = json.load(open(HIST))
        print(f"resumed from checkpoint: epoch {len(hist)}, step {step}", flush=True)
    else:
        gradient_check()
        P = init_params(d_in, len(tasks), rng)
        state = ({k: np.zeros_like(v) for k, v in P.items()},
                 {k: np.zeros_like(v) for k, v in P.items()})
        step = 0
        hist = []
    mAd, vAd = state
    b1, b2, epsA = 0.9, 0.999, 1e-8

    for ep in range(a.epochs):
        t0 = time.time()
        order = rng.permutation(tr)
        tot, nb = 0.0, 0
        for i in range(0, len(order) - BATCH + 1, BATCH):
            rows = order[i:i + BATCH]
            Xb = batch_dense(X, Dz, rows)
            logits, cache = forward(P, Xb, train=True, rng=rng)
            loss, dl = masked_bce(logits, Y[rows], Mk[rows], pos_w)
            G = backward(P, cache, dl)
            step += 1
            for k in P:
                mAd[k] = b1 * mAd[k] + (1 - b1) * G[k]
                vAd[k] = b2 * vAd[k] + (1 - b2) * G[k] ** 2
                mh = mAd[k] / (1 - b1 ** step)
                vh = vAd[k] / (1 - b2 ** step)
                P[k] -= (LR * mh / (np.sqrt(vh) + epsA)).astype(np.float32)
            tot += loss; nb += 1

        lg = predict(P, X, Dz, va)
        sc = []
        for t in ev:
            j = tasks.index(t)
            m = Mk[va, j] > 0
            sc.append(metrics(Y[va, j][m], lg[m, j])["dPR_AUC"])
        mean_dpr = float(np.mean(sc))
        hist.append({"epoch": len(hist) + 1, "train_loss": tot / nb,
                     "val_mean_dPR_AUC": mean_dpr, "sec": round(time.time() - t0, 1)})
        print(f"epoch {hist[-1]['epoch']:>2}  loss={tot/nb:.4f}  "
              f"val mean dPR-AUC={mean_dpr:.4f}  ({time.time()-t0:.0f}s)", flush=True)

        save = {**P, **{f"m_{k}": v for k, v in mAd.items()},
                **{f"v_{k}": v for k, v in vAd.items()}, "step": step}
        np.savez(CKPT, **save)
        if mean_dpr >= max(h["val_mean_dPR_AUC"] for h in hist):
            np.savez(f"{R}/mtl_best.npz", **P)
            print("   -> new best, saved mtl_best.npz", flush=True)
        json.dump(hist, open(HIST, "w"), indent=1)


if __name__ == "__main__":
    main()
