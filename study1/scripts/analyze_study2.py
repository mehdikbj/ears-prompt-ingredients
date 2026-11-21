#!/usr/bin/env python3
"""
Pre-registered analysis of Study 2's automatic outcomes (ANALYSIS_PLAN.md).

  python3 study2/scripts/analyze_study2.py          # needs results/checks_study2.jsonl

Writes study2/results/analysis/*.csv and summary.md. Human ratings are
analysed separately (ANALYSIS_PLAN.md S6) once the sheets are returned.

Section numbers (S1...) refer to ANALYSIS_PLAN.md.
"""
import json
import os
import sys
import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import binomtest, f as f_dist, t as t_dist
from statsmodels.stats.contingency_tables import cochrans_q
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.proportion import proportion_confint

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from s2common import CHECKS, FROZEN_PATH, PURE150, RAW_FULL, RESULTS, load_json, read_jsonl

OUT = f"{RESULTS}/analysis"
TIERS = ["gpt-5.4-nano", "gpt-5.4-mini", "gpt-5.4"]
FACTORIAL = ["F_base", "F_E", "F_C", "F_R", "F_EC", "F_ER", "F_CR", "F_ECR"]
ALL_ARMS = ["A0_name_only", *FACTORIAL, "J_json"]
FACTORS = ["e", "c", "r"]
NAMES = {"e": "examples", "c": "chain-of-thought", "r": "rules"}
SENSITIVE_ITEMS = ["PURE-014", "PURE-126"]  # closest to a few-shot exemplar (fewshot_exemplars.json)
B = 2000


# ---------------------------------------------------------------- data

def load():
    df = pd.DataFrame(read_jsonl(CHECKS))
    if df.empty:
        sys.exit(f"{CHECKS} is empty or missing")
    docs = {i["id"]: i["source_document_key"] for i in load_json(PURE150)}
    df["doc"] = df.item_id.map(docs)
    df["tier"] = df.model_alias
    df["y"] = df.compliant_itt.astype(int)
    for f in FACTORS:
        df[f] = df[f.upper()].astype(float) - 0.5  # effect coding (+/-0.5); NaN for A0 and J_json
    # Upper-case "C" would shadow patsy's C() in the model formulas.
    return df.drop(columns=["E", "C", "R"])


def check_complete(df):
    exp = 150 * len(ALL_ARMS) * len(TIERS)
    dup = df.duplicated(["item_id", "arm", "tier"]).sum()
    cells = df.groupby(["arm", "tier"]).size()
    msg = f"{len(df)} outputs (expected {exp}); duplicates {dup}; cells {len(cells)} (expected {len(ALL_ARMS) * len(TIERS)})"
    complete = len(df) == exp and dup == 0 and (cells == 150).all()
    return complete, msg


# ---------------------------------------------------------------- helpers

def wilson(k, n):
    lo, hi = proportion_confint(k, n, method="wilson")
    return lo, hi


def mcnemar_exact(a, b):
    """a, b: paired 0/1 arrays. Returns (n10, n01, p)."""
    n10 = int(((a == 1) & (b == 0)).sum())
    n01 = int(((a == 0) & (b == 1)).sum())
    p = binomtest(min(n10, n01), n10 + n01, 0.5).pvalue if n10 + n01 else 1.0
    return n10, n01, p


def boot_diff(a, b, rng):
    n = len(a)
    idx = rng.integers(0, n, (B, n))
    d = a[idx].mean(1) - b[idx].mean(1)
    return np.percentile(d, 2.5), np.percentile(d, 97.5)


def gee(df, formula, group="item_id", family=None, small_sample=False):
    """small_sample=True (few clusters): bias-reduced (Mancl-DeRouen) robust covariance, and t / F reference
    distributions with (clusters - 1) denominator degrees of freedom instead of normal / chi-square."""
    fam = family or sm.families.Gaussian()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model = sm.GEE.from_formula(formula, groups=group, data=df, family=fam,
                                    cov_struct=sm.cov_struct.Independence())
        res = model.fit(cov_type="bias_reduced") if small_sample else model.fit()
    res.s2_df = (df[group].nunique() - 1) if small_sample else None
    return res


def term_cols(res, factors, with_tier):
    """Indices of parameters whose factors are exactly `factors` (+ tier if with_tier)."""
    idx = []
    for k, name in enumerate(res.model.exog_names):
        parts = name.split(":")
        base = {("tier" if p.startswith("C(tier") else p) for p in parts}
        want = set(factors) | ({"tier"} if with_tier else set())
        if name != "Intercept" and base == want:
            idx.append(k)
    return idx


TINY = 1e-10


def coef(res, name):
    """(estimate, ci_lo, ci_hi, z^2, p) for one coefficient. A coefficient that is exactly 0 with ~0 SE
    (no discordant pairs at all) gets p = 1 instead of a meaningless tiny p."""
    k = res.model.exog_names.index(name)
    est = float(res.params.iloc[k])
    se = float(np.sqrt(res.cov_params().iloc[k, k]))
    if abs(est) < TINY and se < TINY:
        return 0.0, 0.0, 0.0, 0.0, 1.0
    z = est / se
    if res.s2_df:
        p, q = 2 * t_dist.sf(abs(z), res.s2_df), t_dist.ppf(0.975, res.s2_df)
    else:
        p, q = float(res.pvalues.iloc[k]), 1.96
    return est, est - q * se, est + q * se, z ** 2, p


def wald(res, idx):
    if np.all(np.abs(res.params.values[idx]) < TINY) and np.all(res.bse.values[idx] < TINY):
        return 0.0, len(idx), 1.0
    if res.s2_df:  # F test: (Wald chi-square / q) against F(q, clusters - 1)
        b = res.params.values[idx]
        v = res.cov_params().values[np.ix_(idx, idx)]
        chi2 = float(b @ np.linalg.pinv(v) @ b)
        return chi2, len(idx), float(f_dist.sf(chi2 / len(idx), len(idx), res.s2_df))
    r = np.zeros((len(idx), len(res.params)))
    for row, k in enumerate(idx):
        r[row, k] = 1
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        w = res.wald_test(r, scalar=True)
    return float(np.squeeze(w.statistic)), len(idx), float(w.pvalue)


FORMULA = "y ~ e * c * r * C(tier, Sum)"


def primary_tests(res, label=""):
    """S3.1: the six primary tests: main effects of e, c, r; and e x tier, c x tier, r x tier."""
    rows = []
    for f in FACTORS:
        est, lo, hi, stat, p = coef(res, f)
        rows.append(dict(test=f"main effect: {NAMES[f]}", estimate=est, ci_lo=lo, ci_hi=hi, stat=stat, df=1, p=p,
                         analysis=label))
    for f in FACTORS:
        stat, d, p = wald(res, term_cols(res, [f], True))
        rows.append(dict(test=f"{NAMES[f]} x tier", estimate=np.nan, ci_lo=np.nan, ci_hi=np.nan, stat=stat, df=d, p=p,
                         analysis=label))
    t = pd.DataFrame(rows)
    t["p_holm"] = multipletests(t.p, method="holm")[1]
    return t


# ---------------------------------------------------------------- analysis

def main():
    os.makedirs(OUT, exist_ok=True)
    rng = np.random.default_rng(load_json(FROZEN_PATH)["seeds"]["bootstrap"])
    df = load()
    complete, msg = check_complete(df)
    if not complete and "--provisional" not in sys.argv:
        sys.exit(f"ERROR: {msg}. The pre-registered analysis needs all 4,500 outputs "
                 "(use --provisional only for a labelled, non-reportable look).")
    log = [msg + ("" if complete else "  ** INCOMPLETE: PROVISIONAL, NOT REPORTABLE **")]

    # Run provenance (raw file): spend, reasoning tokens, truncation.
    raw = pd.DataFrame(read_jsonl(RAW_FULL))
    if not raw.empty:
        ok = raw[raw.error.isna()]
        rt = ok.usage.map(lambda u: u.get("reasoning_tokens"))
        log.append(f"API: {len(ok)} successful calls, {raw.error.notna().sum()} failed attempts logged, "
                   f"spend ${raw.cost_usd.fillna(0).sum():.2f}, reasoning_tokens>0 in {(rt.fillna(0) > 0).sum()} calls "
                   f"(null in {rt.isna().sum()}), finish_reason counts {ok.finish_reason.value_counts().to_dict()}, "
                   f"distinct api_model_returned {sorted(ok.api_model_returned.unique())}")
        rt_calls = ok[rt.fillna(0) > 0][["item_id", "arm", "model_alias", "api_response_id"]].assign(
            reasoning_tokens=rt[rt.fillna(0) > 0])
        rt_calls.to_csv(f"{OUT}/12_calls_with_reasoning_tokens.csv", index=False)
    log.append(f"extraction failures {int(df.extraction_failure.sum())}; outputs with >1 answer tag {int((df.n_tags > 1).sum())}")

    # S2 descriptive: compliance by arm x tier
    rows = []
    for (a, t), g in df.groupby(["arm", "tier"]):
        k, n = int(g.y.sum()), len(g)
        lo, hi = wilson(k, n)
        rows.append(dict(arm=a, tier=t, n=n, compliant=k, rate=k / n, ci_lo=lo, ci_hi=hi,
                         extraction_failures=int(g.extraction_failure.sum())))
    desc = pd.DataFrame(rows)
    desc.to_csv(f"{OUT}/01_compliance_by_arm_tier.csv", index=False)

    fr = df.explode("fail_reasons").dropna(subset=["fail_reasons"])
    fr.groupby(["arm", "tier", "fail_reasons"]).size().rename("n").reset_index() \
        .to_csv(f"{OUT}/10_fail_reasons.csv", index=False)
    df.groupby(["arm", "tier", "pattern_v2"], dropna=False).size().rename("n").reset_index() \
        .to_csv(f"{OUT}/11_patterns.csv", index=False)

    fac = df[df.arm.isin(FACTORIAL)].copy()

    # S3.3 omnibus: Cochran's Q across the 8 factorial arms, per tier
    rows = []
    for t in TIERS:
        m = fac[fac.tier == t].pivot(index="item_id", columns="arm", values="y")[FACTORIAL].dropna()
        q = cochrans_q(m.values)
        rows.append(dict(tier=t, n_items=len(m), Q=q.statistic, df=q.df, p=q.pvalue))
    pd.DataFrame(rows).to_csv(f"{OUT}/02_cochran_q_factorial.csv", index=False)

    # S3.1 primary: factorial GEE, identity link (risk-difference scale), item clusters
    res = gee(fac, FORMULA)
    coefs = pd.DataFrame({"term": res.model.exog_names, "estimate": res.params.values, "se": res.bse.values,
                          "p": res.pvalues.values})
    coefs.to_csv(f"{OUT}/03_factorial_gee_coefficients.csv", index=False)
    prim = primary_tests(res, "primary: identity GEE, item clusters, extraction failure = non-compliant")
    prim.to_csv(f"{OUT}/03_primary_tests.csv", index=False)

    # S3.1 companion: each factor's effect within each tier (averaged over the other two factors)
    rows = []
    for t in TIERS:
        g = fac[fac.tier == t]
        for f in FACTORS:
            w = g.pivot_table(index="item_id", columns=f, values="y", aggfunc="mean")
            a, b = w[0.5].values, w[-0.5].values
            lo, hi = boot_diff(a, b, rng)
            rows.append(dict(tier=t, factor=NAMES[f], with_minus_without=a.mean() - b.mean(), ci_lo=lo, ci_hi=hi))
    pd.DataFrame(rows).to_csv(f"{OUT}/03_factor_effects_by_tier.csv", index=False)

    # S3.2 ingredient interactions (Holm over 3); three-way reported, exploratory
    rows = []
    for pair in (["e", "c"], ["e", "r"], ["c", "r"]):
        est, lo, hi, _, p = coef(res, ":".join(pair))
        rows.append(dict(test=f"{NAMES[pair[0]]} x {NAMES[pair[1]]}", estimate=est, ci_lo=lo, ci_hi=hi, p=p))
    inter = pd.DataFrame(rows)
    inter["p_holm"] = multipletests(inter.p, method="holm")[1]
    est, lo, hi, _, p = coef(res, "e:c:r")
    inter = pd.concat([inter, pd.DataFrame([dict(test="examples x CoT x rules (exploratory)", estimate=est,
                                                 ci_lo=lo, ci_hi=hi, p=p, p_holm=np.nan)])])
    inter.to_csv(f"{OUT}/04_ingredient_interactions.csv", index=False)

    # S3.4 reference contrasts: pattern definitions (F_base vs A0) and JSON (J_json vs F_base); Holm over 2
    rows = []
    for label, a, b in [("shared base vs name-only prompt: F_base - A0_name_only", "F_base", "A0_name_only"),
                        ("JSON output: J_json - F_base", "J_json", "F_base")]:
        d = df[df.arm.isin([a, b])].copy()
        d["x"] = (d.arm == a).astype(float) - 0.5
        r2 = gee(d, "y ~ x * C(tier, Sum)")
        est, lo, hi, _, p = coef(r2, "x")
        stat, dd, p_int = wald(r2, term_cols(r2, ["x"], True))
        rows.append(dict(test=label, estimate=est, ci_lo=lo, ci_hi=hi, p=p,
                         x_tier_chi2=stat, x_tier_df=dd, x_tier_p=p_int))
    ref = pd.DataFrame(rows)
    ref["p_holm"] = multipletests(ref.p, method="holm")[1]
    ref.to_csv(f"{OUT}/05_reference_contrasts.csv", index=False)

    # S3.5 per-tier simple contrasts vs F_base, exact McNemar, Holm over all 15
    rows = []
    for t in TIERS:
        w = df[df.tier == t].pivot(index="item_id", columns="arm", values="y")
        for a in ["A0_name_only", "F_E", "F_C", "F_R", "J_json"]:
            x, base = w[a].values, w["F_base"].values
            n10, n01, p = mcnemar_exact(x, base)
            lo, hi = boot_diff(x, base, rng)
            rows.append(dict(tier=t, contrast=f"{a} - F_base", diff=x.mean() - base.mean(), ci_lo=lo, ci_hi=hi,
                             n_arm_only=n10, n_base_only=n01, p=p))
    simple = pd.DataFrame(rows)
    simple["p_holm"] = multipletests(simple.p, method="holm")[1]
    simple.to_csv(f"{OUT}/06_simple_contrasts_per_tier.csv", index=False)

    # S4 sensitivity analyses of the six primary tests
    sens = []
    cell_rates = fac.groupby(["arm", "tier"]).y.mean()
    if ((cell_rates == 0) | (cell_rates == 1)).any():
        log.append("logit GEE not estimable: at least one factorial cell is at 0% or 100%")
    else:
        try:
            sens.append(primary_tests(gee(fac, FORMULA, family=sm.families.Binomial()), "logit link (log-odds scale)"))
        except Exception as e:  # noqa: BLE001
            log.append(f"logit GEE failed: {e}")
    d = fac[~fac.extraction_failure]
    sens.append(primary_tests(gee(d, FORMULA), "extraction failures excluded"))
    d = fac.copy()
    d["y"] = d.ears_v2_compliant_first_tag.astype(int)
    sens.append(primary_tests(gee(d, FORMULA), "first-tag extraction rule"))
    d = fac[~fac.item_id.isin(SENSITIVE_ITEMS)]
    sens.append(primary_tests(gee(d, FORMULA), f"excluding {', '.join(SENSITIVE_ITEMS)}"))
    sens.append(primary_tests(gee(fac, FORMULA, group="doc", small_sample=True),
                              "clusters = source document (19), bias-reduced SE, t/F with 18 df"))
    pd.concat(sens).to_csv(f"{OUT}/07_sensitivity.csv", index=False)

    # S5 secondary measures (frozen definitions): same six tests per measure, Holm within measure
    rows, sec = [], []
    for m in ["template_slot", "register_leakage", "transcription"]:
        d = df.dropna(subset=[m]).copy()
        d[m] = d[m].astype(int)
        for (a, t), g in d.groupby(["arm", "tier"]):
            rows.append(dict(measure=m, arm=a, tier=t, n_extractable=len(g), rate=g[m].mean()))
        f = d[d.arm.isin(FACTORIAL)].copy()
        f["y"] = f[m]
        if f.y.sum() == 0:
            log.append(f"{m}: zero occurrences in factorial arms; no test")
            continue
        sec.append(primary_tests(gee(f, FORMULA), m))
    pd.DataFrame(rows).to_csv(f"{OUT}/08_secondary_rates.csv", index=False)
    df.dropna(subset=["length_words"]).groupby(["arm", "tier"]).length_words.agg(["count", "mean", "median"]) \
        .reset_index().to_csv(f"{OUT}/13_length_words.csv", index=False)  # descriptive only (S2)
    if sec:
        pd.concat(sec).to_csv(f"{OUT}/08_secondary_tests.csv", index=False)

    write_summary(log, desc, prim, inter, ref)
    print("\n".join(log))
    print(f"\nWrote {OUT}/")


def write_summary(log, desc, prim, inter, ref):
    piv = desc.pivot(index="arm", columns="tier", values="rate").reindex(ALL_ARMS)[TIERS]
    fmt = lambda t: t.to_string(float_format=lambda v: f"{v:.3f}")
    lines = ["# Study 2: automatic-outcome analysis", "", "Generated by analyze_study2.py. Plan: ANALYSIS_PLAN.md.", "",
             "## Run log", "", *[f"- {l}" for l in log], "",
             "## EARS v2 compliance (extraction failure = non-compliant)", "", "```", fmt(piv), "```", "",
             "## Primary tests (S3.1, Holm over 6)", "", "```",
             fmt(prim[["test", "estimate", "ci_lo", "ci_hi", "stat", "df", "p", "p_holm"]]), "```", "",
             "## Ingredient interactions (S3.2)", "", "```", fmt(inter), "```", "",
             "## Reference contrasts (S3.4)", "", "```", fmt(ref), "```", ""]
    with open(f"{OUT}/summary.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
