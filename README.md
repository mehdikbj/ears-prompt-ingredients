# Which Prompt Ingredients Help LLMs Choose the Right EARS Pattern? — replication package

Data, code and results of the paper *Which Prompt Ingredients Help LLMs Choose the Right EARS Pattern?
Two Factorial Studies Across Three GPT-5.4 Tiers* (submitted to ICSCA 2027).

## Reproduce the results

```bash
python3 -m venv .venv && . .venv/bin/activate     # Python 3.13
pip install -r requirements.txt
./reproduce.sh
```

`reproduce.sh` re-runs every analysis from the committed raw API records. It makes no API call and needs no
key. It then regenerates the LaTeX tables and figures of the paper, checks the frozen design files against
their recorded SHA-256 hashes, and compares every regenerated result with the committed one. The last line
should read `OK: every regenerated result matches the committed one.` CSV results are compared with a
floating-point tolerance (1e-9). One secondary sensitivity analysis is numerically unstable across machines,
without effect on its conclusion: the logit-link fit of checker compliance, whose Holm-adjusted p-values are 1
in every run (see `tools/compare_results.py`).

The model calls are not re-run. `study1/scripts/run_inference_study2.py` and `study2/scripts/run_inference_2b.py`
are included for transparency; they need an OpenAI API key, cost money and would not return identical outputs.
The nano snapshot (`gpt-5.4-nano-2026-03-17`) is removed from the API on 1 April 2027.

## Names in the paper and in this repository

| Paper | Repository |
|---|---|
| Study 1 | `study1/`|
| Study 2 | `study2/`|
| R1 | `R1`; annotator `B` in `study2/pattern_fit/` |
| R2 | in rating files; annotator `A` in `study2/pattern_fit/` |
| Base, Base+E, …, Base+ECR; Name-only; JSON (Study 1) | arms `F_base`, `F_E`, …, `F_ECR`; `A0_name_only`; `J_json` |
| Study 2 conditions | arms `B_<ingredients>_<reasoning>`, e.g. `B_base_none`, `B_ER_native` |
| nano, mini, full | `gpt-5.4-nano-2026-03-17`, `gpt-5.4-mini-2026-03-17`, `gpt-5.4-2026-03-05` |

## Where to find each element of the paper

| Paper | Files |
|---|---|
| 150 items from PURE (Section 3.2) | `data/pure_150.json` |
| Selection: criteria, procedure, shortlist, kept items | `docs/item_selection.md`, `data/interim/`, `scripts/` |
| Inputs (informal paraphrases): rules, examples, archived batches, quality checks | `docs/inputs.md`, `data/interim/messify_batches/`, `data/pure_150_messified.json`, `data/pure_150_messified_qc_report.json` |
| Prompts (Fig. 3), exemplars, Name-only and JSON prompts | `study1/prompts/`, `study1/config/`, `study2/prompts/`, `study2/config/` |
| Frozen plans and deviations (Table 2) | `study1/ANALYSIS_PLAN.md`, `study2/ANALYSIS_PLAN.md`; deviations in `study1/README.md`, `study2/README.md` |
| Raw API records (prompt, output, model fields, tokens) | `study1/results/raw_inference_study2.jsonl`, `study2/results/raw_inference_2b.jsonl`, pilots in `*/results/pilot*/` |
| Extraction and form checker (Section 3.5) | `scripts/check_ears_compliance_v2.py`; outputs `*/results/checks_*.jsonl` |
| Pattern labels (admissible patterns) | `study2/pattern_fit/01_instructions.md`, `02_sheet_annotator_A.csv`, `02_sheet_annotator_B.csv` |
| Human ratings: criteria, sheets, keys | criteria and directives for both studies: `study1/rater_kit/`; Study 1: `study1/results/human_ratings/`, `study1/results/human_eval_key_study2.jsonl`; Study 2: `study2/human_eval/` |
| Table 4 (Study 2 effects) | `study2/results/analysis/02_primary_tests.csv`, `03_reasoning_contrasts.csv` |
| Fig. 4 (tiers) | `study2/results/post_hoc/PH6_tier_figure_ci.csv` |
| Table 5 (admissible sets) | `study2/results/post_hoc/PH7_label_sets_contrasts.csv` |
| Table 6 (Study 1 by condition) | `study1/results/analysis/`, `study2/pattern_fit/results/` |
| Table 7 (input strata) | `study2/results/post_hoc/PH2_strata.csv` |
| Human ratings (Section 4.6) | `study2/human_eval/results/`, `study2/results/post_hoc/PH5_human_by_fit.csv` |
| Post hoc analyses | `study1/results/post_hoc/` (P1–P8, P10), `study2/results/post_hoc/` (PH1–PH14) |
| LaTeX tables and figures, as generated | `paper_outputs/` |

## Licences

Code (`*.py`, `*.sh`): MIT, see `LICENSE`. Data: CC BY 4.0, see `LICENSE-DATA`. The items and inputs derive
from PURE (Ferrari, Spagnolo and Gnesi, 2017; https://doi.org/10.5281/zenodo.1414117), distributed under
CC BY 4.0. The raw PURE documents are not included; see `data/raw/README.md`.
