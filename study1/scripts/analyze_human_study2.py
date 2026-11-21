#!/usr/bin/env python3
"""
Study 2 human-evaluation analysis (ANALYSIS_PLAN.md, S6).

  python3 study2/scripts/analyze_human_study2.py            # pre-registered run
  python3 study2/scripts/analyze_human_study2.py --no-git   # skip the git checks (testing only, not reportable)

Written and committed before any returned rating sheet was opened (S6,
"Timing"). Inputs:
  study2/results/human_eval_key_study2.jsonl              hidden key (committed with git add -f
                                                         only after both sheets are back)
  study2/results/human_ratings/04_study2_rating_sheet_<rater>.csv
                                                         each returned sheet, committed unmodified
Outputs: study2/results/human_analysis/*.csv and summary.md.

Steps, in the order of S6:
  1. Integrity: both sheets present, committed and unmodified (git); unchanged columns;
     exactly the rated sample IDs of the key, once each; every score an integer 1-5.
     Stops if the two sheets are identical or share more than 50% identical score rows.
  2. Agreement between R1 and R3, per criterion: Krippendorff's ordinal alpha with a
     bootstrap 95% CI (2,000 resamples of outputs, frozen seed); quadratic-weighted
     Cohen's kappa; Spearman rho; % exact and % within one point, each with its chance
     level (from the two raters' marginal distributions).
  3. Confirmatory (Holm over 8 = 4 criteria x 2 contrasts): score = mean of the two
     raters; GEE with identity link, independence working correlation, robust SEs
     clustered on item: score ~ C(arm, Treatment('F_base')) * C(tier, Sum). With tier
     sum-coded, the F_E and F_R coefficients are F_E - F_base and F_R - F_base pooled
     over tiers.
  4. Reported alongside: per-tier Wilcoxon signed-rank tests (descriptive); arm x tier
     Wald tests (exploratory); the confirmatory comparisons without PURE-002 and
     PURE-014 (sensitivity, frozen_settings.json -> human_evaluation); validity: AUC of
     human EARS well-formedness and singularity against checker v2 compliance
     (item-cluster bootstrap 95% CI); per-rater cell means (descriptive).
"""
import csv
import hashlib
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from s2common import FROZEN_PATH, RESULTS, load_json, read_jsonl
from human_subsample_study2 import CRITERIA, KEY, RATED_ARMS, RATERS

import numpy as np
import pandas as pd
import krippendorff
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy.stats import chi2, spearmanr, wilcoxon
from sklearn.metrics import cohen_kappa_score, roc_auc_score
from statsmodels.stats.multitest import multipletests

SHEET_DIR = f"{RESULTS}/human_ratings"
OUT = f"{RESULTS}/human_analysis"
COLUMNS = ["sample_id", "messified_input", "generated_requirement", *CRITERIA, "notes"]
SCALE = [1, 2, 3, 4, 5]
B = 2000
CONTRASTS = ["F_E", "F_R"]
ARM_TERM = "C(arm, Treatment('F_base'))"
FORMULA = f"score ~ {ARM_TERM} * C(tier, Sum)"


def sha(path, algo):
    h = hashlib.new(algo)
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def git_clean_and_tracked(path):
    tracked = subprocess.run(["git", "ls-files", "--error-unmatch", path], capture_output=True).returncode == 0
    dirty = subprocess.run(["git", "status", "--porcelain", "--", path], capture_output=True, text=True).stdout.strip()
    return tracked and not dirty


def load_sheets(key_rated, use_git):
    sheets, problems, meta = {}, [], []
    for rid, name in RATERS.items():
        path = f"{SHEET_DIR}/04_study2_rating_sheet_{name}.csv"
        if not os.path.exists(path):
            problems.append(f"{rid}: {path} not found")
            continue
        if use_git and not git_clean_and_tracked(path):
            problems.append(f"{rid}: {path} is not committed unmodified")
        # utf-8-sig: accept a UTF-8 byte-order mark (added by Excel to R1's sheet).
        # Deviation logged in study2/README.md (2026-11-07); no effect on any score.
        with open(path, newline="", encoding="utf-8-sig") as f:
            rows = list(csv.reader(f))
        if not rows or rows[0] != COLUMNS:
            problems.append(f"{rid}: columns changed: {rows[0] if rows else 'empty file'}")
            continue
        recs = [dict(zip(COLUMNS, r)) for r in rows[1:] if any(c.strip() for c in r)]
        ids = [r["sample_id"] for r in recs]
        if len(ids) != len(set(ids)):
            problems.append(f"{rid}: duplicate sample IDs")
        if set(ids) != key_rated:
            problems.append(f"{rid}: {len(set(ids) - key_rated)} unknown IDs, {len(key_rated - set(ids))} missing IDs")
        for r in recs:
            for c in CRITERIA:
                v = r[c].strip()
                if v not in {"1", "2", "3", "4", "5"}:
                    problems.append(f"{rid}: {r['sample_id']} {c} = {v!r} (must be an integer 1-5)")
                    break
        df = pd.DataFrame(recs)
        for c in CRITERIA:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        sheets[rid] = df.set_index("sample_id")
        meta.append(dict(rater=rid, file=path, rows=len(recs), sha1=sha(path, "sha1"), sha256=sha(path, "sha256")))
    return sheets, problems, meta


def chance_levels(a, b):
    pa = np.array([(a == k).mean() for k in SCALE])
    pb = np.array([(b == k).mean() for k in SCALE])
    exact = float(pa @ pb)
    within = float(sum(pa[i] * pb[j] for i in range(5) for j in range(5) if abs(i - j) <= 1))
    return exact, within


def alpha(a, b):
    return krippendorff.alpha(reliability_data=np.vstack([a, b]).astype(float), value_domain=SCALE,
                              level_of_measurement="ordinal")


def agreement(m, rng):
    rows = []
    r_a, r_b = list(RATERS)
    for c in CRITERIA:
        a, b = m[f"{c}_{r_a}"].to_numpy(), m[f"{c}_{r_b}"].to_numpy()
        n = len(a)
        boots = []
        for _ in range(B):
            idx = rng.integers(0, n, n)
            try:
                boots.append(alpha(a[idx], b[idx]))
            except Exception:  # noqa: BLE001 -- a degenerate resample (one category) has no alpha
                pass
        ce, cw = chance_levels(a, b)
        rho, p_rho = spearmanr(a, b)
        rows.append(dict(criterion=c, n=n, alpha_ordinal=alpha(a, b),
                         alpha_ci_lo=np.percentile(boots, 2.5), alpha_ci_hi=np.percentile(boots, 97.5),
                         kappa_quadratic=cohen_kappa_score(a, b, weights="quadratic", labels=SCALE),
                         spearman_rho=rho, spearman_p=p_rho,
                         exact=(a == b).mean(), exact_chance=ce,
                         within_one=(np.abs(a - b) <= 1).mean(), within_one_chance=cw,
                         mean_R_a=a.mean(), mean_R_b=b.mean()))
    return pd.DataFrame(rows).rename(columns={"mean_R_a": f"mean_{r_a}", "mean_R_b": f"mean_{r_b}"})


def fit(d):
    return smf.gee(FORMULA, groups="item_id", data=d, family=sm.families.Gaussian(),
                   cov_struct=sm.cov_struct.Independence()).fit()


def term(arm):
    return f"{ARM_TERM}[T.{arm}]"


def confirmatory(m, label):
    rows, inter = [], []
    for c in CRITERIA:
        d = m[["item_id", "arm", "tier"]].assign(score=m[f"{c}_mean"])
        res = fit(d)
        ci = res.conf_int()
        for arm in CONTRASTS:
            t = term(arm)
            rows.append(dict(analysis=label, criterion=c, contrast=f"{arm} - F_base", estimate=res.params[t],
                             ci_lo=ci.loc[t, 0], ci_hi=ci.loc[t, 1], p=res.pvalues[t]))
            names = [n for n in res.params.index if n.startswith(t + ":")]
            b = res.params[names].to_numpy()
            v = res.cov_params().loc[names, names].to_numpy()
            stat = float(b @ np.linalg.solve(v, b))
            inter.append(dict(analysis=label, criterion=c, test=f"{arm} vs F_base x tier (exploratory)",
                              wald_chi2=stat, df=len(names), p=chi2.sf(stat, len(names))))
    out = pd.DataFrame(rows)
    out["p_holm"] = multipletests(out.p, method="holm")[1]
    return out, pd.DataFrame(inter)


def per_tier_wilcoxon(m):
    rows = []
    for c in CRITERIA:
        w = m.pivot_table(index=["item_id", "tier"], columns="arm", values=f"{c}_mean")
        for t in sorted(m.tier.unique()):
            wt = w.xs(t, level="tier")
            for arm in CONTRASTS:
                pair = wt[[arm, "F_base"]].dropna()
                diff = (pair[arm] - pair["F_base"]).to_numpy()
                nz = int((diff != 0).sum())
                if nz == 0:
                    stat, p = np.nan, np.nan
                else:
                    stat, p = wilcoxon(pair[arm], pair["F_base"], zero_method="wilcox")
                rows.append(dict(criterion=c, tier=t, contrast=f"{arm} - F_base", n_items=len(pair),
                                 n_nonzero=nz, mean_diff=diff.mean(), wilcoxon_stat=stat, p=p))
    return pd.DataFrame(rows)


def validity(m, rng):
    rows = []
    y = m["ears_v2_compliant"].astype(int).to_numpy()
    items = m["item_id"].unique()
    by_item = {i: np.flatnonzero(m["item_id"].to_numpy() == i) for i in items}
    for c in ["ears_wellformedness", "singularity"]:
        s = m[f"{c}_mean"].to_numpy()
        if len(set(y)) < 2:
            rows.append(dict(criterion=c, auc=np.nan, ci_lo=np.nan, ci_hi=np.nan, n_pass=int(y.sum()), n_fail=0))
            continue
        boots = []
        for _ in range(B):
            idx = np.concatenate([by_item[i] for i in rng.choice(items, len(items))])
            if len(set(y[idx])) == 2:
                boots.append(roc_auc_score(y[idx], s[idx]))
        rows.append(dict(criterion=c, auc=roc_auc_score(y, s), ci_lo=np.percentile(boots, 2.5),
                         ci_hi=np.percentile(boots, 97.5), n_pass=int(y.sum()), n_fail=int((1 - y).sum())))
    return pd.DataFrame(rows)


def main():
    use_git = "--no-git" not in sys.argv
    frozen = load_json(FROZEN_PATH)
    seed = frozen["seeds"]["bootstrap"]
    excluded = frozen["human_evaluation"]["sensitivity_exclude_items"]

    if not os.path.exists(KEY):
        sys.exit(f"{KEY} not found")
    if use_git and not git_clean_and_tracked(KEY):
        sys.exit(f"{KEY} must be committed (git add -f) after both sheets are back, and unmodified")
    key = pd.DataFrame(read_jsonl(KEY))
    rated = key[key.rated]
    sheets, problems, meta = load_sheets(set(rated.sample_id), use_git)
    if problems:
        sys.exit("Integrity check failed, nothing analysed:\n  " + "\n  ".join(problems[:30]))

    (ra, a), (rb, b) = list(sheets.items())
    a, b = a.loc[sorted(a.index)], b.loc[sorted(b.index)]
    if a[CRITERIA].equals(b[CRITERIA]):
        sys.exit("The two sheets have identical scores: stopping (S6).")
    same_rows = (a[CRITERIA].to_numpy() == b.loc[a.index, CRITERIA].to_numpy()).all(axis=1).mean()
    if same_rows > 0.5:
        sys.exit(f"{same_rows:.0%} of score rows are identical in the two sheets (> 50%): stopping (S6).")

    m = rated.set_index("sample_id")[["item_id", "arm", "model_alias", "ears_v2_compliant"]].rename(
        columns={"model_alias": "tier"})
    for rid, s in sheets.items():
        for c in CRITERIA:
            m[f"{c}_{rid}"] = s[c]
    for c in CRITERIA:
        m[f"{c}_mean"] = m[[f"{c}_{rid}" for rid in RATERS]].mean(axis=1)
    m = m.reset_index()
    assert set(m.arm) <= set(RATED_ARMS)

    os.makedirs(OUT, exist_ok=True)
    rng = np.random.default_rng(seed)
    pd.DataFrame(meta).to_csv(f"{OUT}/00_sheets.csv", index=False)
    agr = agreement(m, rng)
    agr.to_csv(f"{OUT}/01_agreement.csv", index=False)
    conf, inter = confirmatory(m, "confirmatory")
    conf.to_csv(f"{OUT}/02_confirmatory.csv", index=False)
    sens, inter_s = confirmatory(m[~m.item_id.isin(excluded)], f"sensitivity: excluding {', '.join(excluded)}")
    sens.to_csv(f"{OUT}/03_sensitivity_calibration_items.csv", index=False)
    pd.concat([inter, inter_s]).to_csv(f"{OUT}/04_arm_x_tier_exploratory.csv", index=False)
    wil = per_tier_wilcoxon(m)
    wil.to_csv(f"{OUT}/05_wilcoxon_per_tier.csv", index=False)
    val = validity(m, rng)
    val.to_csv(f"{OUT}/06_validity_auc.csv", index=False)
    cell = m.groupby(["arm", "tier"])[[f"{c}_{s}" for c in CRITERIA for s in [*RATERS, "mean"]]].mean().reset_index()
    cell.to_csv(f"{OUT}/07_cell_means.csv", index=False)
    m.to_csv(f"{OUT}/08_merged_scores.csv", index=False)

    fmt = lambda t: t.to_string(index=False, float_format=lambda v: f"{v:.3f}")
    lines = ["# Study 2: human-evaluation analysis", "",
             "Generated by analyze_human_study2.py (ANALYSIS_PLAN.md, S6)." +
             ("" if use_git else "  **--no-git: TEST RUN, NOT REPORTABLE**"), "",
             f"Rated outputs: {len(m)} ({m.item_id.nunique()} items x {m.arm.nunique()} arms x {m.tier.nunique()} tiers); "
             f"raters {', '.join(RATERS)}; score rows identical in both sheets: {same_rows:.1%}", "",
             "## Sheets", "", "```", fmt(pd.DataFrame(meta)[["rater", "rows", "sha1"]]), "```", "",
             "## Agreement (R1-R3)", "", "```", fmt(agr), "```", "",
             "## Confirmatory comparisons (Holm over 8)", "", "```", fmt(conf.drop(columns="analysis")), "```", "",
             f"## Sensitivity: excluding {', '.join(excluded)}", "", "```", fmt(sens.drop(columns="analysis")), "```", "",
             "## Validity: AUC of human scores against checker v2 compliance", "", "```", fmt(val), "```", ""]
    with open(f"{OUT}/summary.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
