"""Curate + featurize the DPN panel.

Steps
-----
1. Parse SMILES, keep largest organic fragment, strip isotopes, canonicalise.
2. Drop molecules outside a screening-sensible size window.
3. Deduplicate on canonical SMILES (merge labels by max -> an "active in any
   replicate" rule, which is the convention used by PubChem summary assays).
4. Compute ECFP4 (1024 bit, Morgan r=2) as a sparse CSR matrix plus 14 fast
   physico-chemical descriptors.
5. Compute Bemis-Murcko scaffolds for grouped / scaffold-aware evaluation.
"""
import json, time, sys
import numpy as np, pandas as pd
from scipy import sparse
from rdkit import Chem, RDLogger
from rdkit.Chem import rdFingerprintGenerator, Descriptors, Crippen, rdMolDescriptors, Lipinski
from rdkit.Chem.Scaffolds import MurckoScaffold

RDLogger.DisableLog("rdApp.*")
D = "/home/claude/dpn/data"

meta = json.load(open(f"{D}/panel_meta.json"))
TASKS = list(meta)
df = pd.read_parquet(f"{D}/dpn_panel_raw.parquet")
print("input:", df.shape, flush=True)

gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=1024)

DESC = ["MolWt", "LogP", "TPSA", "HBD", "HBA", "RotB", "AromRings", "RingCount",
        "FracCsp3", "HeavyAtoms", "NumHeteroatoms", "NHOHCount", "NOCount", "FormalCharge"]


def describe(m):
    return (Descriptors.MolWt(m), Crippen.MolLogP(m), rdMolDescriptors.CalcTPSA(m),
            Lipinski.NumHDonors(m), Lipinski.NumHAcceptors(m), Lipinski.NumRotatableBonds(m),
            rdMolDescriptors.CalcNumAromaticRings(m), rdMolDescriptors.CalcNumRings(m),
            rdMolDescriptors.CalcFractionCSP3(m), m.GetNumHeavyAtoms(),
            rdMolDescriptors.CalcNumHeteroatoms(m), Lipinski.NHOHCount(m),
            Lipinski.NOCount(m), Chem.GetFormalCharge(m))


def clean(smi):
    m = Chem.MolFromSmiles(smi)
    if m is None:
        return None
    frags = Chem.GetMolFrags(m, asMols=True, sanitizeFrags=False)
    if len(frags) > 1:                       # keep the largest fragment (desalting)
        m = max(frags, key=lambda f: f.GetNumHeavyAtoms())
    for a in m.GetAtoms():
        a.SetIsotope(0)
    try:
        Chem.SanitizeMol(m)
    except Exception:
        return None
    n = m.GetNumHeavyAtoms()
    if n < 6 or n > 70:                      # screening-sensible size window
        return None
    return m


rows_idx, can_smi, scaffolds, fp_rows, fp_cols, mac_rows, mac_cols, descs = [], [], [], [], [], [], [], []
t0 = time.time()
for i, smi in enumerate(df["smiles"].to_numpy()):
    m = clean(smi)
    if m is None:
        continue
    r = len(rows_idx)
    rows_idx.append(i)
    can_smi.append(Chem.MolToSmiles(m))
    try:
        scaffolds.append(MurckoScaffold.MurckoScaffoldSmiles(mol=m))
    except Exception:
        scaffolds.append("")
    on = gen.GetFingerprint(m).GetOnBits()
    fp_rows.extend([r] * len(on)); fp_cols.extend(on)
    descs.append(describe(m))
    if i % 50000 == 0:
        print(f"  {i}/{len(df)}  kept={r}  {time.time()-t0:.0f}s", flush=True)

n = len(rows_idx)
print(f"kept {n} / {len(df)} molecules in {time.time()-t0:.0f}s", flush=True)

X_ecfp = sparse.csr_matrix((np.ones(len(fp_rows), np.uint8), (fp_rows, fp_cols)), shape=(n, 1024))
X_desc = np.asarray(descs, dtype=np.float32)

sub = df.iloc[rows_idx].reset_index(drop=True)
out = pd.DataFrame({"canonical_smiles": can_smi, "scaffold": scaffolds,
                    "split": sub["split"].to_numpy(), "cid": sub["PUBCHEM_CID"].to_numpy()})
for t in TASKS:
    out[t] = sub[t].to_numpy()

# deduplicate on canonical SMILES; label = max over duplicates, split = first
agg = {t: "max" for t in TASKS}
agg.update({"scaffold": "first", "split": "first", "cid": "first"})
ded = out.groupby("canonical_smiles", as_index=False, sort=False).agg(agg)
keep_pos = out.drop_duplicates("canonical_smiles", keep="first").index.to_numpy()
order = pd.Index(out["canonical_smiles"]).drop_duplicates()
ded = ded.set_index("canonical_smiles").loc[order].reset_index()

print("after dedup:", ded.shape, flush=True)
X_ecfp, X_desc = X_ecfp[keep_pos], X_desc[keep_pos]

sparse.save_npz(f"{D}/X_ecfp4.npz", X_ecfp)
np.save(f"{D}/X_desc.npy", X_desc)
ded.to_parquet(f"{D}/dpn_panel_clean.parquet", index=False)
json.dump(DESC, open(f"{D}/desc_names.json", "w"))

print("\nsplit sizes:\n", ded["split"].value_counts())
print("unique Murcko scaffolds:", ded["scaffold"].nunique())
summ = []
for t in TASKS:
    s = ded[t]
    for sp in ["train", "validation", "test"]:
        ss = ded.loc[ded.split == sp, t]
        summ.append((t, meta[t]["arm"], sp, int(ss.notna().sum()), int((ss == 1).sum())))
pd.DataFrame(summ, columns=["task", "arm", "split", "n", "n_pos"]).to_csv(f"{D}/task_split_summary.csv", index=False)
print(pd.DataFrame(summ, columns=["task", "arm", "split", "n", "n_pos"]).pivot_table(
    index=["task", "arm"], columns="split", values="n_pos").to_string())
