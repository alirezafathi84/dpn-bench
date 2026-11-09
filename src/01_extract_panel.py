"""Extract the DPN-Pain target panel from MolData (PubChem HTS) by streaming."""
import pandas as pd, numpy as np, json, os

RAW = "/home/claude/ext/all_molecular_data.csv"
OUT = "/home/claude/dpn/data"

# Mechanism-anchored panel for painful diabetic neuropathy (PDN/DPNP)
PANEL = {
 # ---- analgesic / nociceptive ion-channel arm ----
 "activity_540275": ("TRPV1_agonist",      "analgesic",      "TRPV1 agonist (capsaicin class; 8% patch FDA-approved for DPN pain)"),
 "activity_540277": ("TRPV1_potentiator",  "analgesic",      "TRPV1 potentiator"),
 "activity_2239":   ("KCNQ2_potentiator",  "analgesic",      "Kv7.2 opener (retigabine/flupirtine class)"),
 "activity_2156":   ("KCNQ2_inhibitor",    "counterscreen",  "Kv7.2 blocker (pro-excitatory; selectivity counter-screen)"),
 "activity_623877": ("K2P_activator",      "analgesic",      "Two-pore K+ (TREK/TASK) activator"),
 "activity_602410": ("K2P_inhibitor",      "counterscreen",  "Two-pore K+ channel inhibitor"),
 "activity_488922": ("K2P_inhibitor_2",    "counterscreen",  "Two-pore K+ channel inhibitor (replicate assay)"),
 "activity_1424":   ("TRP_agonist",        "analgesic",      "Transient receptor potential agonist"),
 # ---- neuroprotective / disease-modifying arm ----
 "activity_624171": ("NRF2_activator",     "neuroprotective","Nrf2/ARE activator (oxidative-stress axis; ALA/curcumin MoA)"),
 "activity_2732":   ("CHOP_inhibitor",     "neuroprotective","CHOP inhibitor (ER-stress/UPR, Schwann-cell injury)"),
 "activity_449763": ("UPR_apoptotic",      "neuroprotective","Activator, apoptotic arm of UPR"),
 "activity_463104": ("UPR_adaptive",       "neuroprotective","Activator, adaptive arm of UPR"),
 "activity_1159519":("ERSR_agonist",       "neuroprotective","ER-stress response agonist"),
 "activity_588621": ("STEP_inhibitor",     "neuroprotective","STriatal-Enriched Phosphatase inhibitor"),
 "activity_435005": ("BetaCell_protect",   "neuroprotective","Inhibitor of beta-cell apoptosis"),
 # ---- glycaemic-axis context tasks (auxiliary, for transfer) ----
 "activity_624172": ("GLP1R_agonist",      "auxiliary",      "GLP-1 receptor agonist"),
 "activity_493160": ("HKDC1_inhibitor",    "auxiliary",      "Hexokinase-domain-containing-1 inhibitor"),
 "activity_493187": ("HKDC1_activator",    "auxiliary",      "Hexokinase-domain-containing-1 activator"),
}

hdr = pd.read_csv(RAW, nrows=0)
cols = list(hdr.columns)
print("total columns:", len(cols))
print("tail columns:", cols[-6:])
missing = [k for k in PANEL if k not in cols]
assert not missing, missing
keep = [c for c in ["smiles", "PUBCHEM_CID", "split"] if c in cols] + list(PANEL)
print("keeping:", keep)

chunks = []
for i, ch in enumerate(pd.read_csv(RAW, usecols=keep, chunksize=200_000)):
    sub = ch[ch[list(PANEL)].notna().any(axis=1)]
    chunks.append(sub)
    if i % 2 == 0:
        print(f"  chunk {i}: rows kept so far = {sum(len(c) for c in chunks)}", flush=True)
df = pd.concat(chunks, ignore_index=True)
df["PUBCHEM_CID"] = df["PUBCHEM_CID"].astype(str)
print("panel rows:", df.shape)
df = df.rename(columns={k: v[0] for k, v in PANEL.items()})
df.to_parquet(f"{OUT}/dpn_panel_raw.parquet", index=False)

meta = {v[0]: {"aid": k.replace("activity_", ""), "arm": v[1], "description": v[2]} for k, v in PANEL.items()}
json.dump(meta, open(f"{OUT}/panel_meta.json", "w"), indent=2)

print("\n=== per-task label counts ===")
rows = []
for k, (name, arm, d) in PANEL.items():
    s = df[name]
    n = int(s.notna().sum()); pos = int((s == 1).sum())
    rows.append((name, arm, n, pos, 100 * pos / max(n, 1)))
    print(f"{name:<20} {arm:<16} n={n:>7}  pos={pos:>6}  ({100*pos/max(n,1):.2f}%)")
pd.DataFrame(rows, columns=["task", "arm", "n", "n_pos", "pct_pos"]).to_csv(f"{OUT}/task_summary.csv", index=False)
