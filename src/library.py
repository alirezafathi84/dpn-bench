"""Curated screening library: agents used (or trialled) in painful diabetic
neuropathy, plus phytochemicals with a DPN evidence base, plus negative controls.

`class` field:
  guideline   - first-line / guideline-recommended for DPNP
  adjunct     - used or trialled in DPNP, not first line
  polyol      - aldose-reductase inhibitors (polyol pathway)
  herbal      - plant-derived / nutraceutical with DPN literature
  control     - should NOT score on these targets (negative controls)
"""

LIBRARY = [
    # ---------------- guideline first-line ----------------
    ("pregabalin",        "CC(C)C[C@H](CN)CC(O)=O", "guideline", "alpha2-delta ligand"),
    ("gabapentin",        "NCC1(CC(O)=O)CCCCC1", "guideline", "alpha2-delta ligand"),
    ("duloxetine",        "CNCC[C@@H](Oc1cccc2ccccc12)c1cccs1", "guideline", "SNRI"),
    ("amitriptyline",     "CN(C)CCC=C1c2ccccc2CCc2ccccc21", "guideline", "TCA"),
    ("nortriptyline",     "CNCCC=C1c2ccccc2CCc2ccccc21", "guideline", "TCA"),
    ("venlafaxine",       "CN(C)CC(c1ccc(OC)cc1)C1(O)CCCCC1", "guideline", "SNRI"),
    ("capsaicin",         "COc1cc(CNC(=O)CCCC/C=C/C(C)C)ccc1O", "guideline", "TRPV1 agonist (8% patch)"),
    # ---------------- adjunct / second line ----------------
    ("tramadol",          "CN(C)C[C@H]1CCCC[C@@]1(O)c1cccc(OC)c1", "adjunct", "opioid/SNRI"),
    ("tapentadol",        "CC[C@@H](Cc1cccc(O)c1)[C@@H](C)CN(C)C", "adjunct", "opioid/NRI"),
    ("carbamazepine",     "NC(=O)N1c2ccccc2C=Cc2ccccc21", "adjunct", "Na channel blocker"),
    ("oxcarbazepine",     "NC(=O)N1c2ccccc2CC(=O)c2ccccc21", "adjunct", "Na channel blocker"),
    ("lacosamide",        "COC[C@@H](NC(C)=O)C(=O)NCc1ccccc1", "adjunct", "slow Na inactivation"),
    ("lamotrigine",       "Nc1nnc(-c2cccc(Cl)c2Cl)c(N)n1", "adjunct", "Na channel blocker"),
    ("mexiletine",        "CC(N)COc1c(C)cccc1C", "adjunct", "Na channel blocker"),
    ("lidocaine",         "CCN(CC)CC(=O)Nc1c(C)cccc1C", "adjunct", "local anaesthetic"),
    ("topiramate",        "CC1(C)OC2COC3(COS(N)(=O)=O)OC(C)(C)OC3C2O1", "adjunct", "mixed"),
    ("clonidine",         "Clc1cccc(Cl)c1NC1=NCCN1", "adjunct", "alpha2 agonist"),
    ("flupirtine",        "CCOC(=O)Nc1ccc(NCc2ccc(F)cc2)nc1N", "adjunct", "Kv7/KCNQ opener"),
    ("retigabine",        "CCOC(=O)Nc1ccc(NCc2ccc(F)cc2)cc1N", "adjunct", "Kv7/KCNQ opener"),
    # ---------------- polyol pathway (aldose reductase) ----------------
    ("epalrestat",        "CC(=C/C=C/c1ccccc1)/C=C1\\SC(=S)N(CC(O)=O)C1=O", "polyol", "ARI (approved in Japan)"),
    ("zopolrestat",       "c1ccc2c(c1)c(nn(c2=O)Cc3nc4cc(ccc4s3)C(F)(F)F)CC(=O)O", "polyol", "ARI"),
    ("fidarestat",        "c1cc2c(cc1F)[C@@]3(C[C@H](O2)C(=O)N)C(=O)NC(=O)N3", "polyol", "ARI"),
    ("zenarestat",        "c1cc2c(cc1Cl)n(c(=O)n(c2=O)Cc3ccc(cc3F)Br)CC(=O)O", "polyol", "ARI"),
    ("alrestatin",        "c1cc2cccc3c2c(c1)C(=O)N(C3=O)CC(=O)O", "polyol", "ARI"),
    ("ranirestat",        "c1cc2n(c1)[C@@]3(CC(=NC3=O)O)C(=O)N(C2=O)Cc4ccc(cc4F)Br", "polyol", "ARI"),
    # ---------------- antioxidant / metabolic adjuncts ----------------
    ("alpha_lipoic_acid", "OC(=O)CCCC[C@@H]1CCSS1", "herbal", "antioxidant, Nrf2"),
    ("acetyl_L_carnitine", "C[N+](C)(C)C[C@@H](OC(C)=O)CC([O-])=O", "herbal", "mitochondrial"),
    ("benfotiamine",      "CCOP(=O)(O)OCCC(=C(N)/C=N(/C)c1cnc(C)nc1N)C=O", "herbal", "thiamine prodrug"),
    ("methylcobalamin_frag", "CC1=CC2=NC1=CC1=C(C)C(CCC(N)=O)=C(N1)C=C1N=C(C=C3N=C2C(C)(CC(N)=O)[C@@H]3CCC(N)=O)[C@@](C)(CC(N)=O)[C@@H]1CCC(N)=O", "herbal", "B12 corrin core"),
    # ---------------- phytochemicals with DPN literature ----------------
    ("curcumin",          "COc1cc(/C=C/C(=O)CC(=O)/C=C/c2ccc(O)c(OC)c2)ccc1O", "herbal", "Nrf2/NF-kB"),
    ("resveratrol",       "Oc1ccc(/C=C/c2cc(O)cc(O)c2)cc1", "herbal", "SIRT1/Nrf2"),
    ("sulforaphane",      "CS(=O)CCCCN=C=S", "herbal", "canonical Nrf2 activator"),
    ("quercetin",         "O=c1c(O)c(-c2ccc(O)c(O)c2)oc2cc(O)cc(O)c12", "herbal", "flavonol, ARI"),
    ("luteolin",          "O=c1cc(-c2ccc(O)c(O)c2)oc2cc(O)cc(O)c12", "herbal", "flavone, ARI"),
    ("apigenin",          "O=c1cc(-c2ccc(O)cc2)oc2cc(O)cc(O)c12", "herbal", "flavone"),
    ("genistein",         "O=c1c(-c2ccc(O)cc2)coc2cc(O)cc(O)c12", "herbal", "isoflavone"),
    ("naringenin",        "O=C1C[C@H](c2ccc(O)cc2)Oc2cc(O)cc(O)c21", "herbal", "flavanone"),
    ("baicalein",         "O=c1cc(-c2ccccc2)oc2cc(O)c(O)c(O)c12", "herbal", "flavone"),
    ("EGCG",              "O[C@@H]1Cc2c(O)cc(O)cc2O[C@@H]1c1cc(O)c(O)c(O)c1", "herbal", "catechin core"),
    ("berberine",         "COc1ccc2cc3[n+](cc2c1OC)CCc1cc2c(cc1-3)OCO2", "herbal", "alkaloid"),
    ("cinnamaldehyde",    "O=C/C=C/c1ccccc1", "herbal", "TRPA1 agonist"),
    ("6_gingerol",        "CCCCC[C@@H](O)CC(=O)CCc1ccc(O)c(OC)c1", "herbal", "TRPV1 ligand"),
    ("piperine",          "O=C(/C=C/C=C/c1ccc2c(c1)OCO2)N1CCCCC1", "herbal", "TRPV1 agonist"),
    ("thymoquinone",      "CC(C)C1=CC(=O)C(C)=CC1=O", "herbal", "quinone, Nrf2"),
    ("silibinin",         "COc1cc([C@@H]2Oc3cc([C@@H]4Oc5cc(O)cc(O)c5C(=O)[C@@H]4O)ccc3O[C@@H]2CO)ccc1O", "herbal", "flavonolignan"),
    ("mangiferin",        "O[C@@H]1[C@@H](O)[C@H](O)[C@@H](CO)O[C@H]1c1c(O)cc(O)c2c1oc1cc(O)c(O)cc1c2=O", "herbal", "xanthone"),
    ("trigonelline",      "C[n+]1cccc(C([O-])=O)c1", "herbal", "fenugreek alkaloid"),
    ("ursolic_acid",      "C[C@@H]1CC[C@@]2(CC[C@]3(C)C(=CC[C@@H]4[C@@]5(C)CC[C@H](O)C(C)(C)[C@@H]5CC[C@@]34C)[C@@H]2[C@H]1C)C(O)=O", "herbal", "triterpene"),
    ("oleanolic_acid",    "CC1(C)CC[C@]2(CC[C@]3(C)C(=CC[C@@H]4[C@@]5(C)CC[C@H](O)C(C)(C)[C@@H]5CC[C@@]34C)[C@@H]2C1)C(O)=O", "herbal", "triterpene"),
    ("crocetin",          "C/C(=C\\C=C\\C(C)=C\\C=C\\C=C(C)\\C=C\\C=C(C)\\C(O)=O)/C(O)=O", "herbal", "saffron apocarotenoid"),
    ("salidroside",       "OC[C@H]1O[C@@H](OCCc2ccc(O)cc2)[C@H](O)[C@@H](O)[C@@H]1O", "herbal", "rhodiola glycoside"),
    ("tanshinone_IIA",    "Cc1coc2c1C(=O)C(=O)c1c-2ccc2c1CCCC2(C)C", "herbal", "diterpene quinone"),
    ("alpha_tocopherol",  "Cc1c(C)c2c(c(C)c1O)CC[C@@](C)(CCC[C@H](C)CCC[C@H](C)CCCC(C)C)O2", "herbal", "vitamin E"),
    ("ferulic_acid",      "COc1cc(/C=C/C(O)=O)ccc1O", "herbal", "phenolic acid"),
    ("rosmarinic_acid",   "O=C(/C=C/c1ccc(O)c(O)c1)O[C@@H](Cc1ccc(O)c(O)c1)C(O)=O", "herbal", "phenolic acid"),
    # ---------------- negative controls ----------------
    ("glucose",           "OC[C@H]1OC(O)[C@H](O)[C@@H](O)[C@@H]1O", "control", "sugar"),
    ("urea",              "NC(N)=O", "control", "tiny polar"),
    ("caffeine",          "Cn1c(=O)c2c(ncn2C)n(C)c1=O", "control", "unrelated xanthine"),
    ("penicillin_G",      "CC1(C)S[C@@H]2[C@H](NC(=O)Cc3ccccc3)C(=O)N2[C@H]1C(O)=O", "control", "antibiotic"),
    ("sucrose",           "OC[C@H]1O[C@@](CO)(O[C@H]2O[C@H](CO)[C@@H](O)[C@H](O)[C@H]2O)[C@@H](O)[C@@H]1O", "control", "disaccharide"),
]
