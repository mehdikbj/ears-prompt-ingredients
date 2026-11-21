#!/usr/bin/env python3
"""
Build the paper's Results section and its figure from the committed analysis outputs.

  python3 study2/scripts/make_paper_results.py

Reads study2/results/analysis/ (pre-registered automatic analysis),
study2/results/human_analysis/ (pre-registered human analysis on the
sheets as returned) and study2/results/post_hoc/ (post hoc analyses, labelled as
such in the text). Writes paper/sections/s1_run.tex, s1_checker.tex and s1_where.tex (Study 1 in the
paper). Study 1 human ratings are not reported in the paper (see the protocol table).
Every number in the Results section comes from those files; the assertions below
stop the script if a sentence's wording no longer matches the numbers.
"""
import os

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

A = "study2/results/analysis"
H = "study2/results/human_analysis"  # sheets as returned (pre-registered)
P = "study2/results/post_hoc"
OUT_TEX = "paper/sections/results.tex"

TIERS = ["gpt-5.4-nano", "gpt-5.4-mini", "gpt-5.4"]
TIER_LABEL = {"gpt-5.4-nano": "nano", "gpt-5.4-mini": "mini", "gpt-5.4": "full"}
ARMS = ["A0_name_only", "F_base", "F_E", "F_C", "F_R", "F_EC", "F_ER", "F_CR", "F_ECR", "J_json"]
ARM_LABEL = {"A0_name_only": "Name-only", "F_base": "Base", "F_E": "Base+E", "F_C": "Base+C", "F_R": "Base+R",
             "F_EC": "Base+EC", "F_ER": "Base+ER", "F_CR": "Base+CR", "F_ECR": "Base+ECR", "J_json": "JSON"}
CRIT = ["faithfulness", "unambiguity", "singularity", "ears_wellformedness"]
CRIT_LABEL = {"faithfulness": "Faithfulness", "unambiguity": "Unambiguity", "singularity": "Singularity",
              "ears_wellformedness": "EARS well-formedness"}
COLORS = ["#2a78d6", "#eb6834", "#1baf7a"]  # categorical slots 1-3, validated all-pairs (light)
MARKERS = ["o", "s", "^"]


def _minus(s):
    """Typeset a leading minus sign as a math minus, not a hyphen."""
    return s.replace("-", "$-$")


def _fmt(x, d, sign):
    if abs(x) < 0.5 * 10 ** -d:  # avoid "-0.0" and "+0.0"
        return f"{0:.{d}f}"
    return _minus(f"{x:+.{d}f}" if sign else f"{x:.{d}f}")


def pp(x, sign=True):
    return _fmt(100 * x, 1, sign)


def ci_pp(lo, hi):
    return f"[{_fmt(100 * lo, 1, False)}, {_fmt(100 * hi, 1, False)}]"


def num(x, d=2, sign=False):
    return _fmt(x, d, sign)


def ci(lo, hi, d=2):
    """A bound that would round to zero but excludes it is printed with one more decimal (e.g. -0.002)."""
    def b(x):
        return _fmt(x, d + 1 if 0 < abs(x) < 0.5 * 10 ** -d else d, False)
    return f"[{b(lo)}, {b(hi)}]"


def p(x):
    if x < 0.001:
        return "$p<.001$"
    s = f"{x:.3f}".lstrip("0")
    return f"$p={s}$"


def ph(x):
    return p(x).replace("$p", "$p_{\\mathrm{Holm}}")


def row(df, **kw):
    m = df
    for k, v in kw.items():
        m = m[m[k] == v]
    assert len(m) == 1, (kw, len(m))
    return m.iloc[0]


def main():
    comp = pd.read_csv(f"{A}/01_compliance_by_arm_tier.csv")
    prim = pd.read_csv(f"{A}/03_primary_tests.csv")
    by_tier = pd.read_csv(f"{A}/03_factor_effects_by_tier.csv")
    inter = pd.read_csv(f"{A}/04_ingredient_interactions.csv")
    ref = pd.read_csv(f"{A}/05_reference_contrasts.csv")
    simple = pd.read_csv(f"{A}/06_simple_contrasts_per_tier.csv")
    sens = pd.read_csv(f"{A}/07_sensitivity.csv")
    cq = pd.read_csv(f"{A}/02_cochran_q_factorial.csv")
    sec = pd.read_csv(f"{A}/08_secondary_tests.csv")
    rates = pd.read_csv(f"{A}/08_secondary_rates.csv")
    fails = pd.read_csv(f"{A}/10_fail_reasons.csv")
    agr = pd.read_csv(f"{H}/01_agreement.csv")
    conf = pd.read_csv(f"{H}/02_confirmatory.csv")
    hsens = pd.read_csv(f"{H}/03_sensitivity_calibration_items.csv")
    auc = pd.read_csv(f"{H}/06_validity_auc.csv")
    merged = pd.read_csv(f"{H}/08_merged_scores.csv")

    # ---------------- numbers: pre-registered automatic analysis
    rate = {(r.arm, r.tier): r.rate for r in comp.itertuples()}
    ex, cot, ru = (row(prim, test=f"main effect: {f}") for f in ["examples", "chain-of-thought", "rules"])
    exT, cotT, ruT = (row(prim, test=f"{f} x tier") for f in ["examples", "chain-of-thought", "rules"])
    assert ex.estimate > 0 and ex.p_holm < 0.05
    assert ru.p_holm >= 0.05 and ru.p < 0.05
    assert cot.p_holm >= 0.05
    assert min(exT.p_holm, cotT.p_holm, ruT.p_holm) >= 0.05
    # Sensitivity analyses. Two of the five are identical to the primary analysis by construction in the
    # factorial conditions (no extraction failure, no output with more than one answer tag).
    identical = ["extraction failures excluded", "first-tag extraction rule"]
    for lab in identical:
        a = sens[(sens.analysis == lab) & (sens.test == "main effect: examples")].iloc[0]
        assert abs(a.estimate - ex.estimate) < 1e-9 and abs(a.p_holm - ex.p_holm) < 1e-9, lab
    sens_ex = sens[(sens.test == "main effect: examples") & ~sens.analysis.isin(identical)]
    n_sens = len(sens_ex)
    assert n_sens == 3 and (sens_ex.p_holm < 0.05).all() and (sens_ex.estimate > 0).all()
    assert (sens[sens.test == "main effect: rules"].p_holm >= 0.05).all()
    assert (sens[sens.test.str.endswith("x tier")].p_holm >= 0.05).all()
    xf = comp[comp.extraction_failures > 0]
    assert len(xf) == 1 and xf.iloc[0].arm == "J_json" and xf.iloc[0].tier == "gpt-5.4"
    n_xf = int(xf.iloc[0].extraction_failures)
    two_way = inter[~inter.test.str.contains("exploratory")]
    three = inter[inter.test.str.contains("exploratory")].iloc[0]
    base_a0 = ref[ref.test.str.startswith("shared base")].iloc[0]
    js = ref[ref.test.str.startswith("JSON")].iloc[0]
    a0_tier = {t: row(simple, tier=t, contrast="A0_name_only - F_base") for t in TIERS}
    assert a0_tier[TIERS[0]]["diff"] < a0_tier[TIERS[1]]["diff"] < a0_tier[TIERS[2]]["diff"] < 0
    assert base_a0.x_tier_p < 0.05 and js.p_holm >= 0.05
    cqd = {r.tier: r for r in cq.itertuples()}
    assert cqd[TIERS[0]].p < 0.05 and cqd[TIERS[1]].p < 0.05 and cqd[TIERS[2]].p >= 0.05
    fr = fails.groupby("fail_reasons").n.sum().sort_values(ascending=False)
    eff = {(r.tier, r.factor): r for r in by_tier.itertuples()}

    def sec_row(measure, test):
        return row(sec, analysis=measure, test=test)

    tr_ex, tr_ru = sec_row("transcription", "main effect: examples"), sec_row("transcription", "main effect: rules")
    tr_exT, tr_ruT = sec_row("transcription", "examples x tier"), sec_row("transcription", "rules x tier")
    lk_ex, lk_ru = sec_row("register_leakage", "main effect: examples"), sec_row("register_leakage", "main effect: rules")
    assert tr_ru.p_holm < 0.05 and tr_ex.p_holm < 0.05 and tr_ruT.p_holm < 0.05
    assert lk_ex.p_holm < 0.05 and lk_ru.p_holm >= 0.05
    tr_rates = rates[rates.measure == "transcription"].set_index(["arm", "tier"]).rate
    tr_fact = tr_rates[[a.startswith("F_") for a, _ in tr_rates.index]]
    tr_top = tr_fact.sort_values(ascending=False).head(2)
    assert {t for _, t in tr_top.index} == {"gpt-5.4-mini"}, tr_top
    assert {a for a, _ in tr_top.index} <= {"F_R", "F_CR", "F_ER", "F_ECR"}, tr_top
    lk_max = rates[rates.measure == "register_leakage"].rate.max()
    slot_max = rates[(rates.measure == "template_slot") & rates.arm.str.startswith("F_")].rate.max()
    assert slot_max == 0

    # ---------------- numbers: post hoc analyses (study2/results/post_hoc/, not pre-registered)
    p1 = pd.read_csv(f"{P}/P1_cot_manipulation_check.csv")
    p1t = pd.read_csv(f"{P}/P1_cot_tokens_by_tier.csv")
    cot_arms = ["F_C", "F_EC", "F_CR", "F_ECR"]
    p1c = p1[p1.arm.isin(cot_arms)]
    n_cot, n_cot_text = int(p1c.n.sum()), int(p1c.outputs_with_text_before_tag.sum())
    assert n_cot == 1800 and n_cot_text == 0 and int(p1.reasoning_tokens_total.sum()) == 0
    tok_gap = p1t.difference.abs().max()
    assert tok_gap < 1
    pat = pd.read_csv(f"{P}/P2_pattern_distribution.csv")
    where = pat[pat.pattern_v2 == "optional-feature"].set_index(["arm", "tier"]).n
    wn = lambda a, t: int(where.get((a, t), 0))  # noqa: E731
    noex = ["F_base", "F_C", "F_R", "F_CR"]
    withex = ["F_E", "F_EC", "F_ER", "F_ECR"]
    nano, mini, full = TIERS
    w_nano_noex = [wn(a, nano) for a in noex]
    w_nano_ex = [wn(a, nano) for a in withex]
    w_big_noex = [wn(a, t) for a in noex for t in (mini, full)]
    assert wn("A0_name_only", nano) == 0
    gold = pd.read_csv(f"{P}/P2_gold_opening_words.csv").set_index("opening_word").n
    assert int(gold.get("where", 0)) == 1
    p3 = pd.read_csv(f"{P}/P3_primary_tests_where_noncompliant.csv")
    p3_ex = row(p3, test="main effect: examples")
    p3r = pd.read_csv(f"{P}/P3_reference_contrast_where_noncompliant.csv")
    p3_ba = row(p3r, tier="pooled")
    p3_ba_nano = row(p3r, tier=nano)
    assert p3_ba.estimate < 0 < base_a0.estimate and p3_ex.estimate > 5 * ex.estimate
    p4 = pd.read_csv(f"{P}/P4_fail_reasons_F_base_vs_F_R.csv").set_index("fail_reasons")
    sh_b, sh_r = int(p4.loc["shall_count_not_1", "F_base"]), int(p4.loc["shall_count_not_1", "F_R"])
    mc_b, mc_r = int(p4.loc["misplaced_condition", "F_base"]), int(p4.loc["misplaced_condition", "F_R"])
    assert sh_r < sh_b / 2 and abs(mc_r - mc_b) <= 2
    p5 = pd.read_csv(f"{P}/P5_minimum_detectable_effects.csv")
    mde = {r.test: r for r in p5.itertuples()}
    mde_ex, mde_ru = mde["main effect: examples"], mde["main effect: rules"]
    assert ru.estimate < mde_ru.mde_nominal
    per_tier = p5[p5.test.str.startswith("per tier") & ~p5.test.str.contains("chain")]
    pt_lo, pt_hi = 100 * per_tier.mde_nominal.min(), 100 * per_tier.mde_nominal.max()
    ceil = pd.read_csv(f"{P}/P5_items_at_ceiling.csv").iloc[0]
    n_ceiling = int(ceil.items_compliant_in_all_24_factorial_outputs)
    p6 = row(pd.read_csv(f"{P}/P6_primary_without_eirene_fun_7.csv"), test="main effect: examples")
    assert p6.estimate > 0 and p6.p_holm < 0.05
    p8 = pd.read_csv(f"{P}/P8_rater_scores_by_pattern.csv")
    r1f = row(p8, rater="R1", criterion="faithfulness")
    r3e = row(p8, rater="R3", criterion="ears_wellformedness")
    r1e = row(p8, rater="R1", criterion="ears_wellformedness")
    assert r1f.share_le3_non_ubiquitous == 1.0 and r1f.spearman_with_ubiquitous > 0.9
    rated_pat = pd.read_csv(f"{P}/P8_rated_patterns.csv")
    n_ubi = int(rated_pat[rated_pat.pattern_v2 == "ubiquitous"].n.sum())
    n_rated = int(rated_pat.n.sum())
    n_ubi_ge4 = round(r1f.share_ge4_ubiquitous * n_ubi)
    ubi_share = {a: rated_pat[(rated_pat.arm == a) & (rated_pat.pattern_v2 == "ubiquitous")].n.sum() /
                 rated_pat[rated_pat.arm == a].n.sum() for a in ["F_base", "F_E"]}
    p10 = row(pd.read_csv(f"{P}/P10_rules_unambiguity_without_copying.csv"), subset="without transcription or leakage")
    assert p10.ci_hi < 0

    # ---------------- numbers: human evaluation, sheets as returned (pre-registered analysis)
    per_rater = {}
    for c in CRIT:
        for r in ["R1", "R3"]:
            g = merged.groupby("arm")[f"{c}_{r}"].mean()
            per_rater[(c, r, "F_E")] = g["F_E"] - g["F_base"]
            per_rater[(c, r, "F_R")] = g["F_R"] - g["F_base"]
    consistent = {(c, a): (per_rater[(c, "R1", a)] * per_rater[(c, "R3", a)] > 0) for c in CRIT for a in ["F_E", "F_R"]}

    def hc(c, a):
        return row(conf, criterion=c, contrast=f"{a} - F_base")

    u_r, s_r = hc("unambiguity", "F_R"), hc("singularity", "F_R")
    assert u_r.p_holm < 0.05 and u_r.estimate < 0 and consistent[("unambiguity", "F_R")]
    assert s_r.p_holm < 0.05 and s_r.estimate > 0 and consistent[("singularity", "F_R")]
    f_e, e_e = hc("faithfulness", "F_E"), hc("ears_wellformedness", "F_E")
    ag = {r.criterion: r for r in agr.itertuples()}
    au = {r.criterion: r for r in auc.itertuples()}
    sens_ok = all(row(hsens, criterion=c, contrast="F_R - F_base").p_holm < 0.05 for c in ["unambiguity", "singularity"])
    assert sens_ok
    assert f_e.p_holm < 0.05 and e_e.p_holm < 0.05
    assert abs(per_rater[("faithfulness", "R3", "F_E")]) < 0.1 and abs(per_rater[("ears_wellformedness", "R1", "F_E")]) < 0.1
    sig = conf[conf.p_holm < 0.05]
    named = {("unambiguity", "F_R - F_base"), ("singularity", "F_R - F_base"),
             ("faithfulness", "F_E - F_base"), ("ears_wellformedness", "F_E - F_base")}
    others = sig[[(r.criterion, r.contrast) not in named for r in sig.itertuples()]]
    others_max = others.estimate.abs().max() if len(others) else 0.0
    ing = {"F_E": "examples", "F_R": "rules"}
    others_names = " and ".join(f"{ing[r.contrast.split(' ')[0]]} on {CRIT_LABEL[r.criterion]}" for r in others.itertuples())
    assert len(others) == 2 and all(consistent[(r.criterion, r.contrast.split(" ")[0])] for r in others.itertuples())
    assert ag["singularity"].alpha_ci_lo > 0
    assert ag["unambiguity"].alpha_ci_lo < 0 < ag["unambiguity"].alpha_ci_hi
    assert ag["faithfulness"].alpha_ci_hi < 0 and ag["ears_wellformedness"].alpha_ci_hi < 0

    # ---------------- tables
    t_comp = ["\\begin{table}", "  \\caption{Study 1: EARS compliance by condition and tier (\\%; 150 items per cell; extraction "
              "failures count as non-compliant) and number of outputs, of 150, that use the Optional-feature pattern "
              "(WHERE), which the checker accepts whether or not it fits the input (post hoc count).}",
              "  \\label{tab:compliance}", "  \\footnotesize", "  \\setlength{\\tabcolsep}{3.5pt}",
              "  \\begin{tabular}{@{}lcccccc@{}}", "    \\toprule",
              "    & \\multicolumn{3}{c}{Compliance (\\%)} & \\multicolumn{3}{c}{WHERE outputs} \\\\",
              "    \\cmidrule(lr){2-4}\\cmidrule(l){5-7}",
              "    Condition & nano & mini & full & nano & mini & full \\\\", "    \\midrule"]
    for a in ARMS:
        t_comp.append(f"    {ARM_LABEL[a]} & " + " & ".join(pp(rate[(a, t)], False) for t in TIERS) + " & "
                      + " & ".join(str(wn(a, t)) for t in TIERS) + " \\\\")
        if a in ("F_base", "F_ECR"):
            t_comp.append("    \\midrule")
    t_comp += ["    \\bottomrule", "  \\end{tabular}", "\\end{table}"]

    short = {"ears_wellformedness": "EARS well-form."}
    t_agr = ["\\begin{table}", "  \\caption{Agreement between the two raters on the 450 rated outputs, with R3's sheet "
             "as returned before the comparison (Section~\\ref{sec:results-run}): Krippendorff's ordinal $\\alpha$ with a "
             "95\\% CI from resampling outputs, quadratic-weighted $\\kappa$, and exact and within-one agreement (\\%) "
             "with chance levels in parentheses. R1 is the first author.}",
             "  \\label{tab:agreement}", "  \\footnotesize", "  \\setlength{\\tabcolsep}{4pt}",
             "  \\begin{tabular}{@{}lccccc@{}}", "    \\toprule",
             "    Criterion & $\\alpha$ & 95\\% CI & $\\kappa_w$ & Exact & $\\pm1$ \\\\", "    \\midrule"]
    for c in CRIT:
        r = ag[c]
        t_agr.append(f"    {short.get(c, CRIT_LABEL[c])} & {num(r.alpha_ordinal)} & {ci(r.alpha_ci_lo, r.alpha_ci_hi)} & "
                     f"{num(r.kappa_quadratic)} & {100 * r.exact:.0f} ({100 * r.exact_chance:.0f}) & "
                     f"{100 * r.within_one:.0f} ({100 * r.within_one_chance:.0f}) \\\\")
    t_agr += ["    \\bottomrule", "  \\end{tabular}", "\\end{table}"]

    t_hum = ["\\begin{table*}", "  \\caption{Human-judged quality, exploratory: differences from F\\_base on the mean of the "
             "two raters (GEE, item clusters; Holm over eight), with each rater's own difference; R3's sheet as returned before the comparison. "
             "R1's Faithfulness scores follow the output's EARS pattern (Section~\\ref{sec:results-human}) and are not "
             "interpreted.}", "  \\label{tab:human}", "  \\small",
             "  \\begin{tabular}{@{}llccccc@{}}", "    \\toprule",
             "    Criterion & Contrast & Estimate [95\\% CI] & $p_{\\mathrm{Holm}}$ & R1 & R3 & Same sign \\\\", "    \\midrule"]
    for c in CRIT:
        for a in ["F_E", "F_R"]:
            r = hc(c, a)
            ph_s = "$<.001$" if r.p_holm < 0.001 else f"{r.p_holm:.3f}".lstrip("0")
            t_hum.append(f"    {CRIT_LABEL[c] if a == 'F_E' else ''} & {ARM_LABEL[a]}$-$Base & {num(r.estimate, sign=True)} "
                         f"{ci(r.ci_lo, r.ci_hi)} & {ph_s} & {num(per_rater[(c, 'R1', a)], sign=True)} & "
                         f"{num(per_rater[(c, 'R3', a)], sign=True)} & {'yes' if consistent[(c, a)] else 'no'} \\\\")
    t_hum += ["    \\bottomrule", "  \\end{tabular}", "\\end{table*}"]

    # ---------------- text fragments (Study 1 = repository study2/, exploratory), input into the Results section
    words = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
    frag = {}
    base_rates = [rate[("F_base", t_)] for t_ in TIERS]
    assert wn("J_json", nano) == 43
    frag["s1_run"] = (
        f"In Study~1, the chain-of-thought sentence produced no reasoning (post hoc check): none of the {n_cot:,} "
        f"outputs of its four conditions has any text before the answer tag, and no call used reasoning tokens. "
        f"{words[n_xf].capitalize()} JSON outputs on the full tier had no extractable requirement.")
    frag["s1_checker"] = (
        f"Scored by the checker, Study~1's base prompt already reaches {pp(min(base_rates), False)}\\% to "
        f"{pp(max(base_rates), False)}\\% across tiers (Table~\\ref{{tab:study1}}). Examples add {pp(ex.estimate)} pp "
        f"{ci_pp(ex.ci_lo, ex.ci_hi)} ({ph(ex.p_holm)}) and rules {pp(ru.estimate)} pp {ci_pp(ru.ci_lo, ru.ci_hi)} "
        f"({ph(ru.p_holm)}, no difference detected); no ingredient $\\times$ tier test is significant. The largest "
        f"difference is the base prompt over the Name-only prompt, {pp(base_a0.estimate)} pp "
        f"{ci_pp(base_a0.ci_lo, base_a0.ci_hi)} ({ph(base_a0.p_holm)}); JSON output makes no detectable difference "
        f"({pp(js.estimate)} pp).")
    frag["s1_where"] = (
        f"The checker accepts any opening WHERE clause. Without examples, nano uses WHERE in {min(w_nano_noex)} to "
        f"{max(w_nano_noex)} of 150 outputs per factorial condition (Table~\\ref{{tab:study1}}; {wn('J_json', nano)} "
        f"with the JSON prompt), and with examples in {min(w_nano_ex)} to {max(w_nano_ex)}. The larger tiers use it in "
        f"{min(w_big_noex)} to {max(w_big_noex)} outputs without examples (post hoc counts). Only one of the 150 "
        f"source requirements opens with ``Where''; Fig.~\\ref{{fig:example}} shows one such output.")
    for name, text in frag.items():
        with open(f"paper/sections/{name}.tex", "w", encoding="utf-8") as f:
            f.write("% Generated by study2/scripts/make_paper_results.py from the committed analysis outputs.\n"
                    "% Do not edit by hand: change the script and re-run it.\n" + text + "\n")
    print("Wrote paper/sections/s1_run.tex, s1_checker.tex and s1_where.tex (input into the Results section)")


if __name__ == "__main__":
    main()
