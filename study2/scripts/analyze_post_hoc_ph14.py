#!/usr/bin/env python3
"""
PH14 (post hoc, unadjusted): is the examples effect on pattern fit larger than the other ingredients' effects?

NOT in study2b/ANALYSIS_PLAN.md. Added on 2026-11-21, after the planned and earlier post hoc analyses, because a
reviewer of the draft asked whether "worked examples show the largest improvement" is supported by a test rather
than by ranking point estimates.

For each item, the examples effect (mean fit with E minus without, averaged over the other factors) minus another
ingredient's effect (rules; written - none; native - none), then a t interval over the 150 items. Same label
handling (union of the two annotators' admissible sets) and the same helpers as analyze_post_hoc_2b.py.

  python3 study2b/scripts/analyze_post_hoc_ph14.py   # run from the repository root
  -> study2b/results/post_hoc/PH14_examples_vs_other_ingredients.csv
"""
import os
import sys

import pandas as pd

ROOT = os.getcwd()
sys.path.insert(0, os.path.join(ROOT, "study2b", "scripts"))
import analyze_post_hoc_2b as P  # noqa: E402

PF = P.PF
EFFECTS = {
    "examples": (lambda x: x.E == 1, lambda x: x.E == 0),
    "rules": (lambda x: x.R == 1, lambda x: x.R == 0),
    "written - none": (lambda x: x.reasoning == "written", lambda x: x.reasoning == "none"),
    "native - none": (lambda x: x.reasoning == "native", lambda x: x.reasoning == "none"),
}


def main():
    a = PF.read_sheet(f"{P.PATTERN_FIT_DIR}/02_sheet_annotator_A.csv")
    b = PF.read_sheet(f"{P.PATTERN_FIT_DIR}/02_sheet_annotator_B.csv")
    A_, B_ = PF.admissible(a), PF.admissible(b)
    U = {i: A_[i] | B_[i] for i in A_}
    c2 = pd.DataFrame(P.S.read_jsonl(P.CHECKS_2B))
    c2["comp"] = c2.compliant_itt.astype(bool)
    c2["adm"] = [p in U[i] for p, i in zip(c2.pattern_v2, c2.item_id)]
    c2["fit"] = (c2.comp & c2.adm).astype(float)
    rows = []
    for tier in ["all"] + P.TIERS:
        d = c2 if tier == "all" else c2[c2.model_alias == tier]
        eff = {k: P.paired(d, pl, mi, "fit") for k, (pl, mi) in EFFECTS.items()}
        for other in ["rules", "written - none", "native - none"]:
            rows.append(dict(contrast=f"examples effect - {other} effect", tier=tier,
                             **P.tci((eff["examples"] - eff[other]).dropna())))
    os.makedirs(P.OUT, exist_ok=True)
    pd.DataFrame(rows).to_csv(f"{P.OUT}/PH14_examples_vs_other_ingredients.csv", index=False)


if __name__ == "__main__":
    main()
