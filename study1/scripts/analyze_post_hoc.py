#!/usr/bin/env python3
"""
Post hoc analyses of Study 2, written on 2026-11-08 in response to an internal
review of the paper draft (study2/POST_HOC.md).

NOT PRE-REGISTERED. None of these analyses is in ANALYSIS_PLAN.md, none
replaces a pre-registered result, and the paper labels every number taken
from them as post hoc. They read committed files only and make no API call.

  python3 study2/scripts/analyze_post_hoc.py      # from the repository root

Writes study2/results/post_hoc/*.csv and summary.md:
  P1  chain-of-thought manipulation check (text before the answer tag, tokens)
  P2  EARS pattern distribution per condition and tier, and in the PURE originals
  P3  bound: compliance with every Optional-feature (WHERE) output counted as non-compliant
  P4  checker fail reasons with and without each ingredient
  P5  minimum detectable effects (80% power) from the pre-registered standard errors
  P6  primary family without the eirene_fun_7 items (same specification as an exemplar)
  P7  contamination probe: numbers and acronyms of the PURE original absent from the input
  P8  dependence of each rater's scores on the output's EARS pattern (sheets as returned)
  P10 rules effect on Unambiguity without outputs flagged for transcription or leakage
"""
import os
import re
import sys

import numpy as np
import pandas as pd
from scipy.stats import norm, spearmanr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyze_study2 as A  # noqa: E402  (pre-registered helpers, reused unchanged)
from s2common import ARM_DIR, CHECKS, MESSIFIED, PURE150, RAW_FULL, RESULTS, load_json, read_jsonl  # noqa: E402

OUT = f"{RESULTS}/post_hoc"
AN = f"{RESULTS}/analysis"
H_RET = f"{RESULTS}/human_analysis"  # pre-registered analysis, sheets as returned
TIERS = A.TIERS
FACTORIAL = A.FACTORIAL
CRIT = ["faithfulness", "unambiguity", "singularity", "ears_wellformedness"]
WHERE = "optional-feature"


def p1_cot_manipulation(log):
    raw = pd.DataFrame(read_jsonl(RAW_FULL))
    raw = raw[raw.error.isna()].copy()
    rows = []
    for r in raw.itertuples():
        tag = "FINAL JSON:" if r.arm == "J_json" else "FINAL REQUIREMENT:"
        out = r.raw_output or ""
        k = out.find(tag)
        before = out[:k] if k >= 0 else ""
        rows.append(dict(arm=r.arm, tier=r.model_alias, cot=int(r.C == 1) if r.C is not None else np.nan,
                         tag_found=k >= 0, words_before_tag=len(before.split()),
                         completion_tokens=(r.usage or {}).get("completion_tokens"),
                         reasoning_tokens=(r.usage or {}).get("reasoning_tokens") or 0))
    d = pd.DataFrame(rows)
    t = d.groupby(["arm", "tier"]).agg(n=("arm", "size"), tag_found=("tag_found", "sum"),
                                        outputs_with_text_before_tag=("words_before_tag", lambda s: int((s > 0).sum())),
                                        mean_completion_tokens=("completion_tokens", "mean"),
                                        reasoning_tokens_total=("reasoning_tokens", "sum")).reset_index()
    t.to_csv(f"{OUT}/P1_cot_manipulation_check.csv", index=False)
    f = d[d.arm.isin(FACTORIAL)]
    by = f.groupby(["tier", "cot"]).completion_tokens.mean().unstack()
    by.columns = ["without_cot", "with_cot"]
    by["difference"] = by.with_cot - by.without_cot
    by.reset_index().to_csv(f"{OUT}/P1_cot_tokens_by_tier.csv", index=False)
    cot_arms = f[f.cot == 1]
    log.append(f"P1: CoT arms: {len(cot_arms)} outputs, {int((cot_arms.words_before_tag > 0).sum())} with any text "
               f"before the answer tag; reasoning tokens total {int(d.reasoning_tokens.sum())}; "
               f"mean completion tokens with minus without CoT by tier: "
               f"{ {k: round(v, 1) for k, v in by.difference.items()} }")


def p2_patterns(df, log):
    t = df.groupby(["arm", "tier"]).pattern_v2.value_counts(dropna=False).rename("n").reset_index()
    t["share"] = t.n / 150
    t.to_csv(f"{OUT}/P2_pattern_distribution.csv", index=False)
    gold = load_json(PURE150)
    opener = pd.Series([re.match(r"\s*(\w+)", g["text"]).group(1).lower() for g in gold])
    g = opener[opener.isin(["where", "when", "if", "while"])].value_counts().rename("n").reset_index()
    g.columns = ["opening_word", "n"]
    g.to_csv(f"{OUT}/P2_gold_opening_words.csv", index=False)
    w = t[t.pattern_v2 == WHERE].pivot(index="arm", columns="tier", values="n").reindex(columns=TIERS).fillna(0)
    log.append(f"P2: PURE originals opening with Where/When/If/While: {dict(zip(g.opening_word, g.n))}; "
               f"Optional-feature outputs per 150: {w.astype(int).to_dict(orient='index')}")


def p3_where_bound(df, log):
    d = df.copy()
    d["y"] = ((d.y == 1) & (d.pattern_v2 != WHERE)).astype(int)
    rates = d.groupby(["arm", "tier"]).y.mean().rename("rate_where_noncompliant").reset_index()
    rates.to_csv(f"{OUT}/P3_compliance_where_noncompliant.csv", index=False)
    fac = d[d.arm.isin(FACTORIAL)].copy()
    prim = A.primary_tests(A.gee(fac, A.FORMULA), "bound: every WHERE output counted non-compliant")
    prim.to_csv(f"{OUT}/P3_primary_tests_where_noncompliant.csv", index=False)
    rows = []
    for label, a, b in [("F_base - A0_name_only", "F_base", "A0_name_only")]:
        x = d[d.arm.isin([a, b])].copy()
        x["x"] = (x.arm == a).astype(float) - 0.5
        r2 = A.gee(x, "y ~ x * C(tier, Sum)")
        est, lo, hi, _, p = A.coef(r2, "x")
        rows.append(dict(contrast=label, tier="pooled", estimate=est, ci_lo=lo, ci_hi=hi, p=p))
        for t in TIERS:
            w = x[x.tier == t].pivot(index="item_id", columns="arm", values="y")
            rows.append(dict(contrast=label, tier=t, estimate=(w[a] - w[b]).mean(), ci_lo=np.nan, ci_hi=np.nan,
                             p=np.nan))
    ref = pd.DataFrame(rows)
    ref.to_csv(f"{OUT}/P3_reference_contrast_where_noncompliant.csv", index=False)
    e = prim[prim.test == "main effect: examples"].iloc[0]
    log.append(f"P3: with WHERE counted non-compliant: F_base - A0 pooled {100 * ref.estimate.iloc[0]:+.1f} pp "
               f"(nano {100 * ref.estimate.iloc[1]:+.1f}); examples main effect {100 * e.estimate:+.1f} pp "
               f"[{100 * e.ci_lo:.1f}, {100 * e.ci_hi:.1f}]")


def p4_fail_reasons(df, log):
    fac = df[df.arm.isin(FACTORIAL)].explode("fail_reasons").dropna(subset=["fail_reasons"])
    rows = []
    for f in ["e", "c", "r"]:
        for lev, lab in [(-0.5, "without"), (0.5, "with")]:
            c = fac[fac[f] == lev].fail_reasons.value_counts()
            for reason, n in c.items():
                rows.append(dict(ingredient=A.NAMES[f], level=lab, fail_reason=reason, n=int(n)))
    t = pd.DataFrame(rows)
    t.to_csv(f"{OUT}/P4_fail_reasons_by_ingredient.csv", index=False)
    pair = fac[fac.arm.isin(["F_base", "F_R"])].groupby(["arm", "fail_reasons"]).size().unstack(0).fillna(0).astype(int)
    pair.reset_index().to_csv(f"{OUT}/P4_fail_reasons_F_base_vs_F_R.csv", index=False)
    log.append(f"P4: fail reasons F_base vs F_R (all tiers): {pair.to_dict(orient='index')}")


def p5_mde(df, log):
    prim = pd.read_csv(f"{AN}/03_primary_tests.csv")
    z80 = norm.ppf(0.8)
    rows = []
    for r in prim[prim.test.str.startswith("main effect")].itertuples():
        se = (r.ci_hi - r.ci_lo) / (2 * 1.96)
        rows.append(dict(test=r.test, estimate=r.estimate, se=se, mde_nominal=(norm.ppf(0.975) + z80) * se,
                         mde_holm_strictest=(norm.ppf(1 - 0.05 / 12) + z80) * se))
    by = pd.read_csv(f"{AN}/03_factor_effects_by_tier.csv")
    for r in by.itertuples():
        se = (r.ci_hi - r.ci_lo) / (2 * 1.96)
        rows.append(dict(test=f"per tier: {r.factor}, {r.tier}", estimate=r.with_minus_without, se=se,
                         mde_nominal=(norm.ppf(0.975) + z80) * se, mde_holm_strictest=np.nan))
    t = pd.DataFrame(rows)
    t.to_csv(f"{OUT}/P5_minimum_detectable_effects.csv", index=False)
    fac = df[df.arm.isin(FACTORIAL)]
    all_ok = int((fac.groupby("item_id").y.mean() == 1).sum())
    pd.DataFrame([dict(items_compliant_in_all_24_factorial_outputs=all_ok, items=fac.item_id.nunique())]) \
        .to_csv(f"{OUT}/P5_items_at_ceiling.csv", index=False)
    m = t[t.test.str.startswith("main effect")]
    log.append("P5: MDE (80% power, alpha .05 / strictest Holm): " + "; ".join(
        f"{r.test.split(': ')[1]} {100 * r.mde_nominal:.1f} / {100 * r.mde_holm_strictest:.1f} pp" for r in m.itertuples())
               + f"; items compliant in all 24 factorial outputs: {all_ok}/150")


def p6_without_eirene_fun_7(df, log):
    fac = df[df.arm.isin(FACTORIAL) & (df.doc != "eirene_fun_7")].copy()
    prim = A.primary_tests(A.gee(fac, A.FORMULA), "excluding the 8 eirene_fun_7 items")
    prim.to_csv(f"{OUT}/P6_primary_without_eirene_fun_7.csv", index=False)
    e = prim[prim.test == "main effect: examples"].iloc[0]
    log.append(f"P6: without eirene_fun_7 ({fac.item_id.nunique()} items): examples {100 * e.estimate:+.1f} pp, "
               f"p_holm {e.p_holm:.3f}")


TOKEN = re.compile(r"\b\d+(?:[.,/]\d+)*\b|\b[A-Z][A-Z0-9]+(?:-[A-Z0-9]+)*\b")


def p7_contamination(df, log):
    gold = {g["id"]: g["text"] for g in load_json(PURE150)}
    mess = load_json(MESSIFIED)
    mess = {m["id"]: m.get("messified_text") or m.get("messified") or m.get("text") for m in mess}
    prompts = " ".join(open(os.path.join(ARM_DIR, f), encoding="utf-8").read() for f in os.listdir(ARM_DIR))
    cand = {}
    for i, g in gold.items():
        toks = {t for t in TOKEN.findall(g) if t.lower() not in mess[i].lower() and t not in prompts}
        if toks:
            cand[i] = toks
    rows = []
    for r in df.itertuples():
        for t in cand.get(r.item_id, ()):
            if isinstance(r.requirement_text, str) and re.search(rf"(?<![\w.]){re.escape(t)}(?![\w])", r.requirement_text):
                rows.append(dict(item_id=r.item_id, token=t, arm=r.arm, tier=r.tier, requirement=r.requirement_text))
    hits = pd.DataFrame(rows, columns=["item_id", "token", "arm", "tier", "requirement"])
    hits.to_csv(f"{OUT}/P7_contamination_hits.csv", index=False)
    pd.DataFrame([dict(item_id=i, tokens=" ".join(sorted(t))) for i, t in sorted(cand.items())]) \
        .to_csv(f"{OUT}/P7_contamination_candidates.csv", index=False)
    log.append(f"P7: items with a number or acronym absent from the input: {len(cand)}; outputs reproducing one: "
               f"{hits[['item_id', 'arm', 'tier']].drop_duplicates().shape[0]} of {len(df)} "
               f"({hits.item_id.nunique()} items; tokens {sorted(set(hits.token))})")


def merged_with_pattern(path, df):
    m = pd.read_csv(f"{path}/08_merged_scores.csv")
    pat = df[["item_id", "arm", "tier", "pattern_v2", "transcription", "register_leakage"]]
    return m.merge(pat, on=["item_id", "arm", "tier"], how="left", validate="one_to_one")


def p8_rater_pattern(df, log):
    m = merged_with_pattern(H_RET, df)
    ubi = (m.pattern_v2 == "ubiquitous").astype(int)
    rows = []
    for rater in ["R1", "R3"]:
        for c in CRIT:
            s = m[f"{c}_{rater}"]
            rho, p = spearmanr(s, ubi)
            rows.append(dict(rater=rater, criterion=c, spearman_with_ubiquitous=rho, p=p,
                             mean_ubiquitous=s[ubi == 1].mean(), mean_other=s[ubi == 0].mean(),
                             mean_where=s[m.pattern_v2 == WHERE].mean(),
                             share_le3_non_ubiquitous=(s[ubi == 0] <= 3).mean(),
                             share_ge4_ubiquitous=(s[ubi == 1] >= 4).mean()))
    t = pd.DataFrame(rows)
    t.to_csv(f"{OUT}/P8_rater_scores_by_pattern.csv", index=False)
    m.groupby(["arm", "pattern_v2"]).size().rename("n").reset_index().to_csv(f"{OUT}/P8_rated_patterns.csv", index=False)
    f1 = t[(t.rater == "R1") & (t.criterion == "faithfulness")].iloc[0]
    e3 = t[(t.rater == "R3") & (t.criterion == "ears_wellformedness")].iloc[0]
    share_ubi = m.groupby("arm").apply(lambda g: (g.pattern_v2 == "ubiquitous").mean(), include_groups=False)
    log.append(f"P8: R1 faithfulness vs Ubiquitous: rho {f1.spearman_with_ubiquitous:.2f}; non-Ubiquitous with F<=3 "
               f"{f1.share_le3_non_ubiquitous:.3f}; Ubiquitous with F>=4 {f1.share_ge4_ubiquitous:.3f} "
               f"(n Ubiquitous {int(ubi.sum())}); R3 EARS mean on WHERE {e3.mean_where:.2f} vs Ubiquitous "
               f"{e3.mean_ubiquitous:.2f}; Ubiquitous share by rated arm {share_ubi.round(3).to_dict()}")


def p10_unambiguity_without_copying(df, log):
    from analyze_human_study2 import fit, term  # pre-registered model, reused unchanged
    m = merged_with_pattern(H_RET, df)
    rows = []
    for label, d in [("all rated outputs", m),
                     ("without transcription or leakage", m[~(m.transcription.astype(bool) | m.register_leakage.astype(bool))])]:
        res = fit(d[["item_id", "arm", "tier"]].assign(score=d.unambiguity_mean))
        ci = res.conf_int()
        t = term("F_R")
        rows.append(dict(subset=label, n=len(d), estimate=res.params[t], ci_lo=ci.loc[t, 0], ci_hi=ci.loc[t, 1],
                         p=res.pvalues[t]))
    t = pd.DataFrame(rows)
    t.to_csv(f"{OUT}/P10_rules_unambiguity_without_copying.csv", index=False)
    log.append(f"P10: rules on Unambiguity: all {t.estimate.iloc[0]:+.2f}; without transcription/leakage "
               f"(n={t.n.iloc[1]}) {t.estimate.iloc[1]:+.2f} [{t.ci_lo.iloc[1]:.2f}, {t.ci_hi.iloc[1]:.2f}]")


def main():
    os.makedirs(OUT, exist_ok=True)
    df = A.load()
    log = [f"Input: {CHECKS}, {RAW_FULL}, {H_RET} (committed files)"]
    p1_cot_manipulation(log)
    p2_patterns(df, log)
    p3_where_bound(df, log)
    p4_fail_reasons(df, log)
    p5_mde(df, log)
    p6_without_eirene_fun_7(df, log)
    p7_contamination(df, log)
    p8_rater_pattern(df, log)
    p10_unambiguity_without_copying(df, log)
    with open(f"{OUT}/summary.md", "w", encoding="utf-8") as f:
        f.write("# Study 1: post hoc analyses (not planned)\n\nGenerated by analyze_post_hoc.py.\n\n"
                + "\n".join(f"- {l}" for l in log) + "\n")
    print("\n".join(log))


if __name__ == "__main__":
    main()
