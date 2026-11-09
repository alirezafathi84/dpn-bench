"""Score the curated DPNP / phytochemical library against the trained panel.

For every (compound, task) we report
  * percentile  - rank of the MTL score inside the 39.5k-compound test split,
                  i.e. "this compound beats X % of a real screening deck"
  * p_active    - Mondrian inductive-conformal p-value against *validation
                  actives* for that task. Large p = score is consistent with
                  the known actives; small p = inconsistent.
  * maxTc       - maximum Tanimoto to any training active for that task
                  (applicability domain: high maxTc means the prediction is
                  essentially a near-neighbour lookup, not an extrapolation).
"""
import json, os, sys
import numpy as np, pandas as pd
from scipy import sparse
from rdkit import Chem, RDLogger
from rdkit.Chem import rdFingerprintGenerator, Descriptors, Crippen, rdMolDescriptors, Lipinski
sys.path.insert(0, os.path.dirname(__file__))
from dpn_common import load, split_idx, eval_tasks, R, D
from library import LIBRARY
exec(open(os.path.join(os.path.dirname(__file__), "04_mtl.py")).read().split("def main(")[0])

RDLogger.DisableLog("rdApp.*")
gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=1024)


def featurize(smiles):
    rows, cols, descs, ok = [], [], [], []
    for r, smi in enumerate(smiles):
        m = Chem.MolFromSmiles(smi)
        if m is None:
            ok.append(False); continue
        ok.append(True)
        on = list(gen.GetFingerprint(m).GetOnBits())
        rows.extend([len(descs)] * len(on)); cols.extend(on)
        descs.append((Descriptors.MolWt(m), Crippen.MolLogP(m), rdMolDescriptors.CalcTPSA(m),
                      Lipinski.NumHDonors(m), Lipinski.NumHAcceptors(m), Lipinski.NumRotatableBonds(m),
                      rdMolDescriptors.CalcNumAromaticRings(m), rdMolDescriptors.CalcNumRings(m),
                      rdMolDescriptors.CalcFractionCSP3(m), m.GetNumHeavyAtoms(),
                      rdMolDescriptors.CalcNumHeteroatoms(m), Lipinski.NHOHCount(m),
                      Lipinski.NOCount(m), Chem.GetFormalCharge(m)))
    X = sparse.csr_matrix((np.ones(len(rows), np.uint8), (rows, cols)), shape=(len(descs), 1024))
    return X, np.asarray(descs, np.float32), np.asarray(ok)


def max_tanimoto(Xq, Xref):
    if Xref.shape[0] == 0:
        return np.zeros(Xq.shape[0])
    a = np.asarray(Xref.sum(1)).ravel(); b = np.asarray(Xq.sum(1)).ravel()
    inter = (Xq @ Xref.T).toarray()
    union = b[:, None] + a[None, :] - inter
    return (inter / np.maximum(union, 1e-9)).max(1)


M, X, Dsc, meta = load()
idx = split_idx(M)
tasks = list(meta); ev = eval_tasks(M, meta)
mu, sd = np.load(f"{D}/desc_scaler.npy")
P = {k: v for k, v in np.load(f"{R}/mtl_best.npz").items()}

names = [l[0] for l in LIBRARY]; smis = [l[1] for l in LIBRARY]
Xq, Dq, ok = featurize(smis)
bad = [n for n, o in zip(names, ok) if not o]
if bad:
    print("UNPARSEABLE (dropped):", bad)
names = [n for n, o in zip(names, ok) if o]
cls = [l[2] for l, o in zip(LIBRARY, ok) if o]
note = [l[3] for l, o in zip(LIBRARY, ok) if o]
print(f"library: {len(names)} compounds parsed of {len(LIBRARY)}")

Dqz = ((Dq - mu) / sd).astype(np.float32)
Xq_in = np.hstack([Xq.toarray(), Dqz]).astype(np.float32)
logit_q = forward(P, Xq_in)[0]

te, va = idx["test"], idx["validation"]
logit_te = np.load(f"{R}/mtl_test_logits.npy")
logit_va = np.load(f"{R}/mtl_val_logits.npy")

recs = []
for t in ev:
    j = tasks.index(t)
    ref = logit_te[:, j]
    yv = M[t].to_numpy()[va]
    cal = logit_va[~pd.isna(yv) & (yv == 1), j]          # validation actives
    ytr = M[t].to_numpy()[idx["train"]]
    act_rows = idx["train"][(~pd.isna(ytr)) & (ytr == 1)]
    mtc = max_tanimoto(Xq, X[act_rows])
    for i, nm in enumerate(names):
        s = logit_q[i, j]
        recs.append({
            "task": t, "arm": meta[t]["arm"], "compound": nm, "class": cls[i], "note": note[i],
            "score": float(s),
            "percentile": float((ref < s).mean() * 100),
            "p_active": float(((cal <= s).sum() + 1) / (len(cal) + 1)),
            "maxTc_train_active": float(mtc[i]),
        })
S = pd.DataFrame(recs)
S.to_csv(f"{R}/screen_library.csv", index=False)

print("\n" + "=" * 92)
print("POSITIVE CONTROLS - does the panel recover known pharmacology?")
print("=" * 92)
checks = [("capsaicin", "TRPV1_agonist"), ("6_gingerol", "TRPV1_agonist"),
          ("piperine", "TRPV1_agonist"), ("sulforaphane", "NRF2_activator"),
          ("curcumin", "NRF2_activator"), ("alpha_lipoic_acid", "NRF2_activator"),
          ("thymoquinone", "NRF2_activator"), ("retigabine", "KCNQ2_potentiator"),
          ("flupirtine", "KCNQ2_potentiator"), ("glucose", "TRPV1_agonist"),
          ("urea", "NRF2_activator"), ("sucrose", "KCNQ2_potentiator")]
print(f"{'compound':<20}{'task':<20}{'pct':>7}{'p_act':>8}{'maxTc':>8}   expectation")
for c, t in checks:
    r = S[(S.compound == c) & (S.task == t)]
    if len(r) == 0:
        continue
    r = r.iloc[0]
    exp = "NEGATIVE control" if r["class"] == "control" else "active expected"
    print(f"{c:<20}{t:<20}{r.percentile:>7.1f}{r.p_active:>8.3f}{r.maxTc_train_active:>8.2f}   {exp}")

print("\n" + "=" * 92)
print("TOP-RANKED LIBRARY COMPOUNDS PER TASK (percentile vs 39.5k test deck)")
print("=" * 92)
for t in ev:
    sub = S[S.task == t].nlargest(5, "percentile")
    head = ", ".join(f"{r.compound}({r.percentile:.0f}%,p={r.p_active:.2f})" for r in sub.itertuples())
    print(f"{t:<20} {head}")

print("\n--- mean percentile by compound class (all analgesic+neuroprotective tasks) ---")
sel = S[S.arm.isin(["analgesic", "neuroprotective"])]
print(sel.groupby("class")["percentile"].agg(["mean", "median", "count"]).round(1).to_string())
