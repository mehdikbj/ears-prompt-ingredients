# Study 2 (frozen as `study2b/`)

Planned factorial study: worked examples (E) × explicit rules (R) × reasoning (none, written, native);
150 inputs × 12 conditions × 3 tiers = 5,400 calls at the API's default temperature. Primary outcome: pattern
fit. Plan: `ANALYSIS_PLAN.md`.

| Folder | Content |
|---|---|
| `config/`, `prompts/` | Conditions, settings, prompt components and assembled prompts; `prompts/MANIFEST.json` holds the frozen hashes |
| `scripts/` | Prompt building, inference (API), extraction and checks, analyses, post hoc analyses (PH1–PH14), LaTeX tables and figures |
| `pattern_fit/` | Instructions and the two annotators' label sheets (admissible patterns and best pattern per input), consolidated sheet, analysis and results |
| `human_eval/` | Equivalence criterion, the two raters' sheets, key, analysis and results |
| `results/` | Raw API records, checks, pilots, analyses (`analysis/`), post hoc analyses (`post_hoc/`) |

## Deviations from the frozen plan

| Date | Change | Reason |
|---|---|---|
| 2026-11-08 | Before any call: the run script's clean-tree check ignores `results/`, so that an interrupted run can resume; a planned external registration was removed from the plan. | No design decision changed (noted in `ANALYSIS_PLAN.md`). |
| 2026-11-08 | Native `reasoning_effort` changed from `low` to `medium` after the pilot, before the full run. The first pilot is kept in `results/pilot_effort_low/`; the confirmation pilot is in `results/pilot/`. | At `low`, nano used reasoning tokens in 16 of 20 native calls, below the planned 90% threshold; mini and full: 20 of 20. |
| 2026-11-09 | Post hoc analyses PH1–PH13 added (`scripts/analyze_post_hoc_2b.py`). No frozen file changed. | Internal reviews; labelled post hoc in the paper. |
| 2026-11-21 | Post hoc analysis PH14 added (`scripts/analyze_post_hoc_ph14.py`): examples effect minus the rules and native-reasoning effects. No frozen file changed. | Review of the draft: is "examples help most" supported by a test? |
