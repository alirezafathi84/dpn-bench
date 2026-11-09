"""Score the best multi-task checkpoint on the test split and assemble the
benchmark table against the single-task baselines."""
import json, os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
from dpn_common import load, split_idx, eval_tasks, metrics, R, D
import importlib
mtl = importlib.import_module("04_mtl") if False else None
sys.path.insert(0, os.path.dirname(__file__))
exec(open(os.path.join(os.path.dirname(__file__), "04_mtl.py")).read().split("def main(")[0])

M, X, Dsc, meta = load()
idx = split_idx(M)
tasks = list(meta)
ev = eval_tasks(M, meta)
mu, sd = np.load(f"{D}/desc_scaler.npy")
Dz = ((Dsc - mu) / sd).astype(np.float32)

z = np.load(f"{R}/mtl_best.npz")
P = {k: z[k] for k in z.files}
te = idx["test"]
logit_te = predict(P, X, Dz, te)
np.save(f"{R}/mtl_test_logits.npy", logit_te)
np.save(f"{R}/mtl_val_logits.npy", predict(P, X, Dz, idx["validation"]))

rows = []
for t in ev:
    j = tasks.index(t)
    y = M[t].to_numpy()[te]
    m = ~pd.isna(y)
    yy = y[m].astype(int)
    r = metrics(yy, logit_te[m, j])
    r.update(task=t, arm=meta[t]["arm"], model="MTL_FCNN")
    rows.append(r)
    b = json.load(open(f"{R}/baselines/{t}.json"))
    for name, mm in b.items():
        mm = dict(mm); mm.update(task=t, arm=meta[t]["arm"], model=name)
        rows.append(mm)

T = pd.DataFrame(rows)
T = T[["arm", "task", "model", "n", "n_pos", "prevalence", "ROC_AUC", "PR_AUC",
       "dPR_AUC", "BEDROC", "EF_1pct", "EF_5pct", "MCC_at_prev"]]
T.to_csv(f"{R}/benchmark_full.csv", index=False)

print("=" * 108)
print("DPN-Bench: 15 mechanism-anchored tasks, MolData scaffold split, held-out test")
print("=" * 108)
for metric in ["ROC_AUC", "BEDROC", "EF_1pct"]:
    piv = T.pivot_table(index=["arm", "task"], columns="model", values=metric)
    piv = piv[["TanimotoKNN", "LogReg_ECFP4", "LightGBM_ECFP4", "MTL_FCNN"]]
    print(f"\n--- {metric} ---")
    print(piv.round(3).to_string())
    print("MEAN:", piv.mean().round(3).to_dict())

# win counts
print("\n--- per-task winner (BEDROC) ---")
piv = T.pivot_table(index="task", columns="model", values="BEDROC")
win = piv.idxmax(axis=1)
print(win.value_counts().to_string())

summ = T.groupby("model")[["ROC_AUC", "PR_AUC", "dPR_AUC", "BEDROC", "EF_1pct", "EF_5pct"]].mean()
summ = summ.loc[["TanimotoKNN", "LogReg_ECFP4", "LightGBM_ECFP4", "MTL_FCNN"]]
summ.round(4).to_csv(f"{R}/benchmark_summary.csv")
print("\n--- panel means ---")
print(summ.round(4).to_string())
