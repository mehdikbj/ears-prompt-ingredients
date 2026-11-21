# Study 2 — Pre-registered analysis plan

Design fixed on 26 Oct 2026 and revised on 7 Nov 2026, both before the freeze
commit and before any Study 2 API call (revisions listed in `README.md`,
Decisions). This file is listed in
`prompts/MANIFEST.json`; the inference script refuses to run if it changes
after the freeze commit. Any later change is a deviation and is logged in
`README.md` (Deviations), with the reason and the date.

## S0. Questions

An earlier exploratory run on the same 150 items (archived in
`archive/study1/`, not reported as a study) compared three whole prompts. Its
constrained prompt bundled four things (pattern templates, rules,
step-by-step reasoning, JSON output), so no effect could be attributed to any
one of them, and it had no few-shot condition. This study therefore
decomposes the prompt into ingredients on one shared base. It asks:

- **Q1 (ingredients).** Which prompt ingredient raises EARS compliance when
  every condition gets the same EARS pattern definitions: worked examples,
  chain-of-thought, or explicit rules? Do the ingredients interact?
- **Q2 (capability).** Does the effect of any ingredient depend on model tier?
- **Q3 (reference contrasts).** What does the shared base prompt (with the
  five EARS pattern definitions) add over a name-only prompt, which only
  names EARS? What does a JSON output format (`pattern`, `requirement`) add
  over a one-line answer?
- **Q4 (human quality, after ratings).** Do the examples and rules arms differ
  from the base in human-judged faithfulness, unambiguity, singularity and
  EARS well-formedness?

Q1 and Q2 together are the main contribution. Neither is framed as a test of
Khan (arXiv:2510.22251); Khan is cited as one prior claim that the best
technique depends on model capability.

## S1. Design

- **Items.** The 150 messified PURE items (`data/pure_150_messified.json`).
- **Models.** The locked lineup (`config/model_lineup.json`): pinned snapshots
  `gpt-5.4-nano-2026-03-17`, `gpt-5.4-mini-2026-03-17`, `gpt-5.4-2026-03-05`.
- **Arms (10).** Every item goes through every arm on every model: 4,500 outputs.

| Arm | Examples (E) | Chain-of-thought (C) | Rules (R) | Output |
|---|---|---|---|---|
| A0_name_only | – | – | – | one line (name-only reference prompt, `prompts/reference/name_only.txt`) |
| F_base | 0 | 0 | 0 | one line |
| F_E | 1 | 0 | 0 | one line |
| F_C | 0 | 1 | 0 | one line |
| F_R | 0 | 0 | 1 | one line |
| F_EC | 1 | 1 | 0 | one line |
| F_ER | 1 | 0 | 1 | one line |
| F_CR | 0 | 1 | 1 | one line |
| F_ECR | 1 | 1 | 1 | one line |
| J_json | 0 | 0 | 0 | JSON schema (`pattern`, `requirement`) |

  All F arms and J_json share one base: the task sentence and the five EARS
  patterns. Each ingredient is one fixed text block (`prompts/components/`).
  `build_prompts.py` asserts that any two arms differing in one factor differ
  by exactly that block, and that J_json differs from F_base only in the
  output instruction.
- **Examples.** Five fixed exemplars, one per pattern, approved by the author on
  26 Oct 2026, from PURE documents that supply no test item
  (`config/fewshot_exemplars.json`).
- **Call settings.** Identical to the prior exploratory run: chat completions, temperature 0, no
  max_tokens, no reasoning_effort parameter (the API default is `none` for all
  three snapshots, per OpenAI's model pages on 26 Oct 2026). Reasoning tokens
  are logged on every call; every call with reasoning tokens > 0 is listed
  (`results/analysis/12_calls_with_reasoning_tokens.csv`) and reported.
- **Order.** Calls are issued in a seeded random order (seed 20261026).
- **Pilot.** 5 frozen items × 10 arms × 3 models = 150 calls, archived under
  `results/pilot/`, never analysed. Its only purpose is to confirm the calls,
  logging and extraction work. If the pilot leads to any change, that change
  is a deviation.
- **Budget.** $15 cap for pilot + full run together, enforced by the script.
- **Sample size.** Fixed by the dataset (150 items). No formal power
  analysis was run; non-significant results are reported as "no difference
  detected", with confidence intervals, never as "no difference".

## S2. Outcomes

- **Primary.** `ears_v2_compliant` from the unchanged EARS v2 checker
  (`scripts/check_ears_compliance_v2.py`, SHA-256 `4a9bb37b…20e8f`). An
  output with no extractable answer counts as non-compliant.
- **Extraction.** One-line arms: the **last** `FINAL REQUIREMENT:` tag that
  starts a line (markdown markers such as `**`, `#` allowed before it); if no
  tag starts a line, the last exact upper-case tag anywhere. The answer is the
  first line after the tag that still has text once markdown markers are
  removed. JSON arm: the same tag rule for `FINAL JSON:`, then the
  `requirement` field. The first-tag rule (first tag anywhere, the prior
  run's rule) is sensitivity analysis S4.3. Extraction stops unless every planned call has
  exactly one successful record from the frozen prompt version.
- **Secondary** (definitions in `config/frozen_settings.json`, all on the
  checker's normalized text):
  - `template_slot`: an unfilled `<...>` slot (checker v2 rule R1);
  - `register_leakage`: contains one of the 32 frozen informal terms
    (list SHA-256 `a6552a46…429b529`, defined on the prior exploratory run);
  - `transcription`: at least half of the requirement's tokens sit in word
    4-grams copied from the messified input;
  - `extraction_failure`, and `length_words` (descriptive only).

  Secondary rates use outputs with an extractable requirement as the
  denominator. Extraction failures are reported on their own.

  The register-leakage and transcription measures were defined after
  inspecting the outputs of the prior exploratory run. Here they are frozen
  before any Study 2 call and treated as confirmatory secondary outcomes.

## S3. Confirmatory analysis (automatic outcomes)

All models are GEE with an identity link (effects in percentage points), an
independence working correlation and robust standard errors clustered on
item. The ingredients are effect-coded (±0.5), so each main effect is the
with-minus-without difference averaged over the other two ingredients and the
three tiers. Tier uses sum coding.

**S3.1 Primary family (Holm over 6 tests).** Model on the 8 factorial arms:
`y ~ e * c * r * C(tier, Sum)`.
1–3. Main effects of examples, chain-of-thought, rules (Wald z).
4–6. Examples × tier, chain-of-thought × tier, rules × tier (Wald χ², 2 df).
Q1 is answered by tests 1–3 and Q2 by tests 4–6. Each factor's effect
within each tier is also reported, with item-bootstrap 95% CIs (2,000
resamples, seed 20261026).

**S3.2 Ingredient interactions (Holm over 3).** examples × CoT, examples ×
rules, CoT × rules, from the same model. With ±0.5 coding, a two-way
coefficient is the change in one ingredient's effect when the other is
added. The three-way term is reported as exploratory.

**S3.3 Omnibus.** Cochran's Q across the 8 factorial arms, per tier (supporting
evidence only).

**S3.4 Reference contrasts (Holm over 2).** Shared base vs the
name-only prompt (F_base − A0_name_only) and JSON output (J_json − F_base),
each from a GEE on the two arms: `y ~ x * C(tier, Sum)`. The x × tier test is
reported alongside each. F_base differs from A0 mainly by the five pattern
definitions, but also by its task wording ("convert … exactly one" vs "turn …
a single") and by dropping A0's line "Read the description and write it as one
EARS requirement." So this contrast is reported as "shared base vs name-only
prompt", not as a pure pattern-definition effect.

**S3.5 Per-tier simple contrasts (Holm over 15).** A0, F_E, F_C, F_R and J_json
each against F_base, within each tier: exact McNemar test, paired difference,
item-bootstrap 95% CI.

## S4. Sensitivity analyses (primary family re-run)

1. Logit link (log-odds scale). Skipped and reported as not estimable if any
   factorial cell is at 0% or 100% compliance.
2. Extraction failures excluded instead of counted as non-compliant.
3. First-tag extraction rule (first tag instead of last).
4. Excluding PURE-014 and PURE-126, the two test items with the most wording
   in common with a few-shot exemplar.
5. Clustering on source document (19 clusters) instead of item. With 24
   parameters and only 19 clusters, this uses the bias-reduced (Mancl–DeRouen)
   robust covariance and t / F reference distributions with 18 denominator
   degrees of freedom.

A primary conclusion is called robust if its direction and Holm-significance
hold in sensitivity analyses 2–5. Analysis 1 changes the effect scale, so
only its direction is compared.

## S5. Secondary measures

For `template_slot`, `register_leakage` and `transcription`, the S3.1 model is
fitted and the same six tests are run, with Holm correction within each
measure. Rates are reported by arm and tier, and fail reasons and
detected patterns are tabulated. A measure with zero occurrences in the
factorial arms is reported without a test.

## S6. Human evaluation (Q4)

- **Sample.** 50 of the 150 items, drawn before any Study 2 call
  (`config/human_subsample_items.json`). The draw is stratified by source
  document with proportional allocation (seed 20261026). Rated arms: F_base,
  F_E and F_R, on all three tiers: 450 outputs per rater.
- **Raters.** Two raters: R1 (author) and R3. Both took part in the
  calibration of 1 Oct 2026 (with a third rater, R2, who does not rate this
  sample) on five outputs of the prior exploratory run for three inputs
  (PURE-002, PURE-014, PURE-017), followed by an online discussion of which
  no written record was kept (`calibration/`).
  No new calibration phase. Before any Study 2 sheet is built, R1 and R3
  hold a short refresher on eight first-round outputs on which they
  disagreed or which show a systematic difference between them, all for
  inputs outside the 50 sampled items and the calibration inputs
  (`calibration/refresher_2026-11/`, selection rule fixed in advance). The
  interpretations agreed there are the written directives for this round
  (guideline v1.1, `docs/human_eval_rating_guideline.md`). No Study 2 output is used.
- **Blinding.**
  - Raters see only the messified input and the generated requirement.
  - Every output has a neutral ID, and each rater gets a different seeded order.
  - The arm, the tier and the checker result stay in a hidden key.
  - Outputs with no extractable requirement are not rated (listed in the key).
  - IDs and rater orders come from a secret salt drawn when the sheets are
    built, so the key cannot be rebuilt from the repository. The key is
    git-ignored until both sheets are returned.
- **Instrument.** The criteria and anchors of the guideline, unchanged, with the refresher directives (v1.1): faithfulness,
  unambiguity, singularity, EARS well-formedness, each 1–5.
- **Agreement.**
  - Krippendorff's ordinal α between the two raters (bootstrap 95% CI).
  - Quadratic-weighted κ, Spearman, and % exact and % within one point, each
    with its chance level.
  - Low agreement is reported as is.
- **Confirmatory comparisons (Holm over 8 = 4 criteria × 2 contrasts).** The
  score is the mean of the two raters' scores for each output. F_E − F_base and F_R − F_base,
  pooled over tiers, from a GEE with identity link and item clusters:
  `score ~ arm * C(tier, Sum)`.
- **Reported alongside.**
  - Per-tier Wilcoxon signed-rank tests (descriptive).
  - The arm × tier Wald tests (exploratory).
  - Sensitivity: the confirmatory comparisons repeated without PURE-002 and
    PURE-014, the two sampled inputs whose outputs were discussed at
    calibration (`config/frozen_settings.json`, `human_evaluation`).
  - Validity: AUC of human EARS well-formedness and singularity against
    checker v2 compliance.
- **Timing.** The human-analysis script is written and committed before any
  returned rating sheet is opened. Each sheet is committed unmodified, with
  its SHA-1, before analysis. Two sheets that are identical, or share more
  than 50% of identical score rows, stop the analysis.

## S7. Interpretation rules

- Effects are reported in percentage points with 95% CIs, and Holm-adjusted
  p-values decide significance at α = 0.05 within each family.
- An ingredient "raises compliance" only if its S3.1 main effect is positive
  and Holm-significant. An effect "depends on capability" only if its × tier
  test is Holm-significant. In that case, the per-tier effects describe the
  pattern.
- A non-significant result is written as "no difference detected at this
  sample size", with its CI.
- Compliance results apply to EARS syntax as the v2 checker defines it. Quality
  claims rest only on S6.

## S8. Outside the scope of Study 2

- Models other than GPT-5.4, or models with internal reasoning enabled.
- Datasets other than PURE.
- Any interaction between JSON output and the other ingredients (JSON is one
  arm, not a factor).
- The rules effect as measured "from zero". The base already asks for
  "exactly one" requirement and glosses each pattern (e.g. "no condition"),
  which overlaps slightly with the rules block. The rules effect is therefore
  measured on top of the base.
- A reconstruction of the prior run's full constrained prompt. F_ECR is the
  closest arm but uses a different chain-of-thought wording and no JSON.

## S9. Deviations

Any change to a frozen file, any analysis not listed here, and any re-run
beyond resuming failed calls is a deviation. Deviations are logged in
`README.md` with the date and the reason, and analyses not listed here are
labelled exploratory in the paper.
