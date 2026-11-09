"""Featurize one shard of the DPN panel (keeps each run inside the 300 s budget)."""
import json, sys, time
import numpy as np, pandas as pd
from scipy import sparse
from rdkit import Chem, RDLogger
from rdkit.Chem import rdFingerprintGenerator, Descriptors, Crippen, rdMolDescriptors, Lipinski
from rdkit.Chem.Scaffolds import MurckoScaffold

RDLogger.DisableLog("rdApp.*")
D = "/home/claude/dpn/data"
SHARD = int(sys.argv[1]); NSHARD = int(sys.argv[2])

meta = json.load(open(f"{D}/panel_meta.json"))
TASKS = list(meta)
df = pd.read_parquet(f"{D}/dpn_panel_raw.parquet")
lo = SHARD * len(df) // NSHARD
hi = (SHARD + 1) * len(df) // NSHARD
df = df.iloc[lo:hi].reset_index(drop=True)
print(f"shard {SHARD}/{NSHARD}: rows {lo}:{hi} = {len(df)}", flush=True)

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
    if len(frags) > 1:
        m = max(frags, key=lambda f: f.GetNumHeavyAtoms())
    for a in m.GetAtoms():
        a.SetIsotope(0)
    try:
        Chem.SanitizeMol(m)
    except Exception:
        return None
    n = m.GetNumHeavyAtoms()
    if n < 6 or n > 70:
        return None
    return m


rows_idx, can_smi, scaffolds, fp_rows, fp_cols, descs = [], [], [], [], [], []
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
    on = list(gen.GetFingerprint(m).GetOnBits())
    fp_rows.extend([r] * len(on)); fp_cols.extend(on)
    descs.append(describe(m))
    if i and i % 40000 == 0:
        print(f"  {i}/{len(df)} kept={r} {time.time()-t0:.0f}s", flush=True)

n = len(rows_idx)
X = sparse.csr_matrix((np.ones(len(fp_rows), np.uint8), (fp_rows, fp_cols)), shape=(n, 1024))
sparse.save_npz(f"{D}/shard_{SHARD}_ecfp.npz", X)
np.save(f"{D}/shard_{SHARD}_desc.npy", np.asarray(descs, dtype=np.float32))
sub = df.iloc[rows_idx].reset_index(drop=True)
out = pd.DataFrame({"canonical_smiles": can_smi, "scaffold": scaffolds,
                    "split": sub["split"].to_numpy(), "cid": sub["PUBCHEM_CID"].astype(str).to_numpy()})
for t in TASKS:
    out[t] = sub[t].to_numpy()
out.to_parquet(f"{D}/shard_{SHARD}_meta.parquet", index=False)
json.dump(DESC, open(f"{D}/desc_names.json", "w"))
print(f"shard {SHARD} done: kept {n}/{len(df)} in {time.time()-t0:.0f}s", flush=True)
