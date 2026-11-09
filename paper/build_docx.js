// Builds the IEEE-format Word manuscript.
// IEEE conference template: US Letter, two columns, Times New Roman 10pt body.
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, AlignmentType, SectionType,
  Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle,
  HeadingLevel, convertInchesToTwip, PageNumber, Footer,
} = require("docx");

const FONT = "Times New Roman";
const COLW = 5040;                 // 3.5in column => DXA

// ---------- helpers -------------------------------------------------------
const body = (text, opts = {}) =>
  new Paragraph({
    alignment: AlignmentType.JUSTIFIED,
    spacing: { after: opts.after ?? 0, line: 230 },
    indent: { firstLine: opts.noIndent ? 0 : convertInchesToTwip(0.2) },
    children: [new TextRun({ text, font: FONT, size: 20 })],
  });

let secN = 0;
const ROMAN = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"];
const section = (title) => {
  secN += 1;
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 200, after: 100 },
    keepNext: true,
    children: [new TextRun({ text: `${ROMAN[secN]}.  ${title}`, font: FONT, size: 20, allCaps: false, smallCaps: true })],
  });
};
let subN = 0, lastSec = 0;
const sub = (title) => {
  if (lastSec !== secN) { subN = 0; lastSec = secN; }
  subN += 1;
  const letter = String.fromCharCode(64 + subN);
  return new Paragraph({
    spacing: { before: 120, after: 60 },
    keepNext: true,
    children: [new TextRun({ text: `${letter}.  ${title}`, font: FONT, size: 20, italics: true })],
  });
};
const cell = (text, { bold = false, shade = false, align = AlignmentType.LEFT, w = 1000 } = {}) =>
  new TableCell({
    width: { size: w, type: WidthType.DXA },
    shading: shade ? { type: ShadingType.CLEAR, fill: "E8E8E8", color: "auto" } : undefined,
    margins: { top: 40, bottom: 40, left: 60, right: 60 },
    children: [new Paragraph({
      alignment: align,
      spacing: { after: 0 },
      children: [new TextRun({ text, font: FONT, size: 16, bold })],
    })],
  });
const caption = (text) => new Paragraph({
  alignment: AlignmentType.CENTER,
  spacing: { before: 80, after: 120 },
  children: [new TextRun({ text, font: FONT, size: 16 })],
});
const tableCap = (text) => new Paragraph({
  alignment: AlignmentType.CENTER,
  spacing: { before: 140, after: 60 },
  keepNext: true,
  children: [new TextRun({ text, font: FONT, size: 16, smallCaps: true })],
});
const makeTable = (widths, rows) => new Table({
  columnWidths: widths,
  width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA },
  rows,
});

// ---------- front matter --------------------------------------------------
const title = new Paragraph({
  alignment: AlignmentType.CENTER,
  spacing: { after: 160 },
  children: [new TextRun({
    text: "Evidence-Based Treatment of Painful Diabetic Peripheral Neuropathy: A Graded Synthesis and a Mechanism-Anchored Machine-Learning Audit",
    font: FONT, size: 44,
  })],
});
const authors = [
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 0 },
    children: [new TextRun({ text: "[Author Name]", font: FONT, size: 22 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 0 },
    children: [new TextRun({ text: "[Department, Institution]", font: FONT, size: 20, italics: true })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 240 },
    children: [new TextRun({ text: "[City, Country]  ·  [email@institution.edu]", font: FONT, size: 20 })] }),
];

const abstract = new Paragraph({
  alignment: AlignmentType.JUSTIFIED,
  spacing: { after: 120 },
  children: [
    new TextRun({ text: "Abstract—", font: FONT, size: 18, bold: true, italics: true }),
    new TextRun({
      text: "Painful diabetic peripheral neuropathy (PDPN) affects up to a quarter of people with diabetes, and the four guideline-recommended oral drug classes relieve pain adequately in only about 40 % of patients. This paper has two parts. First, we synthesise the current treatment evidence by level of support: optimised glycaemic management prevents neuropathy in type 1 diabetes (ADA grade A) but only modestly slows it in type 2 (grade C) and reverses neither; the 2022 American Academy of Neurology guideline endorses four oral classes with broadly comparable effect sizes and recommends against opioids, tramadol and tapentadol; the OPTION-DM crossover trial found amitriptyline, duloxetine and pregabalin equivalent, with combination therapy benefiting monotherapy non-responders; and for refractory disease, 10 kHz spinal cord stimulation produced a 79.9 % mean pain reduction at 24 months with 90.1 % of participants achieving at least 50 % relief in the SENZA-PDN randomised trial — the largest effect size in the modern PDPN literature. Second, because candidate generation for new mechanisms is now routinely computational, we build and audit a machine-learning pipeline over a mechanism-anchored panel of 15 high-throughput endpoints spanning the analgesic ion-channel and neuroprotective arms of PDPN (415,085 molecules, 104,706 Bemis–Murcko scaffolds, scaffold split with 1.85 % leakage). A multi-task network attains a mean ROC-AUC of 0.824, BEDROC of 0.260 and 1 % enrichment of 22.0, exceeding LightGBM, logistic regression and a Tanimoto similarity-search control. Critically, an interference audit overturns the naive ranking: 11 of 59 screened compounds carry PAINS alerts and three are memorised training actives, while the model systematically misses the covalent Nrf2 activators (α-lipoic acid, sulforaphane) with the strongest nutraceutical rationale. We conclude that computational screening is a hypothesis generator subordinate to the graded clinical evidence, and release the full pipeline and audit tooling.",
      font: FONT, size: 18, bold: true, italics: true,
    }),
  ],
});
const keywords = new Paragraph({
  alignment: AlignmentType.JUSTIFIED,
  spacing: { after: 160 },
  children: [
    new TextRun({ text: "Keywords—", font: FONT, size: 18, bold: true, italics: true }),
    new TextRun({ text: "diabetic neuropathy, neuropathic pain, evidence-based medicine, spinal cord stimulation, duloxetine, pregabalin, virtual screening, multi-task learning, PAINS", font: FONT, size: 18, italics: true }),
  ],
});

// ---------- content -------------------------------------------------------
const content = [];
const P = (...xs) => content.push(...xs);

P(section("Introduction"));
P(body("Diabetic peripheral neuropathy occurs in up to half of people with diabetes mellitus and is the dominant risk factor for foot ulceration and lower-limb amputation. Between a fifth and a quarter of those affected develop chronic neuropathic pain. The therapeutic problem is not an absence of options but an absence of good ones: the drugs in routine use are symptomatic, none restores nerve function, and standard doses of the two agents holding a regulatory indication relieve pain meaningfully in roughly 40 % of patients.", { noIndent: true }));
P(body("This paper separates two questions that are frequently conflated in the computational literature. The first — what is the best treatment today — is answered by graded clinical evidence, and we synthesise it in Sections III to VII. The second — how should new mechanisms be prioritised — is where machine learning contributes, and we address it in Section IX with a benchmark built specifically around PDPN target biology. Our central methodological claim is that the second must be reported subordinate to the first, and must be audited for the artefacts that dominate high-throughput screening data.", { after: 60 }));

P(section("Methods"));
P(body("Clinical evidence was drawn from the 2022 American Academy of Neurology (AAN) practice guideline update on oral and topical treatment of painful diabetic polyneuropathy, the American Diabetes Association (ADA) Standards of Care in Diabetes—2026 (Section 12), the Cochrane review of enhanced glucose control, and the primary randomised trials cited in Section XI. Where a guideline assigns an evidence grade we report it verbatim rather than restating it as a recommendation of our own. Computational methods are described in Section IX and in full in the released repository.", { noIndent: true, after: 60 }));

P(section("Disease-Modifying and Preventive Therapy"));
P(body("Glycaemic management is the only intervention convincingly shown to alter the natural history of the neuropathy itself, and its effect differs sharply by diabetes type. The ADA Standards of Care—2026 state that optimal glycaemic management can effectively prevent distal polyneuropathy and cardiovascular autonomic neuropathy in type 1 diabetes and may modestly slow progression in type 2, but does not reverse neuronal loss. The accompanying recommendation carries grade A for type 1 and grade C for type 2, with a grade B recommendation to optimise weight, blood pressure and lipids.", { noIndent: true }));
P(body("The quantitative basis is the DCCT, in which intensive therapy reduced new confirmed neuropathy from 13 % to 5 % over five years in type 1 diabetes, and the Cochrane review of 17 randomised studies, which found enhanced glucose control significantly prevents clinical neuropathy in type 1 diabetes on high-quality evidence, while the corresponding reduction in type 2 diabetes did not reach significance (P = 0.06). Exercise has moderate-level evidence for prevention and symptom improvement, though the ADA notes the overall certainty remains low. Importantly, the ADA finds no compelling evidence that glycaemic or lifestyle management treats established neuropathic pain — prevention and analgesia are separate indications."));
P(body("Clinically this means the disease-modifying and the analgesic arms must run in parallel. Treating pain without addressing glycaemia forfeits the only available opportunity to slow the underlying process, and optimising glycaemia without treating pain leaves the patient's presenting complaint untouched.", { after: 60 }));

P(section("First-Line Pharmacotherapy"));
P(body("The 2022 AAN guideline identifies four oral classes with meta-analytic evidence of pain reduction: tricyclic antidepressants (amitriptyline, nortriptyline, imipramine), serotonin–noradrenaline reuptake inhibitors (duloxetine, venlafaxine, desvenlafaxine), gabapentinoids (gabapentin, pregabalin), and sodium-channel blockers (including carbamazepine and related agents). Only pregabalin and duloxetine hold FDA approval for this indication. The guideline is explicit that these agents reduce rather than eliminate pain, and that mood and sleep disorders should be assessed before initiating therapy because their treatment is itself important.", { noIndent: true }));
P(body("The strongest comparative evidence is the OPTION-DM trial, the largest and longest head-to-head crossover study in neuropathic pain, which randomised patients to six ordered sequences of three pathways: amitriptyline supplemented with pregabalin, pregabalin supplemented with amitriptyline, and duloxetine supplemented with pregabalin, each lasting 16 weeks. The three monotherapies were similarly efficacious, as were the three combinations, and combination therapy provided significant additional relief to patients with an inadequate response to maximum-tolerated monotherapy. Mean maximum tolerated doses were 56 mg amitriptyline, 76 mg duloxetine and 397 mg pregabalin per day."));
P(body("The practical consequence is that initial agent selection should be driven by comorbidity, tolerability and cost rather than by expected efficacy, since the classes do not separate. Duloxetine suits coexisting depression but has been associated with increased HbA1c relative to placebo in meta-analysis; gabapentinoids suit coexisting anxiety or insomnia but carry sedation, oedema and misuse liability; tricyclics are inexpensive but anticholinergic and require caution in older adults and cardiac disease."));
P(tableCap("Table I.  Guideline-Endorsed Oral Classes for PDPN"));
P(makeTable([1500, 1500, 2040], [
  new TableRow({ tableHeader: true, children: [
    cell("Class", { bold: true, shade: true, w: 1500 }),
    cell("Representative agents", { bold: true, shade: true, w: 1500 }),
    cell("Principal cautions", { bold: true, shade: true, w: 2040 }),
  ] }),
  new TableRow({ children: [
    cell("SNRI", { w: 1500 }), cell("Duloxetine*, venlafaxine", { w: 1500 }),
    cell("Nausea; possible HbA1c rise", { w: 2040 }) ] }),
  new TableRow({ children: [
    cell("Gabapentinoid", { w: 1500 }), cell("Pregabalin*, gabapentin", { w: 1500 }),
    cell("Sedation, oedema, misuse", { w: 2040 }) ] }),
  new TableRow({ children: [
    cell("TCA", { w: 1500 }), cell("Amitriptyline, nortriptyline", { w: 1500 }),
    cell("Anticholinergic; cardiac risk", { w: 2040 }) ] }),
  new TableRow({ children: [
    cell("Na-channel blocker", { w: 1500 }), cell("Carbamazepine, lacosamide", { w: 1500 }),
    cell("Interactions; monitoring", { w: 2040 }) ] }),
  new TableRow({ children: [
    cell("Not recommended", { w: 1500 }), cell("Opioids, tramadol, tapentadol", { w: 1500 }),
    cell("AAN 2022: risks exceed benefits", { w: 2040 }) ] }),
]));
P(caption("*FDA-approved for PDPN. Effect sizes across the four endorsed classes do not meaningfully separate (AAN 2022; OPTION-DM)."));

P(section("Topical and Non-Traditional Options"));
P(body("For patients who prefer topical or non-pharmacological approaches, the AAN guideline states that clinicians may offer capsaicin, glyceryl trinitrate spray or Citrullus colocynthis, and that Ginkgo biloba, exercise, mindfulness, cognitive behavioural therapy and tai chi may also help, while noting these are supported by fewer studies. The capsaicin 8 % patch is of particular interest because its mechanism is explicit: it activates and then defunctionalises TRPV1 on nociceptive nerve endings, depleting substance P and providing localised relief for up to 12 weeks from a single application. It is the only approved PDPN therapy acting on a target we were able to model directly in Section IX.", { noIndent: true, after: 60 }));

P(section("Interventional Therapy for Refractory Pain"));
P(body("The most consequential advance of the past five years is high-frequency spinal cord stimulation. SENZA-PDN was a prospective, multicentre, randomised controlled trial that allocated 216 patients with refractory PDPN to conventional medical management alone or 10 kHz spinal cord stimulation plus conventional management, with crossover permitted after six months. At 24 months, 10 kHz stimulation reduced pain by a mean of 79.9 % from baseline, 90.1 % of participants achieved at least 50 % pain relief, and 65.7 % demonstrated clinically meaningful neurological improvement; health-related quality of life and sleep improved significantly. A separate analysis reported pain severity reduced by 66.9 % and pain interference with mood and daily activity by 65.8 % on the BPI-DPN.", { noIndent: true }));
P(body("Three features of this result deserve emphasis. First, the effect size is of a different order from any oral agent: 24-month responder rates of about 90 % compare with roughly 41 % for conventional low-frequency stimulation. Second, HbA1c did not change significantly over follow-up, so the benefit is not attributable to improved glycaemic control, and the consistency of effect across 24 months argues against a large placebo component. Third, it is invasive and not without harm — five systems (3.2 %) were explanted for infection. The therapy is therefore appropriately positioned after failure of adequately dosed oral therapy rather than as an early option."));

P(section("Emerging Pharmacology"));
P(body("Three developments are worth tracking. Suzetrigine, a selective Nav1.8 inhibitor with reported selectivity exceeding 31,000-fold over other Nav subtypes, is the first genuinely new analgesic mechanism approved in decades; it holds FDA approval for moderate-to-severe acute pain and achieved positive phase 2 proof-of-concept in painful diabetic neuropathy, with phase 3 trials ongoing and completion estimated for 2027. It is not approved for neuropathy, and its acute-pain trials showed non-inferiority rather than superiority to hydrocodone/acetaminophen. Second, next-generation α2δ ligands with improved subunit selectivity — mirogabalin, approved in Japan, and crisugabalin, approved in China — are reported in a 2025 network meta-analysis of 34 trials and 8,630 patients to reduce average daily pain scores by 0.29 points more than pregabalin 300 mg. Third, LX9211, an adaptor-associated kinase 1 inhibitor, remains in early development.", { noIndent: true, after: 60 }));

P(section("Nutraceutical and Herbal Evidence"));
P(body("α-lipoic acid is the only nutraceutical with evidence approaching clinical relevance, and that evidence is genuinely divided. A 2025 updated systematic review and meta-analysis reported that oral α-lipoic acid at 600–1,800 mg/day improved HbA1c, Neuropathy Impairment Score, Total Symptom Score and Neuropathy Disability Score, with HbA1c, TSS and NDS supported by high-quality GRADE evidence. A 2026 critical review reached a more restrained conclusion: symptoms improve consistently in the short term, but the long-term NATHAN 1 trial was only borderline on its primary composite endpoint (P = 0.05) with no significant nerve-conduction improvement, so the evidence supports adjunctive short-term symptomatic relief rather than functional stabilisation or nerve repair. At least one meta-analysis found no significant benefit over placebo across functional scales.", { noIndent: true }));
P(body("Other phytochemicals — curcumin, resveratrol, benfotiamine, acetyl-L-carnitine — have thinner and more heterogeneous support. Several interact with prescription therapy, and the combination of serotonergic herbals with an SNRI is a specific hazard. We therefore treat the nutraceutical literature as a source of mechanistic hypotheses rather than of treatment recommendations, which is precisely the role in which it enters Section IX.", { after: 60 }));

P(section("Computational Candidate Generation and Its Audit"));
P(sub("A mechanism-anchored benchmark"));
P(body("Existing molecular machine-learning benchmarks are organised by data availability rather than by disease mechanism, so good aggregate performance does not establish usefulness for a given indication. We therefore assembled DPN-Bench: 15 PubChem high-throughput endpoints selected for mechanistic linkage to PDPN. The analgesic arm covers TRPV1 agonism (the capsaicin-patch mechanism of Section VI), KCNQ2/Kv7.2 potentiation (the retigabine and flupirtine class) and two-pore potassium channel activation. Pro-excitatory directions — KCNQ2 and K2P block — are retained deliberately as selectivity counter-screens. The neuroprotective arm covers Nrf2/ARE activation, CHOP inhibition, both arms of the unfolded protein response, STEP phosphatase and β-cell protection, reflecting the oxidative- and endoplasmic-reticulum-stress axes that dominate neuropathy pathogenesis and that constitute the shared mechanism of α-lipoic acid, curcumin and sulforaphane.", { noIndent: true }));
P(body("After curation — desalting, isotope stripping, sanitisation, a 6–70 heavy-atom window and canonical-SMILES deduplication — the benchmark holds 415,085 molecules over 104,706 Bemis–Murcko scaffolds at positive rates of 0.01–3.8 %. We adopt the source scaffold split and measure rather than assume its difficulty: 1.85 % of test scaffolds also appear in training."));
P(sub("Models and results"));
P(body("A multi-task feed-forward network (1038→512→128, 18 masked sigmoid heads, positive-weighted cross-entropy, plain NumPy) was compared against per-task LightGBM, ℓ2 logistic regression, and a Tanimoto k-nearest-neighbour similarity-search control. The last is essential: a model that cannot outperform retrieval of the most similar known active has learned nothing beyond lookup. Because prevalence is below 1 %, we report BEDROC (α = 80.5) and enrichment factors as primary and ROC-AUC only for comparability.", { noIndent: true }));
P(tableCap("Table II.  Held-Out Test Performance, Mean Over 15 Tasks"));
P(makeTable([1740, 1100, 1100, 1100], [
  new TableRow({ tableHeader: true, children: [
    cell("Model", { bold: true, shade: true, w: 1740 }),
    cell("ROC-AUC", { bold: true, shade: true, align: AlignmentType.CENTER, w: 1100 }),
    cell("BEDROC", { bold: true, shade: true, align: AlignmentType.CENTER, w: 1100 }),
    cell("EF 1 %", { bold: true, shade: true, align: AlignmentType.CENTER, w: 1100 }),
  ] }),
  new TableRow({ children: [
    cell("Tanimoto k-NN", { w: 1740 }), cell("0.663", { align: AlignmentType.CENTER, w: 1100 }),
    cell("0.174", { align: AlignmentType.CENTER, w: 1100 }), cell("14.4", { align: AlignmentType.CENTER, w: 1100 }) ] }),
  new TableRow({ children: [
    cell("Logistic regression", { w: 1740 }), cell("0.771", { align: AlignmentType.CENTER, w: 1100 }),
    cell("0.144", { align: AlignmentType.CENTER, w: 1100 }), cell("11.6", { align: AlignmentType.CENTER, w: 1100 }) ] }),
  new TableRow({ children: [
    cell("LightGBM", { w: 1740 }), cell("0.788", { align: AlignmentType.CENTER, w: 1100 }),
    cell("0.232", { align: AlignmentType.CENTER, w: 1100 }), cell("18.8", { align: AlignmentType.CENTER, w: 1100 }) ] }),
  new TableRow({ children: [
    cell("Multi-task network", { bold: true, w: 1740 }), cell("0.824", { bold: true, align: AlignmentType.CENTER, w: 1100 }),
    cell("0.260", { bold: true, align: AlignmentType.CENTER, w: 1100 }), cell("22.0", { bold: true, align: AlignmentType.CENTER, w: 1100 }) ] }),
]));
P(caption("The multi-task network wins 9 of 15 tasks on BEDROC against LightGBM's 6. Similarity search outperforms the linear model on early recognition despite much worse ROC-AUC."));
P(body("Two findings generalise beyond this panel. Similarity search beats the linear model on early recognition (BEDROC 0.174 against 0.144) while losing decisively on ROC-AUC, confirming that global discrimination and screening utility diverge at low prevalence. And performance is strongly endpoint-dependent: the two-pore potassium activator task remains near chance (ROC-AUC 0.568), consistent with cell-based phenotypic read-outs resisting fingerprint-based modelling."));
P(sub("The audit changes the answer"));
P(body("We then scored 59 compounds — guideline agents, aldose-reductase inhibitors, phytochemicals with neuropathy literature, and negative controls — reporting with every score a conformal p-value against validation actives and the maximum Tanimoto to any training active. Negative controls behaved: sucrose reached the 0.4th percentile on KCNQ2 potentiation and glucose the 1.1st on TRPV1 agonism. Retigabine (85.6th percentile) and flupirtine (63.6th) were recovered as Kv7 openers by genuine extrapolation, and cinnamaldehyde topped the Nrf2 task, consistent with its known Michael-acceptor chemistry.", { noIndent: true }));
P(body("In the unaudited ranking, however, quercetin, luteolin, mangiferin, epigallocatechin gallate, ursolic and oleanolic acid and α-tocopherol occupied the top positions of nearly every endpoint. This is not polypharmacology but the classic high-throughput-screening frequent-hitter artefact: 11 of the 59 compounds carry PAINS substructure alerts, predominantly catechols; three are memorised training actives, so capsaicin's 99.7th percentile on TRPV1 reflects lookup (maximum Tanimoto 1.00) rather than prediction; and α-tocopherol entered the top 5 % of seven mechanistically unrelated tasks. Removing memorised, alert-bearing and promiscuous compounds yields a materially different and far more sober ranking."));
P(body("The most instructive result is a failure. Sulforaphane (32.3rd percentile) and α-lipoic acid (28.0th) — the two nutraceuticals with the strongest neuropathy rationale — were missed. Both are small electrophiles that activate Nrf2 by covalently modifying KEAP1 cysteines, and both lie far outside the applicability domain (maximum Tanimoto 0.14–0.18). A topological-fingerprint classifier trained on a reporter-gene assay has no representational capacity for covalent reactivity. Urea, a negative control, reached the 65th percentile on the same endpoint. These are limits of the molecular representation, not of training, and they bound what this class of method can contribute."));

P(section("A Practical Treatment Sequence"));
P(body("Synthesising the graded evidence yields the following sequence, in which each step is justified by the sources cited in the corresponding section above.", { noIndent: true }));
P(tableCap("Table III.  Treatment Sequence by Strength of Evidence"));
P(makeTable([700, 2140, 2200], [
  new TableRow({ tableHeader: true, children: [
    cell("Step", { bold: true, shade: true, w: 700 }),
    cell("Intervention", { bold: true, shade: true, w: 2140 }),
    cell("Basis", { bold: true, shade: true, w: 2200 }),
  ] }),
  new TableRow({ children: [
    cell("0", { w: 700 }), cell("Confirm diagnosis; exclude non-diabetic causes; screen mood and sleep", { w: 2140 }),
    cell("AAN 2022 (Level B assessment)", { w: 2200 }) ] }),
  new TableRow({ children: [
    cell("1", { w: 700 }), cell("Optimise glucose, weight, blood pressure, lipids; foot care; structured exercise", { w: 2140 }),
    cell("ADA 2026: grade A (T1D), C (T2D), B (metabolic); Cochrane", { w: 2200 }) ] }),
  new TableRow({ children: [
    cell("2", { w: 700 }), cell("One of four oral classes, chosen by comorbidity and tolerability; titrate to maximum tolerated dose", { w: 2140 }),
    cell("AAN 2022; OPTION-DM (classes equivalent)", { w: 2200 }) ] }),
  new TableRow({ children: [
    cell("3", { w: 700 }), cell("Switch class, or add a second agent from a different class", { w: 2140 }),
    cell("OPTION-DM (combination helps non-responders)", { w: 2200 }) ] }),
  new TableRow({ children: [
    cell("4", { w: 700 }), cell("Add capsaicin 8 % patch or other topical agent", { w: 2140 }),
    cell("AAN 2022 (may offer)", { w: 2200 }) ] }),
  new TableRow({ children: [
    cell("5", { w: 700 }), cell("Refer for 10 kHz spinal cord stimulation if refractory", { w: 2140 }),
    cell("SENZA-PDN RCT, 24-month data", { w: 2200 }) ] }),
  new TableRow({ children: [
    cell("—", { w: 700 }), cell("Avoid opioids, tramadol and tapentadol", { w: 2140 }),
    cell("AAN 2022 (risks exceed benefits)", { w: 2200 }) ] }),
]));
P(body("α-lipoic acid may be discussed as a short-term adjunct with the patient informed that long-term functional benefit is unproven. Nutraceuticals should not displace step 2.", { after: 60 }));

P(section("Limitations"));
P(body("The clinical synthesis is a narrative review and not a de novo meta-analysis; effect estimates are reported as the cited sources state them. Guideline grades differ in methodology between the AAN and ADA and are not interchangeable. SENZA-PDN was open-label, which blinding is impossible to achieve for an implanted device, so expectation effects cannot be fully excluded despite the durability argument. On the computational side, labels are single-concentration primary screens without dose–response confirmation; pathway endpoints are reporter read-outs, so an active need not be a direct binder; representations are two-dimensional, with no conformers, docking or structure; covalent and redox mechanisms are systematically missed; and no ADMET, blood–nerve-barrier or selectivity modelling was performed. Nothing reported in Section IX has been tested in a cell or an animal.", { noIndent: true, after: 60 }));

P(section("Conclusion"));
P(body("For painful diabetic peripheral neuropathy today, the best-supported treatment is a parallel strategy: optimise glycaemic and cardiometabolic management for the disease, and titrate one of four equivalent oral classes for the pain, escalating to combination therapy and then, in refractory cases, to 10 kHz spinal cord stimulation, which carries the largest randomised effect size in the field. Opioids should be avoided. Against that baseline, computational screening earns a narrow but real role in prioritising new mechanisms — provided it is audited. Without the interference audit reported here, our own screen would have nominated a list of PAINS-flagged polyphenols as novel candidates, which is approximately what much of the phytochemical virtual-screening literature does report. We release the pipeline, trained weights and audit tooling so the audit can be applied to other screens.", { noIndent: true, after: 60 }));

// ---------- references ----------------------------------------------------
const refs = [
  "R. Price et al., “Oral and topical treatment of painful diabetic polyneuropathy: practice guideline update summary: report of the AAN Guideline Subcommittee,” Neurology, vol. 98, no. 1, pp. 31–43, Jan. 2022.",
  "American Diabetes Association Professional Practice Committee, “12. Retinopathy, neuropathy, and foot care: Standards of Care in Diabetes—2026,” Diabetes Care, vol. 49, suppl. 1, 2026.",
  "S. Tesfaye et al., “Comparison of amitriptyline supplemented with pregabalin, pregabalin supplemented with amitriptyline, and duloxetine supplemented with pregabalin for the treatment of diabetic peripheral neuropathic pain (OPTION-DM): a multicentre, double-blind, randomised crossover trial,” The Lancet, vol. 400, no. 10353, pp. 680–690, 2022.",
  "E. A. Petersen et al., “Long-term efficacy of high-frequency (10 kHz) spinal cord stimulation for the treatment of painful diabetic neuropathy: 24-month results of a randomized controlled trial,” Diabetes Res. Clin. Pract., vol. 203, 110865, 2023.",
  "E. A. Petersen et al., “Effect of high-frequency (10-kHz) spinal cord stimulation in patients with painful diabetic neuropathy: a randomized clinical trial,” JAMA Neurol., vol. 78, no. 6, pp. 687–698, 2021.",
  "E. A. Petersen et al., “High-frequency 10-kHz spinal cord stimulation provides long-term (24-month) improvements in diabetes-related pain and quality of life for patients with painful diabetic neuropathy,” J. Diabetes Sci. Technol., 2024.",
  "D. Callaghan et al. / Cochrane, “Enhanced glucose control for preventing and treating diabetic neuropathy,” Cochrane Database Syst. Rev., no. 11, CD007543, 2021.",
  "Diabetes Control and Complications Trial Research Group, “The effect of intensive diabetes therapy on the development and progression of neuropathy,” Ann. Intern. Med., vol. 122, no. 8, pp. 561–568, 1995.",
  "Vertex Pharmaceuticals, “A phase 3, randomized, double-blind, placebo- and active-controlled study of the efficacy and safety of suzetrigine in subjects with pain associated with diabetic peripheral neuropathy,” ClinicalTrials.gov NCT06628908.",
  "“Suzetrigine, a selective pain signal inhibitor of NaV1.8, shows proof-of-concept for treatment of painful diabetic peripheral neuropathy,” Neurology, vol. 104, suppl. 1, S11.002, 2025.",
  "“Therapeutic targets, pharmacological mechanisms, and delivery strategies for diabetic peripheral neuropathy,” Drug Des. Devel. Ther., 2026.",
  "“Alpha lipoic acid: advancing insights in diabetic neuropathy through updated systematic review and meta-analysis,” Explor. Neuroprot. Ther., 2025.",
  "“Alpha-lipoic acid and benfotiamine in diabetic peripheral neuropathy: a critical review of mechanistic rationale and clinical evidence within a nutritional therapeutic framework,” Nutrients, vol. 18, no. 10, 1538, 2026.",
  "A. Keshavarzi Arshadi et al., “MolData: a molecular benchmark for disease and target based machine learning,” J. Cheminformatics, vol. 14, art. 10, 2022.",
  "J.-F. Truchon and C. I. Bayly, “Evaluating virtual screening methods: good and bad metrics for the early recognition problem,” J. Chem. Inf. Model., vol. 47, no. 2, pp. 488–508, 2007.",
  "J. B. Baell and G. A. Holloway, “New substructure filters for removal of pan assay interference compounds (PAINS) from screening libraries,” J. Med. Chem., vol. 53, no. 7, pp. 2719–2740, 2010.",
  "K. Huang, P. Chandak et al., “A foundation model for clinician-centered drug repurposing,” Nature Medicine, vol. 30, 2024.",
  "S. Wan, X. Zhang, X. Xue, P. V. Coveney et al., “On the reliability of AI methods in drug discovery: evaluation of Boltz-2 for structure and binding affinity prediction,” arXiv:2603.05532, 2026.",
  "V. Vovk, A. Gammerman and G. Shafer, Algorithmic Learning in a Random World. New York: Springer, 2005.",
  "G. Landrum et al., “RDKit: open-source cheminformatics.” [Online]. Available: https://www.rdkit.org",
];
P(new Paragraph({
  alignment: AlignmentType.CENTER,
  spacing: { before: 200, after: 100 },
  keepNext: true,
  children: [new TextRun({ text: "References", font: FONT, size: 20, smallCaps: true })],
}));
refs.forEach((r, i) => P(new Paragraph({
  alignment: AlignmentType.JUSTIFIED,
  spacing: { after: 40 },
  indent: { left: convertInchesToTwip(0.25), hanging: convertInchesToTwip(0.25) },
  children: [new TextRun({ text: `[${i + 1}]\t${r}`, font: FONT, size: 16 })],
})));

// ---------- assemble ------------------------------------------------------
const pageCfg = {
  size: { width: 12240, height: 15840 },     // US Letter
  margin: { top: 1080, bottom: 1440, left: 900, right: 900 },
};

const doc = new Document({
  styles: {
    default: {
      document: { run: { font: FONT, size: 20 } },
      heading1: { run: { font: FONT, size: 20, smallCaps: true }, paragraph: { spacing: { before: 200, after: 100 }, keepNext: true } },
      heading2: { run: { font: FONT, size: 20, italics: true }, paragraph: { spacing: { before: 120, after: 60 }, keepNext: true } },
    },
  },
  sections: [
    { properties: { page: pageCfg, column: { count: 1 } },
      children: [title, ...authors] },
    { properties: { type: SectionType.CONTINUOUS, page: pageCfg, column: { count: 2, space: 360, equalWidth: true } },
      footers: { default: new Footer({ children: [new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 18 })],
      })] }) },
      children: [abstract, keywords, ...content] },
  ],
});

Packer.toBuffer(doc).then((b) => {
  fs.writeFileSync("/home/claude/dpn/paper/PDPN_Treatment_IEEE.docx", b);
  console.log("written:", b.length, "bytes");
});
