#!/usr/bin/env python3
"""
Build the paper's Study 2b results section, the Study 2 pattern-fit re-analysis subsection, their tables
and figure, from the committed Study 2b analysis outputs (planned analyses, ANALYSIS_PLAN.md).

  python3 study2b/scripts/make_paper_results_2b.py      # from the repository root

Writes paper/sections/study2b_results.tex (Study 2 in the paper; it includes the re-scoring of Study 1),
paper/sections/results_table_2b_*.tex, paper/sections/results_table_formfit.tex and
paper/figures/study2b_fit_by_tier.pdf. Every sentence that uses a number is guarded by an assertion.
Per-tier rates are descriptive (the plan describes significant x tier tests by per-tier effects).
"""
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyze_study2b as Z  # noqa: E402

A = "study2b/results/analysis"
P = "study2b/pattern_fit/results"
H = "study2b/human_eval/results"
S2 = "study2/results/analysis"
PH = "study2b/results/post_hoc"
TIERS = ["gpt-5.4-nano", "gpt-5.4-mini", "gpt-5.4"]
TL = {"gpt-5.4-nano": "nano", "gpt-5.4-mini": "mini", "gpt-5.4": "full"}
LEVELS = ["none", "written", "native"]
CRIT = ["faithfulness", "unambiguity", "singularity", "ears_wellformedness", "equivalence"]
CL = {"faithfulness": "Faithfulness", "unambiguity": "Unambiguity", "singularity": "Singularity",
      "ears_wellformedness": "EARS well-form.", "equivalence": "Equivalence"}
COLORS = ["#2a78d6", "#eb6834", "#1baf7a"]
MARKERS = ["o", "s", "^"]
UNION, PRIM = "union (primary)", "pattern fit, union (primary)"
CHK = "checker compliance (secondary)"


def _m(s):
    return s.replace("-", "$-$")


def fmt(x, d=1, sign=True):
    if abs(x) < 0.5 * 10 ** -d:
        return f"{0:.{d}f}"
    return _m(f"{x:+.{d}f}" if sign else f"{x:.{d}f}")


def pp(x, sign=True):
    return fmt(100 * x, 1, sign)


def cip(lo, hi):
    return f"[{fmt(100 * lo, 1, False)}, {fmt(100 * hi, 1, False)}]"


def ci2(lo, hi):
    def b(x):
        return fmt(x, 3 if 0 < abs(x) < 0.005 else 2, False)
    return f"[{b(lo)}, {b(hi)}]"


def ph(p):
    return "$p_{\\mathrm{Holm}}<.001$" if p < 0.001 else f"$p_{{\\mathrm{{Holm}}}}={p:.3f}".replace("=0.", "=.") + "$"


def phs(p):
    return "$<.001$" if p < 0.001 else f"{p:.3f}".lstrip("0")


def row(df, **kw):
    m = df
    for k, v in kw.items():
        m = m[m[k] == v]
    assert len(m) == 1, (kw, len(m))
    return m.iloc[0]


def main():
    man = pd.read_csv(f"{A}/01_manipulation_checks.csv")
    prim = pd.read_csv(f"{A}/02_primary_tests.csv")
    con = pd.read_csv(f"{A}/03_reasoning_contrasts.csv")
    sens = pd.read_csv(f"{A}/06_sensitivity.csv")
    agrP = pd.read_csv(f"{P}/01_agreement.csv")
    cue = pd.read_csv(f"{P}/01b_optional_feature_humans_vs_cue_rule.csv").iloc[0]
    s2t = pd.read_csv(f"{P}/03_study2_primary_tests_pattern_fit.csv")
    s2ref = pd.read_csv(f"{P}/04_study2_base_vs_name_only_pattern_fit.csv")
    s2rates = pd.read_csv(f"{P}/02_study2_pattern_fit_rates.csv")
    s2prim = pd.read_csv(f"{S2}/03_primary_tests.csv")
    s2refc = pd.read_csv(f"{S2}/05_reference_contrasts.csv")
    agrH = pd.read_csv(f"{H}/01_agreement.csv")
    conH = pd.read_csv(f"{H}/02_contrasts.csv")
    conH3 = pd.read_csv(f"{H}/03_contrasts_R3_only.csv")
    mH = pd.read_csv(f"{H}/04_merged_scores.csv")
    ph1 = pd.read_csv(f"{PH}/PH1_label_sets.csv").set_index("set")
    ph2 = pd.read_csv(f"{PH}/PH2_strata.csv")
    ph3 = pd.read_csv(f"{PH}/PH3_decomposition.csv")
    ph4 = pd.read_csv(f"{PH}/PH4_contrasts.csv")
    ph5 = pd.read_csv(f"{PH}/PH5_human_by_fit.csv")
    ph6 = pd.read_csv(f"{PH}/PH6_tier_figure_ci.csv")
    ph7 = pd.read_csv(f"{PH}/PH7_label_sets_contrasts.csv")
    ph8f = pd.read_csv(f"{PH}/PH8_condition_inputs_fit.csv")
    ph8c = pd.read_csv(f"{PH}/PH8_confusion_agreed_best.csv").set_index("best")
    ph9 = pd.read_csv(f"{PH}/PH9_test_retest.csv").iloc[0]
    c1chk = Z.load_checks("study2/results/checks_study2.jsonl")
    ph10 = pd.read_csv(f"{PH}/PH10_checker_vs_human_ears.csv").set_index("rater")
    ph11 = pd.read_csv(f"{PH}/PH11_json_self_label.csv").iloc[0]
    ph12 = pd.read_csv(f"{PH}/PH12_minimum_detectable_effects.csv")
    ph13 = pd.read_csv(f"{PH}/PH13_tokens_per_call.csv")
    ph14 = pd.read_csv(f"{PH}/PH14_examples_vs_other_ingredients.csv")

    # ---------------- descriptive data from the checks and the labels
    d = Z.load_checks("study2b/results/checks_2b.jsonl")
    sets = Z.admissible_sets("study2b/pattern_fit")
    d["fit"] = Z.fit_flag(d, sets[UNION]).values
    d["where"] = (d.pattern_v2 == "optional-feature").astype(int)
    fit_rt = d.pivot_table(index="reasoning", columns="tier", values="fit", aggfunc="mean")
    fit_et = d.pivot_table(index="E", columns="tier", values="fit", aggfunc="mean")
    base = d[(d.E == 0) & (d.R == 0)]
    where_rt = base.pivot_table(index="reasoning", columns="tier", values="where", aggfunc="mean")
    by_arm = d.groupby("arm").fit.mean()
    chk_cells = d.groupby(["arm", "tier"]).compliant_itt.mean()
    n_xf = int((~d.extraction_ok).sum())
    xf_tiers = set(d[~d.extraction_ok].tier)
    assert n_xf == 5 and xf_tiers == {"gpt-5.4-nano"}

    # ---------------- manipulation checks
    mm = {(r.reasoning, r.tier): r for r in man.itertuples()}
    assert man.check_passed.all()
    w_min = min(mm[("written", t)].share_ge15_words_before_tag for t in TIERS)
    n_min = min(mm[("native", t)].share_reasoning_tokens for t in TIERS)
    none_txt = max(mm[("none", t)].share_any_text_before_tag for t in TIERS)
    none_rt = max(mm[("none", t)].share_reasoning_tokens for t in TIERS)
    assert w_min >= 0.9 and n_min >= 0.9 and none_txt <= 0.05 and none_rt == 0
    raw_rt = d[d.reasoning == "native"].groupby("tier").reasoning_tokens.mean()
    assert raw_rt.idxmin() == "gpt-5.4-nano"

    # ---------------- primary tests (pattern fit) and checker (secondary)
    def t(outcome, test):
        return row(prim, outcome=outcome, test=test)

    def c(outcome, lev):
        return row(con, outcome=outcome, contrast=f"{lev} - none")

    ex, ru, rs = (t(PRIM, f"main effect: {x}") for x in ["examples", "rules", "reasoning (2 df)"])
    exT, ruT, rsT = (t(PRIM, f"{x} x tier") for x in ["examples", "rules", "reasoning"])
    wr, na = c(PRIM, "written"), c(PRIM, "native")
    for x in (ex, ru, rs, exT, rsT, wr, na):
        assert x.p_holm < 0.05
    assert ruT.p_holm >= 0.05 and ex.estimate > 0 and ru.estimate > 0 and 0 < wr.estimate < na.estimate
    # robustness rule (ANALYSIS_PLAN.md): direction and Holm-significance under logit, document clustering,
    # without the two items, and with the intersection set
    rob = ["logit link", "clusters = source document, bias-reduced, t/F", "excluding PURE-014, PURE-126"]
    for lab in rob:
        s = sens[(sens.analysis == lab) & (sens.outcome == PRIM)]
        for test in ["main effect: examples", "main effect: rules", "main effect: reasoning (2 df)"]:
            r_ = row(s, test=test)
            assert r_.p_holm < 0.05 and (np.isnan(r_.estimate) or r_.estimate > 0), (lab, test)
    for lab in ["admissible set: intersection", "admissible set: cue rule for optional feature"]:
        s = sens[sens.analysis == lab]
        for test in ["main effect: examples", "main effect: rules", "main effect: reasoning (2 df)"]:
            r_ = row(s, test=test)
            assert r_.p_holm < 0.05 and (np.isnan(r_.estimate) or r_.estimate > 0), (lab, test)
        for lev in ["written", "native"]:
            r_ = row(s, contrast=f"{lev} - none")
            assert r_.p_holm < 0.05 and r_.estimate > 0, (lab, lev)
    for lab in rob[1:]:
        for lev in ["written", "native"]:
            r_ = row(sens[(sens.analysis == lab) & (sens.outcome == PRIM)], contrast=f"{lev} - none")
            assert r_.p_holm < 0.05 and r_.estimate > 0
    cex, cru = t(CHK, "main effect: examples"), t(CHK, "main effect: rules")
    cwr, cna = c(CHK, "written"), c(CHK, "native")
    assert cwr.p_holm >= 0.05 and cna.p_holm >= 0.05 and cex.p_holm < 0.05 and cru.p_holm < 0.05
    best, worst = by_arm.idxmax(), by_arm.idxmin()
    assert best == "B_ER_native" and worst == "B_base_none"

    # per-tier descriptive
    e_gain = {tt: fit_et.loc[1, tt] - fit_et.loc[0, tt] for tt in TIERS}
    assert min(e_gain, key=e_gain.get) == "gpt-5.4-mini"
    assert fit_rt.loc["written", "gpt-5.4-mini"] < fit_rt.loc["none", "gpt-5.4-mini"] < fit_rt.loc["native", "gpt-5.4-mini"]
    for tt in ["gpt-5.4-nano", "gpt-5.4"]:
        assert fit_rt.loc["none", tt] < fit_rt.loc["written", tt] < fit_rt.loc["native", tt]
    wn = where_rt["gpt-5.4-nano"]
    assert wn["none"] > wn["written"] > wn["native"]

    # ---------------- part P labels
    ag = {r.measure: r for r in agrP.itertuples()}
    kap = {k.replace("admissible: ", ""): v.cohen_kappa for k, v in ag.items() if k.startswith("admissible")}
    kmin, kmax = min(kap, key=kap.get), max(kap, key=kap.get)
    n_opt = int(cue.items_optional_by_union)
    lab_a = pd.read_csv("study2b/pattern_fit/02_sheet_annotator_A.csv")
    lab_b = pd.read_csv("study2b/pattern_fit/02_sheet_annotator_B.csv")
    n_opt_a, n_opt_b = int(lab_a.adm_optional_feature.sum()), int(lab_b.adm_optional_feature.sum())

    # ---------------- Study 2 re-analysis on pattern fit
    s2u = s2t[s2t.set == UNION]
    s2ex, s2ru = row(s2u, test="main effect: examples"), row(s2u, test="main effect: rules")
    s2exT = row(s2u, test="examples x tier")
    s2ba = row(s2ref, set=UNION)
    s2ba_i, s2ba_c = row(s2ref, set="intersection"), row(s2ref, set="cue rule for optional feature")
    pex, pru = row(s2prim, test="main effect: examples"), row(s2prim, test="main effect: rules")
    pba = s2refc[s2refc.test.str.startswith("shared base")].iloc[0]
    assert s2ba.p >= 0.05 and s2ba.estimate < 0 < pba.estimate and s2ex.p_holm < 0.05 and s2ru.p_holm < 0.05
    assert s2ba_c.p >= 0.05 and s2ba_i.estimate < 0
    r2 = s2rates[s2rates.set == UNION].set_index(["arm", "tier"]).rate
    r1chk = pd.read_csv(f"{S2}/01_compliance_by_arm_tier.csv").set_index(["arm", "tier"]).rate
    assert r1chk.xs("gpt-5.4-nano", level="tier").idxmax() == "F_R"
    for tt in ["gpt-5.4-nano", "gpt-5.4"]:
        assert r2[("A0_name_only", tt)] > r2[("F_base", tt)]
    for tt in TIERS:
        assert r2[("F_E", tt)] > r2[("F_base", tt)]

    # ---------------- part H
    aH = {r.criterion: r for r in agrH.itertuples()}
    assert (conH.p_holm >= 0.05).all() and (conH3.p_holm >= 0.05).all()
    minp = conH.p_holm.min()
    arm_means = mH.groupby("arm")[[f"{c_}_mean" for c_ in CRIT]].mean()
    floor = arm_means.values.min()
    eq4 = (mH.equivalence_mean >= 4).mean()
    eq55 = ((mH.equivalence_R1 == 5) & (mH.equivalence_R3 == 5)).mean()
    assert floor >= 4.0 and aH["unambiguity"].alpha_ci_hi < 0 and aH["faithfulness"].alpha_ci_hi < 0
    n_h = len(mH)
    n_pts = d.groupby(["tier", "reasoning"]).size()
    assert n_pts.nunique() == 1
    n_pt = int(n_pts.iloc[0])
    assert n_pt == 600
    tier_items = mH.groupby("tier").item_id.nunique()

    # ---------------- figure: pattern fit by reasoning level and tier
    plt.rcParams.update({"font.size": 8, "pdf.fonttype": 42, "axes.spines.top": False, "axes.spines.right": False})
    fig, ax = plt.subplots(figsize=(3.33, 2.3))
    base_u = ph1.loc["union"].constant_ubiquitous_fit
    ax.axhline(100 * base_u, color="#8a8984", lw=0.8, ls="--", zorder=0, label="always Ubiquitous")
    for j, tt in enumerate(TIERS):
        for k, lv in enumerate(LEVELS):
            r_ = row(ph6, tier=tt, reasoning=lv)
            assert abs(r_.rate - fit_rt.loc[lv, tt]) < 1e-9
            ax.errorbar(k + (j - 1) * 0.17, 100 * r_.rate, yerr=[[100 * (r_.rate - r_.ci_lo)], [100 * (r_.ci_hi - r_.rate)]],
                        fmt=MARKERS[j], color=COLORS[j], ms=4.5, elinewidth=0.9, capsize=1.5,
                        label=TL[tt] if k == 0 else None)
    ax.set_ylim(50, 100)
    ax.set_xlim(-0.5, 2.5)
    ax.set_xticks(range(3))
    ax.set_xticklabels(["no reasoning", "written", "native"])
    ax.set_ylabel("Pattern fit (%)")
    ax.grid(axis="y", color="#e4e3df", lw=0.6)
    ax.set_axisbelow(True)
    h_, l_ = ax.get_legend_handles_labels()
    order = [l_.index(TL[tt]) for tt in TIERS] + [l_.index("always Ubiquitous")]
    ax.legend([h_[i] for i in order], [l_[i] for i in order], frameon=False, ncol=4, fontsize=6.5,
              loc="lower center", bbox_to_anchor=(0.5, 1.0), handletextpad=0.3, columnspacing=0.9, handlelength=1.6)
    fig.tight_layout()
    fig.savefig("paper/figures/study2b_fit_by_tier.pdf", metadata={"CreationDate": None, "ModDate": None})

    # ---------------- tables
    tab_man = ["\\begin{table}", "  \\caption{Study 2 manipulation checks per reasoning level and tier (600 outputs per "
               "cell): share of outputs with text before the answer tag (at least 15 words for written and native "
               "reasoning, any text for none), and share of calls that used reasoning tokens. All checks passed "
               "(thresholds in Section~\\ref{sec:methods-2b}).}",
               "  \\label{tab:2b-manip}", "  \\footnotesize", "  \\setlength{\\tabcolsep}{4pt}",
               "  \\begin{tabular}{@{}lcccccc@{}}", "    \\toprule",
               "    & \\multicolumn{3}{c}{Text before tag (\\%)} & \\multicolumn{3}{c}{Reasoning tokens (\\%)} \\\\",
               "    \\cmidrule(lr){2-4}\\cmidrule(l){5-7}", "    Reasoning & nano & mini & full & nano & mini & full \\\\",
               "    \\midrule"]
    for lv, lab in [("none", "none"), ("written", "written"), ("native", "native")]:
        col = "share_any_text_before_tag" if lv == "none" else "share_ge15_words_before_tag"
        tab_man.append(f"    {lab} & " + " & ".join(f"{100 * getattr(mm[(lv, tt)], col):.1f}" for tt in TIERS) + " & "
                       + " & ".join(f"{100 * mm[(lv, tt)].share_reasoning_tokens:.1f}" for tt in TIERS) + " \\\\")
    tab_man += ["    \\bottomrule", "  \\end{tabular}", "\\end{table}"]

    def line(name, fitrow, chkrow):
        return (f"    {name} & {pp(fitrow.estimate)} {cip(fitrow.ci_lo, fitrow.ci_hi)} & {phs(fitrow.p_holm)} & "
                f"{pp(chkrow.estimate)} {cip(chkrow.ci_lo, chkrow.ci_hi)} & {phs(chkrow.p_holm)} \\\\")

    tab_eff = ["\\begin{table}", "  \\caption{Study 2 effects in percentage points: pattern fit (primary; "
               "union of the two annotators' admissible patterns) and checker compliance alone (secondary). GEE, item "
               "clusters; $p_{\\mathrm{H}}$: Holm-adjusted, over the primary family (six tests, "
               "Section~\\ref{sec:methods-stats}) and over the two reasoning contrasts.}",
               "  \\label{tab:2b-effects}", "  \\footnotesize", "  \\setlength{\\tabcolsep}{3pt}",
               "  \\begin{tabular}{@{}lcccc@{}}", "    \\toprule",
               "    & \\multicolumn{2}{c}{Pattern fit} & \\multicolumn{2}{c}{Checker only} \\\\",
               "    \\cmidrule(lr){2-3}\\cmidrule(l){4-5}", "    Effect & Est.\\ [95\\% CI] & $p_{\\mathrm{H}}$ & "
               "Est.\\ [95\\% CI] & $p_{\\mathrm{H}}$ \\\\", "    \\midrule",
               line("Examples", ex, cex), line("Rules", ru, cru), line("Written $-$ none", wr, cwr),
               line("Native $-$ none", na, cna), "    \\bottomrule", "  \\end{tabular}", "\\end{table}"]

    def frow(name, plan, fit, plan_p, fit_p, dag=False):
        return (f"    {name} & {pp(plan.estimate)} {cip(plan.ci_lo, plan.ci_hi)} & {phs(plan_p)} & "
                f"{pp(fit.estimate)} {cip(fit.ci_lo, fit.ci_hi)} & {phs(fit_p)}{'$^{\\dagger}$' if dag else ''} \\\\")

    tab_ff = ["\\begin{table}", "  \\caption{Study 1 re-scored: planned checker-compliance estimates and the same "
              "contrasts on pattern-fit compliance (union of the annotators' labels), in percentage points. "
              "$p_{\\mathrm{H}}$: Holm-adjusted; $^{\\dagger}$unadjusted (a single contrast).}",
              "  \\label{tab:formfit}", "  \\footnotesize", "  \\setlength{\\tabcolsep}{3pt}",
              "  \\begin{tabular}{@{}lcccc@{}}", "    \\toprule",
              "    & \\multicolumn{2}{c}{Checker (planned)} & \\multicolumn{2}{c}{Pattern fit} \\\\",
              "    \\cmidrule(lr){2-3}\\cmidrule(l){4-5}", "    Contrast & Est.\\ [95\\% CI] & $p_{\\mathrm{H}}$ & "
              "Est.\\ [95\\% CI] & $p_{\\mathrm{H}}$ \\\\", "    \\midrule",
              frow("Base $-$ Name-only", pba, s2ba, pba.p_holm, s2ba.p, dag=True),
              frow("Examples", pex, s2ex, pex.p_holm, s2ex.p_holm), frow("Rules", pru, s2ru, pru.p_holm, s2ru.p_holm),
              "    \\bottomrule", "  \\end{tabular}", "\\end{table}"]

    tab_h = ["\\begin{table*}", f"  \\caption{{Study 2 human ratings of {n_h} outputs (exploratory; R1 is "
             "\\AuthorRef): agreement between R1 and R3 (Krippendorff's ordinal $\\alpha$ with 95\\% CI, "
             "quadratic-weighted Cohen's $\\kappa$, Spearman's $\\rho$, exact and within-one agreement with their "
             "chance levels) and mean-score differences from no reasoning with 95\\% CI (GEE, item clusters; Holm "
             "over ten). No difference is Holm-significant.}",
             "  \\label{tab:2b-human}", "  \\footnotesize", "  \\setlength{\\tabcolsep}{4pt}",
             "  \\begin{tabular}{@{}lccccccc@{}}", "    \\toprule",
             "    & \\multicolumn{5}{c}{Agreement} & \\multicolumn{2}{c}{Difference from none} \\\\",
             "    \\cmidrule(lr){2-6}\\cmidrule(l){7-8}",
             "    Criterion & $\\alpha$ [95\\% CI] & $\\kappa_w$ & $\\rho$ & Exact (chance) & Within one (chance) & "
             "Written & Native \\\\", "    \\midrule"]
    for c_ in CRIT:
        w_, n_ = (row(conH, criterion=c_, contrast=f"B_base_{lv} - B_base_none") for lv in ["written", "native"])
        a_ = aH[c_]
        tab_h.append(f"    {CL[c_]} & {fmt(a_.alpha_ordinal, 2, False)} {ci2(a_.alpha_ci_lo, a_.alpha_ci_hi)} & "
                     f"{fmt(a_.kappa_quadratic, 2, False)} & {fmt(a_.spearman_rho, 2, False)} & "
                     f"{100 * a_.exact:.0f}\\% ({100 * a_.exact_chance:.0f}\\%) & "
                     f"{100 * a_.within_one:.0f}\\% ({100 * a_.within_one_chance:.0f}\\%) & "
                     f"{fmt(w_.estimate, 2)} {ci2(w_.ci_lo, w_.ci_hi)} & {fmt(n_.estimate, 2)} {ci2(n_.ci_lo, n_.ci_hi)} \\\\")
    tab_h += ["    \\bottomrule", "  \\end{tabular}", "\\end{table*}"]
    kw_lo, kw_hi = min(aH[c_].kappa_quadratic for c_ in CRIT), max(aH[c_].kappa_quadratic for c_ in CRIT)
    rho_lo, rho_hi = min(aH[c_].spearman_rho for c_ in CRIT), max(aH[c_].spearman_rho for c_ in CRIT)
    ex_gain = max(aH[c_].exact - aH[c_].exact_chance for c_ in CRIT)
    w1_gain = max(aH[c_].within_one - aH[c_].within_one_chance for c_ in CRIT)
    assert 0 < ex_gain < 0.15 and 0 < w1_gain < 0.1

    # ---------------- post hoc (study2b/scripts/analyze_post_hoc_2b.py)
    U1 = ph1.loc["union"]
    I1 = ph1.loc["intersection"]
    assert U1["empty"] == 0 and I1["empty"] == 25 and U1.admissible_ubiquitous == 106
    n_multi = int(U1.size_3 + U1.size_4)
    assert int(U1.size_1 + U1.size_2) + n_multi == 150 and U1.size_5 == 0 and U1.size_6 == 0
    assert kmin == "complex"
    CR, UO, MX = "condition required (Ubiquitous not admissible)", "Ubiquitous only", "mixed"
    def st(study, stratum, contrast):
        return row(ph2, study=study, stratum=stratum, contrast=contrast)
    CON = [("examples", "Examples"), ("rules", "Rules"), ("written - none", "Written $-$ none"),
           ("native - none", "Native $-$ none")]
    # consistency with the planned GEE estimates on all items
    for k_, plan_ in [("examples", ex), ("rules", ru), ("written - none", wr), ("native - none", na)]:
        assert abs(st("Study 2b", "all", k_).estimate - plan_.estimate) < 1e-9
    assert abs(st("Study 2", "all", "F_base - A0_name_only").estimate - s2ba.estimate) < 1e-9
    cr = {k_: st("Study 2b", CR, k_) for k_, _ in CON}
    uo = {k_: st("Study 2b", UO, k_) for k_, _ in CON}
    assert all(v.ci_lo > 0 for v in uo.values())
    assert cr["native - none"].ci_lo > 0 and all(cr[k_].ci_lo < 0 < cr[k_].ci_hi for k_ in ["examples", "rules", "written - none"])
    s1cr, s1uo = st("Study 2", CR, "F_base - A0_name_only"), st("Study 2", UO, "F_base - A0_name_only")
    assert s1cr.ci_lo > 0 and s1uo.ci_hi < 0
    n_cr, n_uo, n_mx = int(cr["examples"].n_items), int(uo["examples"].n_items), int(st("Study 2b", MX, "examples").n_items)
    assert n_cr + n_uo + n_mx == 150
    ph3["level"] = ph3["level"].astype(str)
    e0, e1 = (row(ph3, study="Study 2b", factor="E", level=str(v)) for v in (0, 1))
    assert abs((e1.compliant - e0.compliant) - cex.estimate) < 0.005
    a0n = row(ph3, study="Study 2", factor="A0_name_only", level="gpt-5.4-nano")
    def p4(analysis, subset="all", outcome="fit", study="Study 2b"):
        return row(ph4, analysis=analysis, subset=subset, outcome=outcome, study=study)
    nw, nwc = p4("native - written"), p4("native - written", outcome="comp")
    assert nw.ci_lo > 0 and nw.p < 0.05
    ixER, ixEW, ixEN, ixRW, ixRN = (p4(f"interaction {x}") for x in
                                    ["E x R", "E x (written - none)", "E x (native - none)", "R x (written - none)", "R x (native - none)"])
    assert ixEW.ci_hi < 0 and ixEN.ci_hi < 0 and ixRN.ci_lo > 0 and ixER.ci_lo < 0 < ixER.ci_hi and ixRW.ci_lo < 0 < ixRW.ci_hi
    plc, plcc = p4("CoT placebo (C=1 - C=0)", study="Study 2"), p4("CoT placebo (C=1 - C=0)", outcome="comp", study="Study 2")
    assert plc.ci_lo < 0 < plc.ci_hi and plcc.ci_lo < 0 < plcc.ci_hi
    UNS, SEEN = "inputs not in the Study 2 rating sample (100)", "inputs in the Study 2 rating sample (50)"
    uns = {k_: p4(k_, subset=UNS) for k_, _ in CON}
    assert all(v.ci_lo > 0 for v in uns.values())
    ba_uns = p4("F_base - A0_name_only", subset=UNS, study="Study 2")
    ba_seen = p4("F_base - A0_name_only", subset=SEEN, study="Study 2")
    assert ba_uns.ci_lo < 0 < ba_uns.ci_hi and ba_seen.ci_hi < 0
    ba_t = {tt: p4("F_base - A0_name_only", subset=tt, study="Study 2") for tt in TIERS}
    for tt in TIERS:
        assert abs(ba_t[tt].estimate - (r2[("F_base", tt)] - r2[("A0_name_only", tt)])) < 1e-9
    assert ba_t["gpt-5.4-mini"].estimate > 0 > ba_t["gpt-5.4-nano"].estimate and ba_t["gpt-5.4"].estimate < 0
    def h5(c_, who):
        return row(ph5, criterion=c_, rater=who)
    heqm, heq1, heq3 = h5("equivalence", "mean of R1 and R3"), h5("equivalence", "R1"), h5("equivalence", "R3")
    assert heqm.ci_lo > 0 and heq1.ci_lo > 0 and heq3.ci_lo < 0 < heq3.ci_hi

    def cell(r_):
        return f"{pp(r_.estimate)} {cip(r_.ci_lo, r_.ci_hi)}"

    def cellt(r_):
        return f"{pp(r_.estimate)} pp {cip(r_.ci_lo, r_.ci_hi)}"
    tab_st = ["\\begin{table*}", "  \\caption{Post hoc: effects on pattern fit by input stratum, in percentage "
              "points with 95\\% intervals (item-level paired differences, unadjusted). Strata come from the union "
              "admissible sets. The Study~2 columns average over the other factors and the three tiers; the last "
              "column is Study~1's Base minus Name-only. For all inputs the estimates equal the planned "
              "GEE estimates; the intervals use a $t$ reference.}",
              "  \\label{tab:strata}", "  \\footnotesize", "  \\setlength{\\tabcolsep}{2.5pt}",
              "  \\begin{tabular}{@{}lrccccc@{}}", "    \\toprule",
              "    & & \\multicolumn{4}{c}{Study 2} & Study 1 \\\\", "    \\cmidrule(lr){3-6}\\cmidrule(l){7-7}",
              "    Inputs & $n$ & " + " & ".join(lab for _, lab in CON) + " & Base $-$ Name-only \\\\", "    \\midrule"]
    for lab, sname in [("A condition is required", CR), ("Only Ubiquitous admissible", UO), ("Mixed", MX)]:
        tab_st.append(f"    {lab} & {int(st('Study 2b', sname, 'examples').n_items)} & "
                      + " & ".join(cell(st("Study 2b", sname, k_)) for k_, _ in CON)
                      + f" & {cell(st('Study 2', sname, 'F_base - A0_name_only'))} \\\\")
    tab_st += ["    \\midrule", "    All inputs & 150 & " + " & ".join(cell(st("Study 2b", "all", k_)) for k_, _ in CON)
               + f" & {cell(st('Study 2', 'all', 'F_base - A0_name_only'))} \\\\",
               "    \\bottomrule", "  \\end{tabular}", "\\end{table*}"]

    # ---------------- PH7 label sets
    LS = [("union (primary)", "Union (primary)"), ("intersection", "Intersection"), ("R3 alone", "R2 alone"),
          ("R1 alone", "R1 alone"), ("cue rule", "Cue rule")]
    LC = [("examples", "Examples"), ("rules", "Rules"), ("written - none", "Written $-$ none"),
          ("native - none", "Native $-$ none"), ("Study 2: F_base - A0_name_only", "Base $-$ Name-only"),
          ("Study 2: examples", "Examples")]
    def ls(lab, con):
        return row(ph7, label_set=lab, contrast=con)
    for lab, _ in LS:
        for con in ["examples", "rules", "written - none", "native - none", "Study 2: examples"]:
            assert ls(lab, con).ci_lo > 0, (lab, con)
        assert ls(lab, "Study 2: F_base - A0_name_only").estimate < 0
    for con, plan_ in [("examples", ex), ("rules", ru), ("written - none", wr), ("native - none", na)]:
        assert abs(ls("union (primary)", con).estimate - plan_.estimate) < 1e-9
    tab_ls = ["\\begin{table*}", "  \\caption{Post hoc: the planned contrasts on pattern fit under each "
              "admissible set, in percentage points with 95\\% intervals (item-level paired differences, unadjusted). "
              "The union is the primary set; under the intersection, 25 inputs have no admissible pattern. Because these "
              "intervals use a $t$ reference, the union row can differ in the last digit from the GEE intervals of "
              "Table~\\ref{tab:2b-effects}.}",
              "  \\label{tab:labelsets}", "  \\footnotesize", "  \\setlength{\\tabcolsep}{2.5pt}",
              "  \\begin{tabular}{@{}lcccccc@{}}", "    \\toprule",
              "    & \\multicolumn{4}{c}{Study 2} & \\multicolumn{2}{c}{Study 1} \\\\",
              "    \\cmidrule(lr){2-5}\\cmidrule(l){6-7}",
              "    Admissible set & " + " & ".join(l for _, l in LC) + " \\\\", "    \\midrule"]
    for lab, lname in LS:
        tab_ls.append(f"    {lname} & " + " & ".join(
            f"{pp(ls(lab, c_).estimate)} {cip(ls(lab, c_).ci_lo, ls(lab, c_).ci_hi)}" for c_, _ in LC) + " \\\\")
    tab_ls += ["    \\bottomrule", "  \\end{tabular}", "\\end{table*}"]

    # ---------------- PH8 condition-requiring inputs and confusion
    cf_all = ph8f[(ph8f.arm == "all") & (ph8f.tier == "all")].iloc[0]
    cf_arm = ph8f[(ph8f.tier == "all") & (ph8f.arm != "all")].set_index("arm").fit
    assert int(cf_all.n) == 44 * 36 and len(cf_arm) == 12
    assert abs(cf_arm["B_base_none"] - cr["examples"].base_prompt_fit) < 1e-9
    uo_base = uo["examples"].base_prompt_fit
    PCOL = [("ubiquitous", "U"), ("event-driven", "Event"), ("unwanted-behaviour", "Unw."), ("state-driven", "State"),
            ("optional-feature", "Opt."), ("complex", "Cx"), ("non-compliant", "NC")]
    for pcol, _ in PCOL:
        if pcol not in ph8c.columns:
            ph8c[pcol] = 0
    ph8c["total"] = ph8c[[pc for pc, _ in PCOL]].sum(axis=1)
    assert (ph8c.total == 36 * ph8c.n_items).all() and int(ph8c.n_items.sum()) == round(150 * ag["best pattern"].agreement)
    share = ph8c[[pc for pc, _ in PCOL]].div(ph8c.total, axis=0)
    ROWS = [("ubiquitous", "Ubiquitous"), ("event-driven", "Event-driven"), ("unwanted-behaviour", "Unwanted beh."),
            ("state-driven", "State-driven"), ("complex", "Complex")]
    ROWS = [(k_, v_) for k_, v_ in ROWS if k_ in ph8c.index]
    tab_cf = ["\\begin{table}", "  \\caption{Post hoc: pattern chosen by the models (\\% of the 36 Study~2 outputs "
              "per input, all conditions and tiers) by best pattern, on the "
              f"{int(ph8c.n_items.sum())} inputs for which both annotators chose the same best pattern. "
              "NC: not checker-compliant.}",
              "  \\label{tab:confusion}", "  \\footnotesize", "  \\setlength{\\tabcolsep}{2.5pt}",
              "  \\begin{tabular}{@{}lrrrrrrrr@{}}", "    \\toprule",
              "    & & \\multicolumn{7}{c}{Chosen pattern (\\%)} \\\\", "    \\cmidrule(l){3-9}",
              "    Best pattern & $n$ & " + " & ".join(l for _, l in PCOL) + " \\\\", "    \\midrule"]
    for k_, v_ in ROWS:
        tab_cf.append(f"    {v_} & {int(ph8c.loc[k_, 'n_items'])} & " +
                      " & ".join(f"{100 * share.loc[k_, pc]:.1f}" for pc, _ in PCOL) + " \\\\")
    tab_cf += ["    \\bottomrule", "  \\end{tabular}", "\\end{table}"]
    u_where, u_when, u_u = (share.loc["ubiquitous", x] for x in ["optional-feature", "event-driven", "ubiquitous"])
    ev_ok = share.loc["event-driven", "event-driven"]
    uw_ok = share.loc["unwanted-behaviour", "unwanted-behaviour"]
    assert u_where > u_when > 0.05 and ev_ok > 0.75 and uw_ok > 0.75
    best_n = {k_: int(ph8c.loc[k_, "n_items"]) for k_, _ in ROWS}

    # ---------------- PH9 test-retest
    assert int(ph9.n_pairs) == 1800 and ph9.same_text < ph9.same_pattern < 1
    rt_ex1, rt_ex2, rt_ru1, rt_ru2 = (ph9[k_] for k_ in ["examples_effect_fit_study2", "examples_effect_fit_study2b",
                                                         "rules_effect_fit_study2", "rules_effect_fit_study2b"])
    # Study 1 nano F_base WHERE share (temperature 0), for the byte-identical Study 2 prompt
    s1w = c1chk[(c1chk.arm == "F_base") & (c1chk.tier == "gpt-5.4-nano")]
    s1_where = float((s1w.pattern_v2 == "optional-feature").mean())
    assert abs(s1_where - 63 / 150) < 1e-9

    # ---------------- PH10-PH13
    k10m, k10_1, k10_3 = ph10.loc["mean of R1 and R3"], ph10.loc["R1"], ph10.loc["R3"]
    assert int(k10m.n_noncompliant) + int(k10m.n_compliant) == n_h
    assert k10m.ci_lo >= -0.005 and k10_3.ci_lo > 0 and k10_1.ci_lo < 0 < k10_1.ci_hi
    assert ph11.agree_with_keyword == 1.0 and int(ph11.n_outputs) == 450
    mde_lo, mde_hi = ph12.mde_unadjusted.min(), ph12.mde_unadjusted.max()
    # PH14 (added 2026-11-21): is the examples effect larger than the other ingredients' effects?
    xr = row(ph14, contrast="examples effect - rules effect", tier="all")
    xn = row(ph14, contrast="examples effect - native - none effect", tier="all")
    assert xr.ci_lo > 0 and xn.ci_lo > 0
    both_tiers = [t for t in ["gpt-5.4-nano", "gpt-5.4-mini", "gpt-5.4"]
                  if all(row(ph14, contrast=c, tier=t).ci_lo > 0 for c in
                         ["examples effect - rules effect", "examples effect - native - none effect"])]
    assert both_tiers == ["gpt-5.4"], both_tiers  # "per tier, both differences are detected only on the full tier"
    # Accessibility description of the tier figure (acmart \\Description), from PH6
    fr = {(t, lv): int(100 * row(ph6, tier=t, reasoning=lv).rate + 0.5 + 1e-9) for t in ["gpt-5.4-nano", "gpt-5.4-mini", "gpt-5.4"]
          for lv in ["none", "written", "native"]}
    assert fr["gpt-5.4-nano", "none"] < fr["gpt-5.4-nano", "written"] < fr["gpt-5.4-nano", "native"]
    assert fr["gpt-5.4", "none"] < fr["gpt-5.4", "written"] < fr["gpt-5.4", "native"]
    assert fr["gpt-5.4-mini", "written"] < fr["gpt-5.4-mini", "none"] < fr["gpt-5.4-mini", "native"]
    fig_desc = (
        "A line chart of pattern fit in percent (axis from 50 to 100) against reasoning level (none, written, "
        "native), one line per tier. "
        f"Nano rises from about {fr['gpt-5.4-nano', 'none']} to {fr['gpt-5.4-nano', 'written']} to "
        f"{fr['gpt-5.4-nano', 'native']} percent. "
        f"Mini goes from about {fr['gpt-5.4-mini', 'none']} to {fr['gpt-5.4-mini', 'written']} to "
        f"{fr['gpt-5.4-mini', 'native']} percent. "
        f"The full tier rises from about {fr['gpt-5.4', 'none']} to {fr['gpt-5.4', 'written']} to "
        f"{fr['gpt-5.4', 'native']} percent. "
        f"A dashed horizontal line marks the constant-Ubiquitous baseline at "
        f"{pp(U1.constant_ubiquitous_fit, False)} percent.")
    mdeh_lo, mdeh_hi = ph12.mde_holm_worst.min(), ph12.mde_holm_worst.max()
    tk = ph13.groupby("reasoning").completion_tokens.agg(["min", "max"])
    assert abs(ph13[ph13.reasoning == "native"].reasoning_tokens.min() - raw_rt.min()) < 0.6
    assert tk.loc["none", "max"] < tk.loc["written", "min"] and tk.loc["written", "max"] < tk.loc["native", "min"]

    # ---------------- merged Study 1 table: checker compliance and pattern fit per condition and tier, nano WHERE
    nano, mini, full = TIERS
    S1ARMS = [("A0_name_only", "Name-only"), ("F_base", "Base"), ("F_E", "Base+E"), ("F_C", "Base+C"),
              ("F_R", "Base+R"), ("F_EC", "Base+EC"), ("F_ER", "Base+ER"), ("F_CR", "Base+CR"), ("F_ECR", "Base+ECR"),
              ("J_json", "JSON")]
    s1n = c1chk[c1chk.tier == nano]
    where_n = {a: int((s1n[s1n.arm == a].pattern_v2 == "optional-feature").sum()) for a, _ in S1ARMS}
    assert where_n["F_base"] == 63 and where_n["A0_name_only"] == 0
    tab_s1 = ["\\begin{table}", "  \\caption{Study 1 by condition: checker compliance and pattern fit (union labels) "
              "per tier, in \\%, and the number of nano outputs, of 150, that use WHERE. Base = base prompt; +E, +C and "
              "+R add examples, the chain-of-thought sentence and rules.}",
              "  \\label{tab:study1}", "  \\footnotesize", "  \\setlength{\\tabcolsep}{3pt}",
              "  \\begin{tabular}{@{}lccccccc@{}}", "    \\toprule",
              "    & \\multicolumn{3}{c}{Checker} & \\multicolumn{3}{c}{Pattern fit} & WHERE \\\\",
              "    \\cmidrule(lr){2-4}\\cmidrule(lr){5-7}\\cmidrule(l){8-8}",
              "    Condition & nano & mini & full & nano & mini & full & nano \\\\", "    \\midrule"]
    for a, lab in S1ARMS:
        if a in ("F_E", "J_json"):
            tab_s1.append("    \\midrule")
        tab_s1.append(f"    {lab} & " + " & ".join(f"{100 * r1chk[(a, t)]:.1f}" for t in TIERS) + " & "
                      + " & ".join(f"{100 * r2[(a, t)]:.1f}" for t in TIERS) + f" & {where_n[a]} \\\\")
    tab_s1 += ["    \\bottomrule", "  \\end{tabular}", "\\end{table}"]

    # ---------------- label-set ranges (PH7)
    def lsr(con):
        v = [ls(lab, con).estimate for lab, _ in LS[1:]]
        return f"{pp(min(v))} to {pp(max(v))}"

    # ---------------- Results text, ordered by research question
    assert max(ex.p_holm, ru.p_holm, wr.p_holm, na.p_holm) < 0.05 and min(ex.estimate, ru.estimate, wr.estimate, na.estimate) > 0
    assert cru.estimate > cex.estimate and ex.estimate > ru.estimate  # checker and pattern fit order examples and rules differently
    assert fit_rt.loc['none', nano] < fit_rt.loc['written', nano] < fit_rt.loc['native', nano]
    assert fit_rt.loc['none', full] < fit_rt.loc['written', full] < fit_rt.loc['native', full]
    assert fit_rt.loc['written', mini] < fit_rt.loc['none', mini]
    assert ixEW.ci_hi < 0 and ixEN.ci_hi < 0 and ixRN.ci_lo > 0
    kmax = max(kap, key=kap.get)
    assert kmax == "ubiquitous"
    a_lo = min(CRIT, key=lambda c_: aH[c_].alpha_ordinal)
    n_below_paiva = sum(aH[c_].alpha_ordinal < 0.150 for c_ in CRIT)
    assert n_below_paiva == 2
    a_hi = max(CRIT, key=lambda c_: aH[c_].alpha_ordinal)
    L = ["% Generated by study2b/scripts/make_paper_results_2b.py from the committed analysis outputs.",
         "% Do not edit by hand: change the script and re-run it.", "",
         "\\section{Results}", "\\label{sec:results}", "",
         "Sections~\\ref{sec:results-rq1} and~\\ref{sec:results-rq2} answer RQ1 and RQ2 with the planned Study~2. "
         "Sections~\\ref{sec:results-formfit} to~\\ref{sec:results-2b-human} are exploratory: "
         "Section~\\ref{sec:results-formfit} re-scores the exploratory Study~1 for RQ3, "
         "Section~\\ref{sec:results-posthoc} is post hoc, and Section~\\ref{sec:results-2b-human} reports the human "
         "ratings. Table~\\ref{tab:claims} gives the status of each main claim.", "",
         "\\begin{table}", "  \\caption{Main claims and their status.}", "  \\label{tab:claims}", "  \\footnotesize",
         "  \\setlength{\\tabcolsep}{3pt}",
         "  \\begin{tabular}{@{}>{\\raggedright\\arraybackslash}p{0.58\\linewidth}cll@{}}",
         "    \\toprule", "    Claim & Study & Status & Sect. \\\\", "    \\midrule",
         "    Examples, rules and reasoning raise pattern fit & 2 & planned & \\ref{sec:results-rq1} \\\\",
         "    The effects of examples and reasoning differ between tiers & 2 & planned & \\ref{sec:results-rq2} \\\\",
         "    Examples help more than rules or native reasoning (on average over tiers) & 2 & post hoc & "
         "\\ref{sec:results-rq1} \\\\",
         "    Native reasoning helps more than written reasoning & 2 & post hoc & \\ref{sec:results-rq1} \\\\",
         "    Checker compliance alone would rank rules above examples & 2 & descriptive & \\ref{sec:results-rq1} \\\\",
         "    Form-only scoring changes which ingredients seem to matter & 1 & exploratory & \\ref{sec:results-formfit} \\\\",
         "    A step-by-step sentence produced no reasoning (effort \\emph{none}, answer-line instruction) & 1 & post hoc "
         "& \\ref{sec:results-run} \\\\",
         "    Most gains come from not adding conditions & 1, 2 & post hoc & \\ref{sec:results-posthoc} \\\\",
         "    No reasoning effect is detected in the human ratings & 2 & exploratory & \\ref{sec:results-2b-human} \\\\",
         "    \\bottomrule", "  \\end{tabular}", "\\end{table}", "",
         "\\subsection{Manipulation checks and labels}", "\\label{sec:results-run}", "",
         "\\input{sections/s1_run}",
         f"In Study~2, all 5,400 calls completed and reasoning was manipulated on every tier: with written reasoning, "
         f"at least {100 * w_min:.1f}\\% of outputs contain at least 15 words before the tag; with native reasoning, at "
         f"least {100 * n_min:.1f}\\% of calls used reasoning tokens; without reasoning, at most {100 * none_txt:.1f}\\% "
         f"of outputs have any text before the tag and no call used reasoning tokens. "
         f"{['Zero', 'One', 'Two', 'Three', 'Four', 'Five'][n_xf]} nano outputs had no extractable requirement.",
         "",
         f"The annotators chose the same best pattern for {100 * ag['best pattern'].agreement:.0f}\\% of the inputs "
         f"($\\kappa={ag['best pattern'].cohen_kappa:.2f}$; per pattern, from {kap[kmin]:.2f} for complex to "
         f"{kap[kmax]:.2f} for ubiquitous). Under the union, Ubiquitous is admissible for "
         f"{int(U1.admissible_ubiquitous)} of the 150 inputs, so a requirement that is always well-formed and "
         f"Ubiquitous would reach {pp(U1.constant_ubiquitous_fit, False)}\\% pattern fit "
         f"({pp(I1.constant_ubiquitous_fit, False)}\\% under the intersection), our \\emph{{constant-Ubiquitous "
         f"baseline}}. For {int(I1['empty'])} inputs the annotators share no admissible pattern, and Optional feature is "
         f"admissible for only {n_opt} ({n_opt_a} for R2, {n_opt_b} for R1).",
         "",
         "\\subsection{RQ1: Ingredients (Study~2)}", "\\label{sec:results-rq1}", "",
         f"In Study~2, all three ingredients raise pattern fit (Table~\\ref{{tab:2b-effects}}): worked examples by "
         f"{pp(ex.estimate)} pp, explicit rules by {pp(ru.estimate)} pp, and reasoning ({ph(rs.p_holm)}, 2-df test), "
         f"with written reasoning adding {pp(wr.estimate)} pp and native reasoning {pp(na.estimate)} pp; all four "
         f"estimates are Holm-significant. Every effect is robust under the logit link, document-level "
         f"clustering and the intersection set; post hoc, the four contrasts also "
         f"stay above zero under the cue rule and under each annotator's set alone (Table~\\ref{{tab:labelsets}}). "
         f"Post hoc, native reasoning exceeds written reasoning by {cellt(nw)} ($p={nw.p:.3f}$)".replace("=0.", "=.")
         + f", and the examples effect exceeds that of rules by {cellt(xr)} ($p={xr.p:.3f}$)".replace("=0.", "=.")
         + f" and that of native reasoning by {cellt(xn)} ($p={xn.p:.3f}$)".replace("=0.", "=.")
         + f"; per tier, both differences are detected only on the full tier. The planned contrasts would detect "
         f"effects of {pp(mde_lo, False)} to {pp(mde_hi, False)} pp with 80\\% power. The best "
         f"condition, examples with rules and native reasoning, reaches {pp(by_arm[best], False)}\\%, against "
         f"{pp(by_arm[worst], False)}\\% for the base prompt, which is below the constant-Ubiquitous baseline.",
         "",
         f"Checker compliance moves much less (cells from {pp(chk_cells.min(), False)}\\% to "
         f"{pp(chk_cells.max(), False)}\\%): examples add {pp(cex.estimate)} pp and rules {pp(cru.estimate)} pp, and "
         f"neither reasoning contrast is significant after correction. Judged by checker compliance alone, rules would "
         f"thus seem to help more than examples, the reverse of their order in pattern fit (descriptive, not tested).",
         "", "\\input{sections/results_table_2b_effects}", "\\input{sections/results_table_labelsets}", "",
         "\\subsection{RQ2: Tiers (Study~2)}", "\\label{sec:results-rq2}", "",
         f"The effects of examples and of reasoning differ between tiers ("
         + (f"both {ph(exT.p_holm)}" if exT.p_holm < 0.001 and rsT.p_holm < 0.001 else f"{ph(exT.p_holm)} and {ph(rsT.p_holm)}")
         + f"); that of rules does not detectably ({ph(ruT.p_holm)}). Neither follows model size "
         f"(Fig.~\\ref{{fig:2b-tier}}). Examples add {pp(e_gain[nano])} pp on nano, {pp(e_gain[mini])} pp on mini and "
         f"{pp(e_gain[full])} pp on the full tier. Reasoning raises pattern fit on nano and on the full tier, whereas "
         f"written reasoning brings no gain on mini. With the base prompt on nano, reasoning largely removes the "
         f"overuse of WHERE: the share of WHERE outputs falls from {pp(wn['none'], False)}\\% without reasoning to "
         f"{pp(wn['native'], False)}\\% with native reasoning. Post hoc, we compared the four prompts that are "
         f"byte-identical in both studies, run at temperature~0 in Study~1 and at the default temperature in "
         f"Study~2. They give the same pattern-fit result for {pp(ph9.same_fit, False)}\\% of "
         f"{int(ph9.n_pairs):,} paired outputs, and their cell rates differ by at most "
         f"{pp(ph9.max_abs_cell_diff_fit, False)} pp, so tier differences of a few points are within this variation.",
         "", "\\begin{figure}", "  \\centering", "  \\includegraphics[width=\\linewidth]{figures/study2b_fit_by_tier.pdf}",
         f"  \\caption{{Study 2 pattern fit by reasoning level and tier, averaged over examples and rules ({n_pt:,} "
         f"outputs per point), with 95\\% intervals over items. Dashed: constant-Ubiquitous baseline under the union "
         f"({pp(U1.constant_ubiquitous_fit, False)}\\%). The axis starts at 50\\%.}}",
         "  \\Description{" + fig_desc + "}",
         "  \\label{fig:2b-tier}", "\\end{figure}", "",
         "\\subsection{RQ3: What a form-only checker misses (Study~1, exploratory)}", "\\label{sec:results-formfit}", "",
         "\\input{sections/s1_checker}", "\\input{sections/s1_where}", "",
         "\\input{sections/results_table_study1}", "",
         f"We then re-scored Study~1 with Study~2's labels, a secondary analysis fixed in Study~2's plan after "
         f"Study~1's outputs had been inspected. The base prompt's advantage over the Name-only prompt is then no "
         f"longer detected: "
         f"{pp(s2ba.estimate)} pp ($p={s2ba.p:.2f}$, unadjusted)".replace("=0.", "=.")
         + f" instead of {pp(pba.estimate)} pp (per label set in Table~\\ref{{tab:labelsets}}, per-tier rates in "
         f"Table~\\ref{{tab:study1}}). Worked examples raise pattern fit by {pp(s2ex.estimate)} pp ({ph(s2ex.p_holm)}), "
         f"against {pp(pex.estimate)} pp for checker compliance, and rules by {pp(s2ru.estimate)} pp ({ph(s2ru.p_holm)}). "
         f"Base+R gave nano its highest checker compliance ({pp(r1chk[('F_R', nano)], False)}\\%) but a pattern fit of "
         f"{pp(r2[('F_R', nano)], False)}\\%. The pattern that the JSON prompt makes the model name matches its opening "
         f"keyword in all {int(ph11.n_compliant_with_label)} compliant outputs, so the model's own label cannot reveal a "
         f"wrong choice (post hoc).",
         "",
         "\\subsection{Where the gains come from (post hoc)}", "\\label{sec:results-posthoc}", "",
         f"These analyses were added after the planned ones (Table~\\ref{{tab:protocol}}). Most pattern-fit gains come "
         f"from outputs that no longer add a condition the input does not state. Worked examples raise checker "
         f"compliance only from {pp(e0.compliant, False)}\\% to {pp(e1.compliant, False)}\\%, but the share of "
         f"Ubiquitous outputs from {pp(e0.ubiquitous_share, False)}\\% to {pp(e1.ubiquitous_share, False)}\\%. "
         f"Table~\\ref{{tab:strata}} splits the inputs by admissible set. On the {n_uo} inputs for which only Ubiquitous "
         f"is admissible, every ingredient helps. On the {n_cr} inputs that require a condition, pattern fit is already "
         f"high ({pp(cf_arm['B_base_none'], False)}\\% for the base prompt), and only native reasoning, of the four "
         f"Study~2 contrasts, helps detectably. Study~1's base prompt raises pattern fit on the inputs that require a "
         f"condition and lowers it on the Ubiquitous-only ones, where the Name-only prompt mostly writes unconditional "
         f"requirements ({pp(a0n.ubiquitous_share, False)}\\% of its nano outputs). On the {int(ph8c.n_items.sum())} "
         f"inputs whose best pattern both annotators agree on, outputs for Ubiquitous inputs use WHERE in "
         f"{pp(u_where, False)}\\% and WHEN in {pp(u_when, False)}\\% of cases, while event-driven and "
         f"unwanted-behaviour inputs get their pattern in {pp(ev_ok, False)}\\% and {pp(uw_ok, False)}\\%. Reasoning "
         f"adds less when examples are present (examples $\\times$ written {pp(ixEW.estimate)} pp; examples $\\times$ "
         f"native {pp(ixEN.estimate)} pp), whereas rules and native reasoning reinforce each other "
         f"({pp(ixRN.estimate)} pp); all three intervals exclude zero.",
         "", "\\input{sections/results_table_strata}", "",
         f"Both annotators had rated Study~1 outputs for 50 inputs. On the other 100, the Study~2 effects keep their "
         f"size (examples {pp(uns['examples'].estimate)}, rules {pp(uns['rules'].estimate)}, written "
         f"{pp(uns['written - none'].estimate)}, native {pp(uns['native - none'].estimate)} pp, all above zero). By "
         f"contrast, Study~1's Base-versus-Name-only estimate is {cellt(ba_uns)} on them and {pp(ba_seen.estimate)} pp on the 50 "
         f"rated inputs. Within Study~1, the inert step-by-step sentence acts as a placebo: it changes pattern fit by "
         f"{cellt(plc)}.",
         "",
         "\\subsection{Human ratings (exploratory)}", "\\label{sec:results-2b-human}", "",
         f"R1 and R2 rated {n_h} base-prompt outputs ({tier_items[nano]}, {tier_items[mini]} and {tier_items[full]} items "
         f"on nano, mini and full). Agreement is low. Across the five criteria, the highest Krippendorff's "
         f"$\\alpha$ is {fmt(aH[a_hi].alpha_ordinal, 2, False)} ({CL[a_hi]}) and the lowest "
         f"{fmt(aH[a_lo].alpha_ordinal, 2, False)} ({CL[a_lo]}); quadratic-weighted $\\kappa$ lies between "
         f"{fmt(kw_lo, 2, False)} and {fmt(kw_hi, 2, False)}, and exact "
         f"and within-one agreement exceed chance by at most {100 * ex_gain:.0f} and {100 * w1_gain:.0f} points. Low "
         f"agreement is common when humans rate requirement quality: among five evaluators, Paiva "
         f"et al.~\\cite{{paiva2026issuetitles}} report $\\alpha$ between 0.150 and 0.394. Ours is lower still on "
         f"{['no', 'one', 'two', 'three', 'four', 'five'][n_below_paiva]} criteria. Scores sit "
         f"near the ceiling (every condition mean at least {floor:.2f}; {100 * eq4:.0f}\\% of outputs have a mean "
         f"equivalence of at least 4), and no difference between reasoning levels is Holm-significant (smallest "
         f"{ph(minp)}), also for R2 alone. Post hoc, the checker's {int(k10m.n_noncompliant)} non-compliant outputs "
         f"received lower EARS well-formedness scores ({k10m.mean_noncompliant:.2f} vs {k10m.mean_compliant:.2f}). "
         f"Outputs with pattern fit received higher equivalence scores ({heqm.mean_fit:.2f} vs "
         f"{heqm.mean_misfit:.2f}), but this difference comes from R1 ({fmt(heq1.estimate, 2)} "
         f"{ci2(heq1.ci_lo, heq1.ci_hi)}), who is also an annotator, and is not detected for R2 ({fmt(heq3.estimate, 2)} "
         f"{ci2(heq3.ci_lo, heq3.ci_hi)}).", ""]

    with open("paper/sections/study2b_results.tex", "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    for name, tab in [("2b_effects", tab_eff), ("strata", tab_st), ("study1", tab_s1), ("labelsets", tab_ls)]:
        with open(f"paper/sections/results_table_{name}.tex", "w", encoding="utf-8") as f:
            f.write("% Generated by study2b/scripts/make_paper_results_2b.py.\n" + "\n".join(tab) + "\n")
    print("Wrote study2b_results.tex (Study 2 in the paper), four tables and figures/study2b_fit_by_tier.pdf")


if __name__ == "__main__":
    main()
