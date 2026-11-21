#!/usr/bin/env python3
"""
Part H analysis (ANALYSIS_PLAN.md). Written before any sheet exists.

  python3 study2b/human_eval/analyze_human_2b.py              # sheets and key committed
  python3 study2b/human_eval/analyze_human_2b.py --no-git     # test run only, not reportable

Agreement per criterion (Study 2's functions: ordinal alpha with bootstrap CI, weighted kappa,
Spearman, exact and within-one with chance levels). Contrasts B_base_written - B_base_none and
B_base_native - B_base_none on the mean of the two raters (GEE, item clusters; Holm over 10 =
5 criteria x 2), with each rater's own difference and R3-only estimates (R1 is the first author).
A claim needs the same sign for both raters and a Holm-significant mean-score contrast.
"""
import os
import subprocess
import sys

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.multitest import multipletests

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "study2", "scripts"))
import analyze_human_study2 as H  # noqa: E402

H.RATERS = {"R1": "R1", "R3": "R3"}
CRIT = ["faithfulness", "unambiguity", "singularity", "ears_wellformedness", "equivalence"]
BASE = "B_base_none"
CONTRASTS = ["B_base_written", "B_base_native"]
TERM = f"C(arm, Treatment('{BASE}'))"


def committed(path):
    r = subprocess.run(["git", "status", "--porcelain", "--", path], capture_output=True, text=True)
    t = subprocess.run(["git", "ls-files", "--error-unmatch", path], capture_output=True, text=True)
    return r.returncode == 0 and not r.stdout.strip() and t.returncode == 0


def load(sheet_dir, key_path, use_git):
    key = pd.DataFrame(H.read_jsonl(key_path)).set_index("sample_id")
    m = key[["item_id", "arm", "model_alias", "ears_v2_compliant"]].rename(columns={"model_alias": "tier"})
    for r in H.RATERS:
        for name, cols in [("04_sheet1_criteria", CRIT[:4]), ("05_sheet2_equivalence", ["equivalence"])]:
            p = f"{sheet_dir}/{name}_{r}.csv"
            if use_git and not committed(p):
                sys.exit(f"{p} is not committed unmodified")
            d = pd.read_csv(p, encoding="utf-8-sig").set_index("sample_id")
            assert set(d.index) == set(key.index), f"{p}: IDs differ from the key"
            for c in cols:
                assert d[c].isin([1, 2, 3, 4, 5]).all(), f"{p}: {c} must be 1-5"
                m[f"{c}_{r}"] = d[c]
    for c in CRIT:
        m[f"{c}_mean"] = m[[f"{c}_{r}" for r in H.RATERS]].mean(axis=1)
    return m.reset_index()


def contrasts(m, col_suffix, label):
    rows = []
    for c in CRIT:
        d = m.assign(score=m[f"{c}_{col_suffix}"])
        res = smf.gee(f"score ~ {TERM} * C(tier, Sum)", groups="item_id", data=d, family=sm.families.Gaussian(),
                      cov_struct=sm.cov_struct.Independence()).fit()
        ci = res.conf_int()
        for a in CONTRASTS:
            t = f"{TERM}[T.{a}]"
            g = m.groupby("arm")
            rows.append(dict(analysis=label, criterion=c, contrast=f"{a} - {BASE}", estimate=res.params[t],
                             ci_lo=ci.loc[t, 0], ci_hi=ci.loc[t, 1], p=res.pvalues[t],
                             R1=g[f"{c}_R1"].mean()[a] - g[f"{c}_R1"].mean()[BASE],
                             R3=g[f"{c}_R3"].mean()[a] - g[f"{c}_R3"].mean()[BASE]))
    out = pd.DataFrame(rows)
    out["p_holm"] = multipletests(out.p, method="holm")[1]
    out["same_sign"] = np.sign(out.R1) == np.sign(out.R3)
    return out


def main(sheet_dir=f"{HERE}/sheets", key_path=f"{HERE}/key_2b.jsonl", out=f"{HERE}/results"):
    use_git = "--no-git" not in sys.argv
    m = load(sheet_dir, key_path, use_git)
    os.makedirs(out, exist_ok=True)
    rng = np.random.default_rng(20261108)
    H.CRITERIA = CRIT
    H.agreement(m, rng).to_csv(f"{out}/01_agreement.csv", index=False)
    contrasts(m, "mean", "mean of R1 and R3").to_csv(f"{out}/02_contrasts.csv", index=False)
    contrasts(m, "R3", "R3 only").to_csv(f"{out}/03_contrasts_R3_only.csv", index=False)
    m.to_csv(f"{out}/04_merged_scores.csv", index=False)
    print(pd.read_csv(f"{out}/02_contrasts.csv").round(3).to_string(index=False))
    if not use_git:
        print("--no-git: TEST RUN, NOT REPORTABLE")


if __name__ == "__main__":
    main()
