# Study 1 (frozen as `study2/`)

Exploratory factorial study: worked examples (E), a chain-of-thought sentence (C) and explicit rules (R) on a
base prompt, plus two reference prompts (Name-only, JSON); 150 inputs × 10 prompts × 3 tiers = 4,500 calls at
temperature 0. Plan: `ANALYSIS_PLAN.md`.

| Folder | Content |
|---|---|
| `config/`, `prompts/` | Conditions, exemplars, frozen settings, prompt components and assembled prompts; `prompts/MANIFEST.json` holds the frozen hashes |
| `scripts/` | Prompt building, inference (API), extraction, checks, analyses, post hoc analyses, LaTeX tables |
| `rater_kit/` | Rating criteria and directives given to the raters, and the rated sample |
| `results/` | Raw API records, extracted answers, checks, analyses (`analysis/`), post hoc analyses (`post_hoc/`), human ratings and key |

## Human ratings

R1 and R2 (code `R3` in the files) rated 450 outputs. The paper does not use these ratings in its results
(Table 2). The planned analysis (`results/human_analysis/`) uses the sheets as returned
(`results/human_ratings/`). Two other versions of R2's sheet are in `results/human_ratings/not_used/` and are
not used: a first file, which R2 reported as the wrong file and replaced, and a later version made after a
comparison of the two raters' scores had been shared, so not an independent rating.

## Deviations from the frozen plan

| Date | Change | Reason |
|---|---|---|
| 2026-11-07 | `scripts/analyze_human_study2.py` reads the rating sheets as `utf-8-sig` instead of `utf-8`. | One returned sheet started with a byte-order mark. Technical; made before any analysis. |
| 2026-11-07/08 | R2's sheet: the first file was replaced by the file as returned; a later modified version was excluded (see above). | The plan requires each sheet to be analysed as returned. |
| 2026-11-08 | Post hoc analyses P1–P10 added (`scripts/analyze_post_hoc.py`, `results/post_hoc/`; P9, a comparison of the versions of R2's sheet, is not included here). | Internal review; labelled post hoc in the paper. |
| 2026-11-21 | Rater first names replaced by codes in `config/human_subsample_items.json` and `scripts/human_subsample_study2.py`, and in rating-sheet file names. | Privacy, before publication. No other change. |

Further deviations reported in the paper (Table 2): the chain-of-thought sentence produced no reasoning (post
hoc check), the checker accepts any opening WHERE clause, and Study 1 was re-scored for pattern fit in Study 2's
plan.
