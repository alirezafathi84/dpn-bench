"""Merge featurization shards, deduplicate on canonical SMILES, save final matrices."""
import json
import numpy as np, pandas as pd
from scipy import sparse

D = "/home/claude/dpn/data"
NSHARD = 6
meta = json.load(open(f"{D}/panel_meta.json"))
TASKS = list(meta)

metas, Xs, Ds = [], [], []
for s in range(NSHARD):
    metas.append(pd.read_parquet(f"{D}/shard_{s}_meta.parquet"))
    Xs.append(sparse.load_npz(f"{D}/shard_{s}_ecfp.npz"))
    Ds.append(np.load(f"{D}/shard_{s}_desc.npy"))
M = pd.concat(metas, ignore_index=True)
X = sparse.vstack(Xs).tocsr()
Dd = np.vstack(Ds)
print("merged:", M.shape, X.shape, Dd.shape)

# ---- deduplicate on canonical SMILES; label = max (active in any replicate) ----
M["_row"] = np.arange(len(M))
first = M.drop_duplicates("canonical_smiles", keep="first")
agg = M.groupby("canonical_smiles", sort=False)[TASKS].max()
ded = first.set_index("canonical_smiles").copy()
ded[TASKS] = agg.loc[ded.index, TASKS]
ded = ded.reset_index()
keep = ded["_row"].to_numpy()
X, Dd = X[keep], Dd[keep]
ded = ded.drop(columns=["_row"])
print("after dedup:", ded.shape, X.shape)

sparse.save_npz(f"{D}/X_ecfp4.npz", X)
np.save(f"{D}/X_desc.npy", Dd)
ded.to_parquet(f"{D}/dpn_panel_clean.parquet", index=False)

print("\nsplit sizes:\n", ded["split"].value_counts().to_string())
print("unique Murcko scaffolds:", ded["scaffold"].nunique())
# scaffold leakage check between MolData's official splits
tr = set(ded.loc[ded.split == "train", "scaffold"])
te = set(ded.loc[ded.split == "test", "scaffold"])
print(f"scaffold overlap train/test: {len(tr & te)} of {len(te)} test scaffolds "
      f"({100*len(tr & te)/max(len(te),1):.2f}%)")

rows = []
for t in TASKS:
    for sp in ["train", "validation", "test"]:
        ss = ded.loc[ded.split == sp, t]
        rows.append((t, meta[t]["arm"], sp, int(ss.notna().sum()), int((ss == 1).sum())))
S = pd.DataFrame(rows, columns=["task", "arm", "split", "n", "n_pos"])
S.to_csv(f"{D}/task_split_summary.csv", index=False)
piv = S.pivot_table(index=["arm", "task"], columns="split", values=["n", "n_pos"])
print("\n", piv.to_string())
