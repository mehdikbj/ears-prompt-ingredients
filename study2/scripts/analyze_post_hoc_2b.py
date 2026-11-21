#!/usr/bin/env python3
"""
Post hoc analyses of Study 2b (paper: Study 2) and of Study 2 (paper: Study 1) re-scored for pattern fit.
NOT in study2b/ANALYSIS_PLAN.md: added on 2026-11-09 after the planned analyses, in response to an internal
review (logged in study2b/README.md, Deviations). Every contrast is post hoc and unadjusted.

  python3 study2b/scripts/analyze_post_hoc_2b.py     # run from the repository root; writes study2b/results/post_hoc/

Contrasts are item-level paired differences: for each of the 150 items, the mean outcome over all outputs on
one side minus the mean on the other side (averaging over the remaining factors and the three tiers), then a
t interval over items. With item clusters and a balanced design this reproduces the planned GEE marginal
estimates (e.g. examples on pattern fit, +11.0 pp [8.4, 13.5]).

PH1  admissible-set sizes, patterns per set, empty intersections, constant-Ubiquitous baseline
PH2  effects by input stratum: Ubiquitous not admissible (a condition is required) / Ubiquitous only / mixed
PH3  decomposition of pattern fit into P(compliant) and P(admissible | compliant), and Ubiquitous share
PH4  native - written; ingredient interactions; Study 1 CoT placebo; inputs whose outputs neither annotator
     had rated (Study 1 rating sample) vs the 50 rated ones; Study 1 base - name-only per tier
PH5  human ratings of Study 2b by pattern-fit status (GEE, item clusters), mean of the raters and per rater
PH6  per-point 95% intervals for the Study 2b tier figure (descriptive)
PH7  the planned contrasts (as paired differences) under each label set: union, intersection, each annotator
     alone, cue rule
PH8  inputs that require a condition: absolute pattern fit by arm and tier; chosen pattern vs the best pattern
     on which both annotators agree
PH9  test-retest on the four prompts that are byte-identical in Study 2 (temperature 0) and Study 2b (default)
PH10 checker compliance vs the human EARS well-formedness scores (150 rated Study 2b outputs)
PH11 the J_json self-reported pattern vs the pattern read from the opening keyword (Study 2)
PH12 minimum detectable effects (80% power) of the planned Study 2b contrasts
PH13 prompt, completion and reasoning tokens per call by reasoning level and tier (Study 2b)
"""
import json
import os
import sys
import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

warnings.filterwarnings("ignore")
ROOT = os.getcwd()
sys.path.insert(0, os.path.join(ROOT, "study2b", "pattern_fit"))
sys.path.insert(0, os.path.join(ROOT, "study2b", "scripts"))
import analyze_pattern_fit as PF  # noqa: E402  (read_sheet, admissible: the planned label handling, unchanged)
from s2bcommon import CHECKS as CHECKS_2B, PATTERN_FIT_DIR, S  # noqa: E402

OUT = "study2b/results/post_hoc"
CHECKS_1 = "study2/results/checks_study2.jsonl"
RATED_KEY_1 = "study2/results/human_eval_key_study2.jsonl"
HUMAN_2B = "study2b/human_eval/results/04_merged_scores.csv"
TIERS = ["gpt-5.4-nano", "gpt-5.4-mini", "gpt-5.4"]
CRITERIA = ["faithfulness", "unambiguity", "singularity", "ears_wellformedness", "equivalence"]


def tci(v):
    v = np.asarray(v, float)
    m, se = v.mean(), v.std(ddof=1) / np.sqrt(len(v))
    t = stats.t.ppf(0.975, len(v) - 1)
    return dict(estimate=m, ci_lo=m - t * se, ci_hi=m + t * se, p=2 * stats.t.sf(abs(m / se), len(v) - 1),
                n_items=len(v))


def paired(d, plus, minus, y):
    a = d[plus(d)].groupby("item_id")[y].mean()
    b = d[minus(d)].groupby("item_id")[y].mean()
    return (a - b).dropna()


def dd(d, f1, f2, l1, l2, y="fit"):
    g = d.groupby(["item_id", f1, f2])[y].mean().unstack([1, 2])
    return (g[(l1[0], l2[0])] - g[(l1[1], l2[0])]) - (g[(l1[0], l2[1])] - g[(l1[1], l2[1])])


def main():
    os.makedirs(OUT, exist_ok=True)
    a = PF.read_sheet(f"{PATTERN_FIT_DIR}/02_sheet_annotator_A.csv")
    b = PF.read_sheet(f"{PATTERN_FIT_DIR}/02_sheet_annotator_B.csv")
    A_, B_ = PF.admissible(a), PF.admissible(b)
    U = {i: A_[i] | B_[i] for i in A_}
    I = {i: A_[i] & B_[i] for i in A_}

    # PH1
    rows = []
    for name, sets in [("union", U), ("intersection", I), ("R3 (A)", A_), ("R1 (B)", B_)]:
        r = dict(set=name, n_items=len(sets), empty=sum(1 for s in sets.values() if not s),
                 constant_ubiquitous_fit=np.mean(["ubiquitous" in s for s in sets.values()]))
        for k in range(0, 7):
            r[f"size_{k}"] = sum(1 for s in sets.values() if len(s) == k)
        for p in PF.COLMAP.values():
            r[f"admissible_{p}"] = sum(p in s for s in sets.values())
        rows.append(r)
    pd.DataFrame(rows).to_csv(f"{OUT}/PH1_label_sets.csv", index=False)

    c2 = pd.DataFrame(S.read_jsonl(CHECKS_2B))
    c1 = pd.DataFrame(S.read_jsonl(CHECKS_1))
    for d in (c1, c2):
        d["comp"] = d.compliant_itt.astype(bool).astype(float)
        d["adm"] = [p in U[i] for p, i in zip(d.pattern_v2, d.item_id)]
        d["fit"] = (d.comp.astype(bool) & d.adm).astype(float)
        d["ubi"] = (d.pattern_v2 == "ubiquitous").astype(float)
    f1 = c1[c1.arm.str.startswith("F_")].copy()
    f1["C"] = f1.arm.str.contains("C").astype(int)

    # PH2
    strata = {"condition required (Ubiquitous not admissible)": {i for i, s in U.items() if "ubiquitous" not in s},
              "Ubiquitous only": {i for i, s in U.items() if s == {"ubiquitous"}}}
    strata["mixed"] = set(U) - strata["condition required (Ubiquitous not admissible)"] - strata["Ubiquitous only"]
    strata["all"] = set(U)
    rows = []
    for sname, items in strata.items():
        d = c2[c2.item_id.isin(items)]
        base = d[d.arm == "B_base_none"].fit.mean()
        for cname, pl, mi in [("examples", lambda x: x.E == 1, lambda x: x.E == 0),
                              ("rules", lambda x: x.R == 1, lambda x: x.R == 0),
                              ("written - none", lambda x: x.reasoning == "written", lambda x: x.reasoning == "none"),
                              ("native - none", lambda x: x.reasoning == "native", lambda x: x.reasoning == "none")]:
            rows.append(dict(study="Study 2b", stratum=sname, contrast=cname, base_prompt_fit=base,
                             **tci(paired(d, pl, mi, "fit"))))
        d = c1[c1.item_id.isin(items)]
        rows.append(dict(study="Study 2", stratum=sname, contrast="F_base - A0_name_only",
                         base_prompt_fit=d[d.arm == "F_base"].fit.mean(),
                         **tci(paired(d, lambda x: x.arm == "F_base", lambda x: x.arm == "A0_name_only", "fit"))))
    pd.DataFrame(rows).to_csv(f"{OUT}/PH2_strata.csv", index=False)

    # PH3
    rows = []
    for f in ["E", "R", "reasoning"]:
        for lv, g in c2.groupby(f):
            rows.append(dict(study="Study 2b", factor=f, level=lv, compliant=g.comp.mean(),
                             admissible_given_compliant=g[g.comp == 1].adm.mean(), fit=g.fit.mean(),
                             ubiquitous_share=g.ubi.mean()))
    for arm in ["F_base", "A0_name_only"]:
        for t in TIERS:
            g = c1[(c1.arm == arm) & (c1.model_alias == t)]
            rows.append(dict(study="Study 2", factor=arm, level=t, compliant=g.comp.mean(),
                             admissible_given_compliant=g[g.comp == 1].adm.mean(), fit=g.fit.mean(),
                             ubiquitous_share=g.ubi.mean()))
    pd.DataFrame(rows).to_csv(f"{OUT}/PH3_decomposition.csv", index=False)

    # PH4
    rated = {json.loads(l)["item_id"] for l in open(RATED_KEY_1)}
    assert len(rated) == 50
    rows = []
    for y in ["fit", "comp"]:
        rows.append(dict(analysis="native - written", study="Study 2b", subset="all", outcome=y,
                         **tci(paired(c2, lambda x: x.reasoning == "native", lambda x: x.reasoning == "written", y))))
    for nm, f1n, f2n, l1, l2 in [("E x R", "E", "R", (1, 0), (1, 0)),
                                 ("E x (written - none)", "E", "reasoning", (1, 0), ("written", "none")),
                                 ("E x (native - none)", "E", "reasoning", (1, 0), ("native", "none")),
                                 ("R x (written - none)", "R", "reasoning", (1, 0), ("written", "none")),
                                 ("R x (native - none)", "R", "reasoning", (1, 0), ("native", "none"))]:
        rows.append(dict(analysis=f"interaction {nm}", study="Study 2b", subset="all", outcome="fit",
                         **tci(dd(c2, f1n, f2n, l1, l2))))
    for y in ["fit", "comp"]:
        rows.append(dict(analysis="CoT placebo (C=1 - C=0)", study="Study 2", subset="all", outcome=y,
                         **tci(paired(f1, lambda x: x.C == 1, lambda x: x.C == 0, y))))
    for sub, items in [("inputs not in the Study 2 rating sample (100)", set(U) - rated),
                       ("inputs in the Study 2 rating sample (50)", rated)]:
        d = c2[c2.item_id.isin(items)]
        for cname, pl, mi in [("examples", lambda x: x.E == 1, lambda x: x.E == 0),
                              ("rules", lambda x: x.R == 1, lambda x: x.R == 0),
                              ("written - none", lambda x: x.reasoning == "written", lambda x: x.reasoning == "none"),
                              ("native - none", lambda x: x.reasoning == "native", lambda x: x.reasoning == "none")]:
            rows.append(dict(analysis=cname, study="Study 2b", subset=sub, outcome="fit", **tci(paired(d, pl, mi, "fit"))))
        d = c1[c1.item_id.isin(items)]
        rows.append(dict(analysis="F_base - A0_name_only", study="Study 2", subset=sub, outcome="fit",
                         **tci(paired(d, lambda x: x.arm == "F_base", lambda x: x.arm == "A0_name_only", "fit"))))
    for t in TIERS:
        d = c1[c1.model_alias == t]
        rows.append(dict(analysis="F_base - A0_name_only", study="Study 2", subset=t, outcome="fit",
                         **tci(paired(d, lambda x: x.arm == "F_base", lambda x: x.arm == "A0_name_only", "fit"))))
    pd.DataFrame(rows).to_csv(f"{OUT}/PH4_contrasts.csv", index=False)

    # PH5
    m = pd.read_csv(HUMAN_2B)
    key = c2.set_index(["item_id", "arm", "model_alias"])[["fit", "pattern_v2"]]
    m = m.join(key, on=["item_id", "arm", "tier"])
    assert m.fit.notna().all() and len(m) == 150
    rows = []
    for c in CRITERIA:
        for who, col in [("mean of R1 and R3", f"{c}_mean"), ("R1", f"{c}_R1"), ("R3", f"{c}_R3")]:
            x = m[["item_id", "fit", col]].dropna()
            res = sm.GEE.from_formula(f"{col} ~ fit", groups="item_id", data=x,
                                      cov_struct=sm.cov_struct.Independence()).fit()
            lo, hi = res.conf_int().loc["fit"]
            rows.append(dict(criterion=c, rater=who, mean_fit=x[x.fit == 1][col].mean(),
                             mean_misfit=x[x.fit == 0][col].mean(), n_fit=int((x.fit == 1).sum()),
                             n_misfit=int((x.fit == 0).sum()), estimate=res.params["fit"], ci_lo=lo, ci_hi=hi,
                             p=res.pvalues["fit"]))
    pd.DataFrame(rows).to_csv(f"{OUT}/PH5_human_by_fit.csv", index=False)

    # PH6
    rows = []
    for t in TIERS:
        for lv in ["none", "written", "native"]:
            v = c2[(c2.model_alias == t) & (c2.reasoning == lv)].groupby("item_id").fit.mean()
            r = tci(v)
            rows.append(dict(tier=t, reasoning=lv, rate=r["estimate"], ci_lo=r["ci_lo"], ci_hi=r["ci_hi"]))
    pd.DataFrame(rows).to_csv(f"{OUT}/PH6_tier_figure_ci.csv", index=False)

    # PH7: planned contrasts under every label set (item-level paired differences)
    inputs = {i["id"]: i["messified_text"] for i in S.load_json(S.MESSIFIED)}
    CUE = {i: ({p for p in s if p != "optional-feature"} | ({"optional-feature"} if PF.optional_cue(inputs[i]) else set()))
           or {"ubiquitous"} for i, s in U.items()}
    label_sets = [("union (primary)", U), ("intersection", I), ("R3 alone", A_), ("R1 alone", B_), ("cue rule", CUE)]
    f1e = c1[c1.arm.str.startswith("F_")].copy()
    f1e["E"] = f1e.arm.str.contains("E").astype(int)
    rows = []
    for lname, sets in label_sets:
        for d0, study in [(c2, "Study 2b"), (c1, "Study 2"), (f1e, "Study 2 factorial")]:
            d0["fit_s"] = (d0.comp.astype(bool).values & np.array([p in sets[i] for p, i in zip(d0.pattern_v2, d0.item_id)])).astype(float)
        for cname, d0, pl, mi in [("examples", c2, lambda x: x.E == 1, lambda x: x.E == 0),
                                  ("rules", c2, lambda x: x.R == 1, lambda x: x.R == 0),
                                  ("written - none", c2, lambda x: x.reasoning == "written", lambda x: x.reasoning == "none"),
                                  ("native - none", c2, lambda x: x.reasoning == "native", lambda x: x.reasoning == "none"),
                                  ("Study 2: F_base - A0_name_only", c1, lambda x: x.arm == "F_base", lambda x: x.arm == "A0_name_only"),
                                  ("Study 2: examples", f1e, lambda x: x.E == 1, lambda x: x.E == 0)]:
            rows.append(dict(label_set=lname, contrast=cname, **tci(paired(d0, pl, mi, "fit_s"))))
    pd.DataFrame(rows).to_csv(f"{OUT}/PH7_label_sets_contrasts.csv", index=False)

    # PH8: inputs that require a condition: absolute pattern fit, and chosen vs agreed best pattern
    cond = strata["condition required (Ubiquitous not admissible)"]
    d = c2[c2.item_id.isin(cond)]
    rows = [dict(arm=arm, tier="all", fit=g.fit.mean(), n=len(g)) for arm, g in d.groupby("arm")]
    rows += [dict(arm=arm, tier=t, fit=g.fit.mean(), n=len(g)) for (arm, t), g in d.groupby(["arm", "model_alias"])]
    rows += [dict(arm="all", tier="all", fit=d.fit.mean(), n=len(d))]
    pd.DataFrame(rows).to_csv(f"{OUT}/PH8_condition_inputs_fit.csv", index=False)
    best = {i: (a.loc[i, "best_pattern"].strip(), b.loc[i, "best_pattern"].strip()) for i in a.index}
    agreed = {i: x for i, (x, y) in best.items() if x == y}
    d = c2[c2.item_id.isin(agreed)].copy()
    d["best"] = d.item_id.map(agreed)
    d["chosen"] = np.where(d.comp == 1, d.pattern_v2.fillna("none"), "non-compliant")
    conf = pd.crosstab(d.best, d.chosen)
    conf.insert(0, "n_items", d.groupby("best").item_id.nunique())
    conf.to_csv(f"{OUT}/PH8_confusion_agreed_best.csv")

    # PH9: test-retest on prompts that are byte-identical in Study 2 (temperature 0) and Study 2b (default)
    pairs = {"F_base": "B_base_none", "F_E": "B_E_none", "F_R": "B_R_none", "F_ER": "B_ER_none"}
    k1 = c1[c1.arm.isin(pairs)].assign(arm2=lambda x: x.arm.map(pairs))
    m9 = k1.merge(c2, left_on=["item_id", "arm2", "model_alias"], right_on=["item_id", "arm", "model_alias"],
                  suffixes=("_1", "_2"))
    assert len(m9) == 1800
    from sklearn.metrics import cohen_kappa_score
    cell = m9.groupby(["arm_1", "model_alias"]).agg(fit_1=("fit_1", "mean"), fit_2=("fit_2", "mean"),
                                                     comp_1=("comp_1", "mean"), comp_2=("comp_2", "mean"))
    out9 = dict(n_pairs=len(m9),
                same_text=float((m9.normalized_text_1.fillna("") == m9.normalized_text_2.fillna("")).mean()),
                same_pattern=float((m9.pattern_v2_1.fillna("x") == m9.pattern_v2_2.fillna("x")).mean()),
                same_checker=float((m9.comp_1 == m9.comp_2).mean()),
                same_fit=float((m9.fit_1 == m9.fit_2).mean()),
                kappa_fit=float(cohen_kappa_score(m9.fit_1, m9.fit_2)),
                mean_abs_cell_diff_fit=float((cell.fit_1 - cell.fit_2).abs().mean()),
                max_abs_cell_diff_fit=float((cell.fit_1 - cell.fit_2).abs().max()),
                mean_abs_cell_diff_checker=float((cell.comp_1 - cell.comp_2).abs().mean()),
                max_abs_cell_diff_checker=float((cell.comp_1 - cell.comp_2).abs().max()),
                n_cells=len(cell))
    for f, nm in [("E", "examples"), ("R", "rules")]:
        for s_, sfx in [("1", "study2"), ("2", "study2b")]:
            has = m9["arm_1"].str.contains(f)
            pl, mi = m9[has], m9[~has]
            out9[f"{nm}_effect_fit_{sfx}"] = float(pl.groupby("item_id")[f"fit_{s_}"].mean().sub(
                mi.groupby("item_id")[f"fit_{s_}"].mean()).mean())
    pd.DataFrame([out9]).to_csv(f"{OUT}/PH9_test_retest.csv", index=False)
    cell.reset_index().to_csv(f"{OUT}/PH9_test_retest_cells.csv", index=False)


    # PH10: checker compliance vs human EARS well-formedness on the 150 rated Study 2b outputs
    rows = []
    mm = pd.read_csv(HUMAN_2B)
    mm["chk"] = mm.ears_v2_compliant.astype(str).str.lower().eq("true").astype(float)
    for who, col in [("mean of R1 and R3", "ears_wellformedness_mean"), ("R1", "ears_wellformedness_R1"),
                     ("R3", "ears_wellformedness_R3")]:
        x = mm[["item_id", "chk", col]].dropna()
        res = sm.GEE.from_formula(f"{col} ~ chk", groups="item_id", data=x,
                                  cov_struct=sm.cov_struct.Independence()).fit()
        lo, hi = res.conf_int().loc["chk"]
        rho, prho = stats.spearmanr(x.chk, x[col])
        rows.append(dict(rater=who, n_compliant=int((x.chk == 1).sum()), n_noncompliant=int((x.chk == 0).sum()),
                         mean_compliant=x[x.chk == 1][col].mean(), mean_noncompliant=x[x.chk == 0][col].mean(),
                         estimate=res.params["chk"], ci_lo=lo, ci_hi=hi, p=res.pvalues["chk"], spearman=rho,
                         share_noncompliant_scored_le3=float((x[x.chk == 0][col] <= 3).mean()),
                         share_compliant_scored_le3=float((x[x.chk == 1][col] <= 3).mean())))
    pd.DataFrame(rows).to_csv(f"{OUT}/PH10_checker_vs_human_ears.csv", index=False)

    # PH11: J_json self-reported pattern vs the pattern read from the opening keyword (Study 2, 450 outputs)
    j = c1[c1.arm == "J_json"].copy()
    norm = {"unwanted-behavior": "unwanted-behaviour"}
    j["self"] = j.self_reported_pattern.map(lambda v: norm.get(v, v) if isinstance(v, str) else None)
    jc = j[(j.comp == 1) & j["self"].notna()]
    rows = [dict(n_outputs=len(j), n_compliant_with_label=len(jc),
                 agree_with_keyword=float((jc["self"] == jc.pattern_v2).mean()),
                 self_where=int((j["self"] == "optional-feature").sum()),
                 keyword_where=int((j.pattern_v2 == "optional-feature").sum()),
                 self_admissible=float(np.mean([s_ in U[i] for s_, i in zip(jc["self"], jc.item_id)])),
                 keyword_admissible=float(np.mean([p in U[i] for p, i in zip(jc.pattern_v2, jc.item_id)])))]
    pd.DataFrame(rows).to_csv(f"{OUT}/PH11_json_self_label.csv", index=False)

    # PH12: minimum detectable effects (80% power) of the planned Study 2b contrasts, from their GEE intervals
    prim = pd.read_csv("study2b/results/analysis/02_primary_tests.csv")
    con = pd.read_csv("study2b/results/analysis/03_reasoning_contrasts.csv")
    PRIM_ = "pattern fit, union (primary)"
    z80 = stats.norm.ppf(0.8)
    rows = []
    for nm, r_ in [("examples", prim[(prim.outcome == PRIM_) & (prim.test == "main effect: examples")].iloc[0]),
                   ("rules", prim[(prim.outcome == PRIM_) & (prim.test == "main effect: rules")].iloc[0]),
                   ("written - none", con[(con.outcome == PRIM_) & (con.contrast == "written - none")].iloc[0]),
                   ("native - none", con[(con.outcome == PRIM_) & (con.contrast == "native - none")].iloc[0])]:
        se = (r_.ci_hi - r_.ci_lo) / (2 * stats.norm.ppf(0.975))
        k = 6 if nm in ("examples", "rules") else 2
        rows.append(dict(contrast=nm, se=se, mde_unadjusted=(stats.norm.ppf(0.975) + z80) * se,
                         mde_holm_worst=(stats.norm.ppf(1 - 0.025 / k) + z80) * se, holm_family_size=k))
    pd.DataFrame(rows).to_csv(f"{OUT}/PH12_minimum_detectable_effects.csv", index=False)

    # PH13: tokens per call by reasoning level and tier (Study 2b raw records)
    raw = pd.DataFrame(S.read_jsonl("study2b/results/raw_inference_2b.jsonl"))
    raw = raw[raw.error.isna()] if "error" in raw else raw
    for k_ in ["prompt_tokens", "completion_tokens", "reasoning_tokens"]:
        raw[k_] = raw.usage.map(lambda u, k_=k_: (u or {}).get(k_))
    tok = raw.groupby(["reasoning", "model_alias"])[["prompt_tokens", "completion_tokens", "reasoning_tokens"]] \
        .mean().reset_index()
    tok["n"] = raw.groupby(["reasoning", "model_alias"]).size().values
    tok.to_csv(f"{OUT}/PH13_tokens_per_call.csv", index=False)

    print(f"Wrote {OUT}/")


if __name__ == "__main__":
    main()
