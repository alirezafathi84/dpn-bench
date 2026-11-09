# DPN-Bench: a mechanism-anchored molecular ML benchmark for painful diabetic neuropathy

Multi-task virtual screening over 15 target endpoints chosen for their mechanistic
link to diabetic peripheral neuropathic pain (DPNP), with a scaffold-split
benchmark, a conformal-calibrated screen of guideline drugs and phytochemicals,
and an interference audit.

Everything here was trained and evaluated end-to-end before release. No reported
number is copied from a paper; all come from `results/`.

## Why these targets

The panel is not a random assay grab. Each endpoint sits on a pathway with an
approved or clinical-stage agent in DPNP:

| Arm | Tasks | Rationale |
|---|---|---|
| Analgesic | TRPV1 agonist/potentiator, KCNQ2 potentiator, K2P activator, TRP agonist | capsaicin 8% patch is FDA-approved for DPNP foot pain; Kv7 openers are the retigabine/flupirtine class; TREK-1 activation is analgesic |
| Counter-screen | KCNQ2 inhibitor, K2P inhibitor x2 | pro-excitatory directions — used as selectivity filters, not objectives |
| Neuroprotective | Nrf2/ARE activator, CHOP inhibitor, UPR adaptive/apoptotic, STEP inhibitor, beta-cell protection | oxidative stress and ER stress are the core DPN mechanisms; Nrf2 is the shared MoA of alpha-lipoic acid, curcumin and sulforaphane |
| Auxiliary | GLP-1R, HKDC1 inhibitor/activator | glycaemic axis, kept for multi-task transfer |

## Data

| | |
|---|---|
| Source | **MolData** (Keshavarzi Arshadi et al., *J Cheminform* 2022) — PubChem HTS, `github.com/LumosBio/MolData` |
| Molecules after curation | **415,085** |
| Bemis–Murcko scaffolds | **104,706** |
| Tasks | 18 trained / **15 evaluated** (>= 40 test positives) |
| Positive rate | 0.01 % – 3.8 % |
| Split | MolData official scaffold split (347,197 / 28,379 / 39,509) |
| Scaffold leakage train→test | **1.85 %** |

Curation: desalting (largest organic fragment), isotope stripping, sanitisation,
6–70 heavy-atom window, canonical-SMILES dedup with max-label merge.
Features: ECFP4 (Morgan r=2, 1024 bit, sparse CSR) + 14 physico-chemical descriptors.

## Results (held-out test, mean over 15 tasks)

| Model | ROC-AUC | BEDROC (α=80.5) | EF 1% |
|---|---|---|---|
| Tanimoto kNN (similarity search) | 0.663 | 0.174 | 14.4 |
| Logistic regression | 0.771 | 0.144 | 11.6 |
| LightGBM | 0.788 | 0.232 | 18.8 |
| **MTL-FCNN (this work)** | **0.824** | **0.260** | **22.0** |

MTL-FCNN wins 9/15 tasks on BEDROC, LightGBM 6/15. Full per-task table in
`results/benchmark_full.csv`; figure in `results/fig_benchmark.png`.

Two findings worth keeping in view:

- **Similarity search beats the linear model on early recognition** (BEDROC 0.174
  vs 0.144) despite much worse global AUC. Any new method must be compared
  against Tanimoto kNN, not just against a regression baseline.
- **Negative subsampling helps.** Keeping 40k negatives per task instead of all
  ~300k made LightGBM both ~8x faster *and* better (NRF2: ROC-AUC 0.867 vs 0.796,
  EF1% 27.8 vs 19.5). The earlier full-data run was crippled by early stopping on
  a validation metric that misfires at 0.3 % prevalence.

## Screen of guideline drugs and phytochemicals

59 compounds (guideline first-line, adjuncts, aldose-reductase inhibitors,
phytochemicals with DPN literature, negative controls) scored against the panel,
with three columns that make the output auditable:

- `percentile` — rank inside the 39.5k-compound test deck
- `p_active` — Mondrian inductive-conformal p-value vs validation actives
- `maxTc_train_active` — max Tanimoto to a training active (applicability domain)

### Positive and negative controls

| Compound | Task | Percentile | p_active | maxTc | Verdict |
|---|---|---|---|---|---|
| capsaicin | TRPV1 agonist | 99.7 | 0.84 | **1.00** | memorised — it *is* a training active |
| retigabine | KCNQ2 potentiator | 85.6 | 0.38 | 0.40 | genuine extrapolation |
| flupirtine | KCNQ2 potentiator | 63.6 | 0.21 | 0.38 | genuine, weaker |
| curcumin | Nrf2 activator | 87.8 | 0.27 | 0.48 | genuine |
| cinnamaldehyde | Nrf2 activator | 100.0 | 0.81 | 0.39 | genuine — known Michael-acceptor Nrf2 activator |
| **sulforaphane** | Nrf2 activator | **32.3** | 0.03 | 0.14 | **missed** |
| **alpha-lipoic acid** | Nrf2 activator | **28.0** | 0.03 | 0.18 | **missed** |
| sucrose | KCNQ2 potentiator | 0.4 | 0.01 | 0.13 | correctly rejected |
| glucose | TRPV1 agonist | 1.1 | 0.02 | 0.11 | correctly rejected |
| **urea** | Nrf2 activator | **65.2** | 0.10 | 0.17 | **false positive** |

The two misses are the informative ones. Sulforaphane and alpha-lipoic acid are
small, covalent/redox-acting Nrf2 activators that modify KEAP1 cysteines. A
fingerprint QSAR trained on a reporter-gene HTS cannot represent that mechanism,
and both sit far outside the applicability domain (maxTc 0.14–0.18). **The model
is not a substitute for mechanism.**

### Interference audit — read this before trusting any hit

Before auditing, quercetin, luteolin, mangiferin, EGCG, ursolic/oleanolic acid
and alpha-tocopherol topped nearly every task. That is not polypharmacology, it
is the classic HTS frequent-hitter artefact:

- **11 of 59** compounds carry a PAINS alert (mostly `catechol_A`: quercetin,
  luteolin, EGCG, mangiferin, rosmarinic acid, baicalein)
- **3** were memorised (capsaicin, ursolic acid, berberine)
- alpha-tocopherol reached the top 5 % on 7/15 unrelated tasks

`07_audit.py` removes memorised, PAINS-flagged and promiscuous (>= 40 % of tasks)
compounds and re-ranks. `results/screen_audited.csv` is the ranking to cite.
Residual false positives remain — sucrose still ranks 99th percentile on
K2P activator — so the audited list is a hypothesis generator, not a shortlist.

## Manuscript

`paper/PDPN_Treatment_IEEE.docx` — IEEE conference format (US Letter, two column,
Times New Roman 10 pt), 5 pages, 20 references. Covers the graded clinical
treatment evidence and this benchmark. `paper/build_docx.js` regenerates it;
`paper/dpn_bench_ieee.tex` is the LaTeX variant for the methods-only version.

## Testing

```bash
pytest tests/ -v          # metric correctness + hand-written gradient check
python src/04_mtl.py --check
```

CI runs both on Python 3.11 and 3.12 (`.github/workflows/ci.yml`).

## Reproducing

```bash
pip install -r requirements.txt
python src/01_extract_panel.py          # stream the panel out of MolData
python src/02a_featurize_shard.py 0 6   # ... shards 0-5
python src/02b_merge.py                 # dedup + scaffold-leakage check
python src/03_baselines.py NRF2_activator KCNQ2_potentiator ...
python src/04_mtl.py --check            # numerical gradient check (must PASS)
python src/04_mtl.py --epochs 17
python src/05_evaluate.py               # benchmark table
python src/06_screen.py                 # library screen + conformal p-values
python src/07_audit.py                  # PAINS / memorisation / promiscuity
```

The multi-task net is plain NumPy — no PyTorch, no GPU. It trains in ~12 s/epoch
on one CPU core and converges by epoch 13 (validation mean ΔPR-AUC 0.097).
`--check` runs a float64 central-difference gradient check; it reports a worst
relative error of 2.3e-6, which is the finite-difference truncation floor.

## Limitations

1. Single-conformer 2D fingerprints; no structure, no docking, no 3D.
2. Primary HTS labels are single-concentration and noisy; no dose-response confirmation.
3. Pathway assays (Nrf2, UPR, CHOP) are reporter read-outs — an active is not necessarily a direct binder.
4. K2P activator is near-chance (ROC-AUC 0.568); phenotypic assays resist fingerprint QSAR.
5. Covalent and redox mechanisms are systematically missed (see sulforaphane, ALA).
6. No ADMET, no blood–nerve barrier model, no selectivity optimisation.
7. Nothing here has been tested in a cell or an animal.

## Not medical advice

This is computational hypothesis generation. For painful diabetic neuropathy the
evidence-based first-line agents are duloxetine, pregabalin, gabapentin and
amitriptyline (OPTION-DM, *Lancet* 2022, found them comparably effective).
Alpha-lipoic acid has mixed evidence and is at best adjunctive. Several
phytochemicals in this library interact with prescription drugs. Anyone with
diabetic neuropathy needs their own clinician.

## Citing the data

- MolData: Keshavarzi Arshadi et al., *J Cheminform* 14, 10 (2022)
- Assay records: PubChem BioAssay AIDs listed in `data/panel_meta.json`
- BEDROC: Truchon & Bayly, *J Chem Inf Model* 47, 488 (2007)
- Conformal prediction: Vovk, Gammerman & Shafer, *Algorithmic Learning in a Random World* (2005)

MIT licence for the code. MolData is CC-BY-SA 3.0 via ChEMBL/PubChem.
