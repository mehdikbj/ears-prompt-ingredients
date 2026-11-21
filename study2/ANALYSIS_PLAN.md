# Study 2b: analysis plan (FROZEN)

**Status:** frozen on 2026-11-08, before any Study 2b model call, in commit
`5e73e3a`. Before any call, two edits that change no design decision
followed: the clean-tree check (`91df480`) and the removal of a planned
external registration (2026-11-08, author's request).
Written by Claude; decisions D1–D7 taken by the author on 2026-11-08
(`README.md`). From the freeze on, every change to a file listed in
`prompts/MANIFEST.json` is a deviation, logged in `README.md` (Deviations)
with its date and reason.

## Why Study 2b exists

An internal review of the Study 2 paper (2026-11-08) found, and the data
confirm (`study2/POST_HOC.md`):

1. the chain-of-thought instruction produced no reasoning (0 of 1,800
   outputs), so chain-of-thought was never tested;
2. the checker accepts any WHERE clause, and without examples nano used the
   Optional-feature pattern in 63–76 of 150 outputs; pattern fit was never
   measured;
3. the human evaluation cannot support claims (one rater is the author whose
   Faithfulness scores follow the output pattern; agreement at or below
   chance on three criteria; calibration by adoption; about 17 s per output;
   a modified sheet).

Study 2b has three parts: **A** (a run that actually manipulates
reasoning), **P** (a human judgement, blind to outputs, of which patterns each input
admits) and **H** (a human evaluation of new outputs, including their
equivalence to the source requirement). P and H need no extra model call; P
can start as soon as the plan is frozen, H once the Study 2b outputs exist.

## Questions

- **Q1 (A).** Does reasoning, written out because the prompt asks for it or
  native (`reasoning_effort`), change pattern-fit compliance relative to no
  reasoning? Does it interact with examples or rules?
- **Q2 (A).** Do the effects of examples and rules hold on pattern-fit
  compliance?
- **Q3 (A).** Does any of these effects depend on the capability tier?
- **Q4 (P).** How often does the pattern of a Study 2 output fit its input?
  What are Study 2's base-versus-name-only contrast and ingredient effects on
  pattern-fit compliance?
- **Q5 (H).** On new outputs that neither rater has seen, does reasoning
  (written or native) change human-judged faithfulness, unambiguity,
  singularity, EARS well-formedness and equivalence to the source
  requirement, relative to no reasoning?

## A. Reasoning run

- **Arms (12)** = examples (0/1) × rules (0/1) × reasoning (none / written /
  native), `config/arms.json`. *None* and *native* arms use the Study 2
  prompts F_base, F_E, F_R, F_ER byte for byte; *native* differs only in
  `reasoning_effort`. *Written* arms add one block
  (`prompts/components/cot_written.txt`) that asks the model to write its
  reasoning after a `REASONING:` line before the answer line.
  `build_prompts_2b.py` asserts both properties.
- **Models.** The three Study 2 snapshots. `gpt-5.4-nano-2026-03-17` is
  removed from the API on **2027-04-01**.
- **Call.** Chat Completions; `reasoning_effort` passed on every call
  (none / none / medium; D2 was `low`, changed to `medium` after the pilot,
  see `README.md`, Deviations); `temperature` omitted on every call (D1); no
  output cap; one call per item × arm × tier = 5,400 calls, in a seeded
  random order. Pilot: the five Study 2 pilot items (180 calls), never
  analysed.
- **Extraction and checks.** Study 2's rules unchanged (last line-start
  `FINAL REQUIREMENT:` tag; checker v2; secondary measures), plus words
  before the tag and reasoning tokens (`extract_and_check_2b.py`).
- **Manipulation checks** (per tier; `settings.json`): written: ≥ 90 % of
  outputs with ≥ 15 words before the tag; native: ≥ 90 % of calls with
  reasoning tokens > 0; none: ≤ 5 % with any text before the tag and no
  reasoning tokens. A level that fails in a tier is reported as not
  manipulated there, and no conclusion is drawn about it there.
- **Primary outcome:** pattern-fit compliance = checker v2 compliant **and**
  the output's pattern is admissible for the item (union of the two
  annotators' labels from P). **Secondary:** checker compliance alone; WHERE share; transcription;
  register leakage.
- **Primary family** (Holm over 6), GEE, identity link, independence working
  correlation, robust SEs clustered on item:
  `y ~ e * r * C(reasoning, Sum) * C(tier, Sum)`, `e`, `r` effect-coded
  (±0.5). Tests: examples, rules (marginal contrasts averaged over the other
  factors), reasoning (2-df Wald), and each × tier (Wald).
  **Reasoning contrasts** (Holm over 2): written − none, native − none,
  averaged over examples, rules and tier.
- **Sensitivity** (`analyze_study2b.py`, each with its own Holm correction):
  logit link (Wald tests on log-odds coefficients); clusters = the 19 source
  documents with the bias-reduced covariance and t / F reference
  distributions; without PURE-014 and PURE-126 (closest to an exemplar);
  and, for pattern fit, the intersection, cue-rule and (if made)
  consolidated admissible sets. An effect is called **robust** if its
  direction and Holm-significance hold under the logit link, document
  clustering and without the two items, and, for pattern fit, with the
  intersection set.
- **Interpretation.** As Study 2 (S7): an effect is claimed only if positive
  or negative and Holm-significant; a non-significant result is "no
  difference detected" with its CI and the minimum detectable effect.
- **Power.** From Study 2's standard errors, main effects on checker
  compliance were detectable at about 2–3 pp (80 % power). Pattern fit is
  further from the ceiling, so its variance is larger; expect about 3–5 pp
  for main effects and reasoning contrasts. Per-tier effects only if large.

## P. Pattern admissibility (no model call)

- **Annotators (D4, 2026-11-08).** R3 (sheet A, first) and R1 (sheet B), the
  only people available. Both have seen Study 2 outputs and know the
  hypothesis (WHERE overuse), so their labels may lean towards marking
  Optional feature as inadmissible. Mitigations: labels are given on inputs
  only, without opening any output; R1 labels without seeing sheet A; the
  primary set is the **union**, the most lenient towards WHERE outputs; a
  pre-registered lexical cue rule (`OPTIONAL_CUES` in
  `analyze_pattern_fit.py`) gives an objective cross-check; the paper
  states who annotated and that they knew the hypothesis.
- **Material.** The 150 messified inputs only (`pattern_fit/02_sheet_annotator_*.csv`,
  different seeded orders). No output, no source requirement, no paper.
- **Task.** For each input, mark every admissible pattern (0/1 for the five
  patterns and "complex") and choose one best pattern
  (`pattern_fit/01_instructions.md`; Optional feature only if the input says
  or clearly implies the feature is optional).
- **Procedure.** Independent, no AI assistant. Each sheet committed
  unmodified with its SHA-1 before any comparison. Optionally, the two
  annotators then resolve disagreements in a consolidated file (sensitivity
  analysis only).
- **Agreement.** Cohen's κ and % agreement per pattern (admissible yes/no)
  and for the best pattern.
- **Admissible sets.** Union (primary), intersection (strict), consolidated
  (if made), and the cue rule (Optional feature admissible only if the input
  matches a pre-registered lexical cue; other patterns from the union). The
  agreement between the annotators' Optional-feature labels and the cue rule
  is reported.
- **Use.** Primary outcome of A; and a secondary analysis of all 4,500 Study 2
  outputs: compliance per condition and tier, the Study 2 primary family and
  F_base − A0 on pattern fit (`pattern_fit/analyze_pattern_fit.py`, committed
  before any label exists). Reported as a secondary analysis of existing
  data whose labels were collected after the outputs existed but blind to
  them.

## H. Human evaluation of new outputs (no extra model call)

- **Raters (D5, 2026-11-08).** R1 (first author) and R3, the only people
  available, volunteers. Re-rating the 450 Study 2 outputs they already
  rated would add little, so they rate outputs they have not seen.
- **Sample.** 150 Study 2b outputs: the 50 Study 2 sample items × the three
  reasoning levels of the base prompt (`B_base_none`, `B_base_written`,
  `B_base_native`); each item gets one tier by a seeded balanced draw, so
  its three outputs are paired (`human_eval/build_sheets_2b.py`). New salted
  IDs, a different order per rater and per sheet; key git-ignored until all
  sheets are back.
- **Sheet 1** (four criteria against the informal input): the instrument and
  directives of Study 2 (`study2/rater_kit/01_criteria.md`, v1.1). R3 rates
  first; no discussion until both sheets are committed.
- **Sheet 2** (D6, 2026-11-08: equivalence to the PURE source requirement,
  1–5, `human_eval/02_equivalence_criterion.md`), sent only after both
  sheet 1 files are committed, so the source does not influence sheet 1.
- **Analysis** (`human_eval/analyze_human_2b.py`): agreement per criterion
  (ordinal α with bootstrap CI, κ, ρ, exact and ±1 with chance levels);
  contrasts written − none and native − none on the mean of the two raters
  (GEE, item clusters, Holm over 10), with each rater's difference and
  R3-only estimates. A claim needs a Holm-significant mean contrast and the
  same sign for both raters; all human results are labelled exploratory,
  because one rater is the author.
- **Integrity.** Each sheet is committed unmodified as received, with its
  SHA-1, before analysis. Any later version of a sheet is logged and not
  analysed.

## Freeze and order of work

1. Author confirms D1–D7.
2. Done 2026-11-08: sensitivity analyses implemented, file renamed, status
   set to frozen, manifest rebuilt, dry run, freeze committed.
3. Pilot (180 calls), check, full run (5,400 calls), extraction and checks.
4. P can start at any time after the freeze, in parallel with step 3; H
   starts once the Study 2b outputs are checked.
5. Analyses run only after both annotation sheets (P) and all rating sheets
   (H) are committed.
