"""Audit the screen: memorisation, PAINS alerts and frequent-hitter behaviour.

Three failure modes matter on HTS-derived panels:
  1. memorisation - the query is already a training active (maxTc ~ 1.0)
  2. assay interference - PAINS / polyphenol frequent hitters
  3. promiscuity - one compound topping many unrelated tasks
"""
import sys, os
import numpy as np, pandas as pd
from rdkit import Chem, RDLogger
from rdkit.Chem import FilterCatalog, Descriptors
from rdkit.Chem.FilterCatalog import FilterCatalogParams
sys.path.insert(0, os.path.dirname(__file__))
from dpn_common import R
from library import LIBRARY
RDLogger.DisableLog("rdApp.*")

params = FilterCatalogParams()
for f in (FilterCatalogParams.FilterCatalogs.PAINS_A,
          FilterCatalogParams.FilterCatalogs.PAINS_B,
          FilterCatalogParams.FilterCatalogs.PAINS_C):
    params.AddCatalog(f)
cat = FilterCatalog.FilterCatalog(params)

S = pd.read_csv(f"{R}/screen_library.csv")
smi = {l[0]: l[1] for l in LIBRARY}

flags = []
for c in S["compound"].unique():
    m = Chem.MolFromSmiles(smi[c])
    hit = cat.GetFirstMatch(m) if m else None
    flags.append({"compound": c, "PAINS": "" if hit is None else hit.GetDescription(),
                  "MolWt": round(Descriptors.MolWt(m), 1) if m else np.nan})
F = pd.DataFrame(flags)

ntask = S["task"].nunique()
prom = (S[S.percentile >= 95].groupby("compound").size()
        .rename("n_tasks_top5pct").reset_index())
memo = (S[S.maxTc_train_active >= 0.99].groupby("compound").size()
        .rename("n_tasks_memorised").reset_index())

A = (F.merge(prom, how="left").merge(memo, how="left").fillna(0))
A["n_tasks_top5pct"] = A["n_tasks_top5pct"].astype(int)
A["n_tasks_memorised"] = A["n_tasks_memorised"].astype(int)
A["promiscuity_frac"] = (A["n_tasks_top5pct"] / ntask).round(2)
A = A.sort_values("n_tasks_top5pct", ascending=False)
A.to_csv(f"{R}/screen_audit.csv", index=False)

print(f"tasks in panel: {ntask}\n")
print("=" * 86)
print("FREQUENT HITTERS - compounds in the top 5 % of many unrelated tasks")
print("=" * 86)
print(f"{'compound':<20}{'MolWt':>8}{'top5%':>7}{'frac':>7}  {'PAINS alert'}")
for r in A[A.n_tasks_top5pct > 0].itertuples():
    print(f"{r.compound:<20}{r.MolWt:>8.1f}{r.n_tasks_top5pct:>7}{r.promiscuity_frac:>7.2f}  {r.PAINS[:42]}")

print("\n" + "=" * 86)
print("MEMORISATION - query is itself a training active (maxTc >= 0.99)")
print("=" * 86)
mm = A[A.n_tasks_memorised > 0]
if len(mm) == 0:
    print("none")
for r in mm.itertuples():
    tsk = S[(S.compound == r.compound) & (S.maxTc_train_active >= 0.99)]["task"].tolist()
    print(f"{r.compound:<20} memorised on: {', '.join(tsk)}")

print("\n" + "=" * 86)
print("PAINS-FLAGGED COMPOUNDS IN LIBRARY")
print("=" * 86)
pf = A[A.PAINS != ""]
print(f"{len(pf)} of {len(A)} compounds carry a PAINS alert:")
for r in pf.itertuples():
    print(f"  {r.compound:<20} {r.PAINS}")

# clean ranking: drop memorised, PAINS-flagged and promiscuous, then re-rank
bad = set(A.loc[(A.PAINS != "") | (A.promiscuity_frac >= 0.40), "compound"])
print(f"\nexcluded as interference-prone or promiscuous: {len(bad)} compounds")
print(" ", ", ".join(sorted(bad)))
C = S[(~S.compound.isin(bad)) & (S.maxTc_train_active < 0.99)]
print("\n" + "=" * 86)
print("AUDITED TOP-3 PER TASK  (memorised / PAINS / promiscuous removed)")
print("=" * 86)
for t in sorted(C["task"].unique()):
    sub = C[C.task == t].nlargest(3, "percentile")
    print(f"{t:<20} " + ", ".join(
        f"{r.compound}({r.percentile:.0f}%,Tc={r.maxTc_train_active:.2f})" for r in sub.itertuples()))
C.to_csv(f"{R}/screen_audited.csv", index=False)
