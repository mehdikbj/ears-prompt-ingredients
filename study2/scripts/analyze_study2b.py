#!/usr/bin/env python3
"""
Study 2b analysis (study2b/ANALYSIS_PLAN.md).

  python3 study2b/scripts/analyze_study2b.py               # needs results/checks_2b.jsonl (+ pattern-fit labels)
  python3 study2b/scripts/analyze_study2b.py --simulate    # pipeline test on simulated outputs -> a temp dir

1. Manipulation checks per reasoning level and tier (settings.json, manipulation_checks).
2. Primary outcome: pattern-fit compliance (checker v2 compliant AND pattern admissible for the item,
   union of the two annotators' labels in study2b/pattern_fit/). Secondary: checker compliance alone.
3. Primary family (Holm over 6), GEE identity link, item clusters:
   y ~ e * r * C(reasoning, Sum) * C(tier, Sum), e and r effect-coded (+/-0.5).
   Tests: examples, rules (marginal contrasts averaged over the other factors), reasoning (2-df Wald),
   and each x tier (Wald). Reasoning contrasts written - none, native - none (Holm over 2).
4. Sensitivity analyses of the primary family (each with its own Holm correction): logit link (Wald
   tests on log-odds coefficients); clusters = 19 source documents with bias-reduced covariance and t / F
   reference distributions; without PURE-014 and PURE-126 (closest to an exemplar); and, for pattern fit,
   the intersection, cue-rule and (if made) consolidated admissible sets.
"""
import os
import sys
import tempfile
import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import chi2, f as f_dist, norm, t as t_dist
from statsmodels.stats.multitest import multipletests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from s2bcommon import CHECKS, PATTERN_FIT_DIR, RESULTS, SETTINGS_PATH, S  # noqa: E402

FORMULA = "y ~ e * r * C(reasoning, Sum) * C(tier, Sum)"
SENSITIVE_ITEMS = ["PURE-014", "PURE-126"]


def manipulation(d):
    rows = []
    for (lev, t), g in d.groupby(["reasoning", "tier"]):
        wb = g.words_before_tag.fillna(0)
        rows.append(dict(reasoning=lev, tier=t, n=len(g), share_ge15_words_before_tag=(wb >= 15).mean(),
                         share_any_text_before_tag=(wb > 0).mean(), share_reasoning_tokens=(g.reasoning_tokens > 0).mean(),
                         mean_completion_tokens=g.completion_tokens.mean()))
    m = pd.DataFrame(rows)
    ok = {"written": m.reasoning.eq("written") & (m.share_ge15_words_before_tag >= 0.90),
          "native": m.reasoning.eq("native") & (m.share_reasoning_tokens >= 0.90),
          "none": m.reasoning.eq("none") & (m.share_any_text_before_tag <= 0.05) & (m.share_reasoning_tokens == 0)}
    m["check_passed"] = ok["written"] | ok["native"] | ok["none"]
    return m


def fit(d, family=None, group="item_id", small=False):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model = sm.GEE.from_formula(FORMULA, groups=group, data=d, family=family or sm.families.Gaussian(),
                                    cov_struct=sm.cov_struct.Independence())
        res = model.fit(cov_type="bias_reduced") if small else model.fit()
    res.small_df = (d[group].nunique() - 1) if small else None
    return res


def _p_and_q(z, res):
    if res.small_df:
        return 2 * t_dist.sf(abs(z), res.small_df), t_dist.ppf(0.975, res.small_df)
    return 2 * norm.sf(abs(z)), 1.96


def marginal(res, d, col, a, b):
    """Mean predicted difference (col=a minus col=b) over the observed rows, with robust SE (identity link)."""
    from patsy import build_design_matrices
    di = getattr(res.model.data, "model_spec", None) or getattr(res.model.data, "design_info")  # statsmodels 0.15
    xa = np.asarray(build_design_matrices([di], d.assign(**{col: a}))[0]).mean(0)
    xb = np.asarray(build_design_matrices([di], d.assign(**{col: b}))[0]).mean(0)
    L = xa - xb
    est = float(L @ res.params.values)
    se = float(np.sqrt(L @ res.cov_params().values @ L))
    if se == 0:
        return est, est, est, 1.0
    p, q = _p_and_q(est / se, res)
    return est, est - q * se, est + q * se, p


def _parts(name):
    return {"tier" if p.startswith("C(tier") else "reasoning" if p.startswith("C(reasoning") else p
            for p in name.split(":")}


def wald(res, pred):
    idx = [k for k, n in enumerate(res.model.exog_names) if n != "Intercept" and pred(_parts(n))]
    b = res.params.values[idx]
    v = res.cov_params().values[np.ix_(idx, idx)]
    stat = float(b @ np.linalg.pinv(v) @ b)
    if res.small_df:
        return stat, len(idx), float(f_dist.sf(stat / len(idx), len(idx), res.small_df))
    return stat, len(idx), float(chi2.sf(stat, len(idx)))


def primary(d, label, family=None, group="item_id", small=False):
    res = fit(d, family, group, small)
    logit = family is not None and isinstance(family, sm.families.Binomial)
    rows = []
    for f, nm in [("e", "examples"), ("r", "rules")]:
        if logit:  # log-odds coefficient (effect coding: average over the other factors)
            stat, df, p = wald(res, lambda s, f=f: s == {f})
            k = res.model.exog_names.index(f)
            rows.append(dict(test=f"main effect: {nm}", estimate=float(res.params.iloc[k]), stat=stat, df=df, p=p,
                             scale="log-odds"))
        else:
            est, lo, hi, p = marginal(res, d, f, 0.5, -0.5)
            rows.append(dict(test=f"main effect: {nm}", estimate=est, ci_lo=lo, ci_hi=hi, p=p, scale="probability"))
    stat, df, p = wald(res, lambda s: s == {"reasoning"})
    rows.append(dict(test="main effect: reasoning (2 df)", stat=stat, df=df, p=p))
    for f, nm in [("e", "examples"), ("r", "rules"), ("reasoning", "reasoning")]:
        stat, df, p = wald(res, lambda s, f=f: s == {f, "tier"})
        rows.append(dict(test=f"{nm} x tier", stat=stat, df=df, p=p))
    t = pd.DataFrame(rows)
    t["p_holm"] = multipletests(t.p, method="holm")[1]
    c = pd.DataFrame()
    if not logit:
        c = pd.DataFrame([dict(contrast=f"{lev} - none", **dict(zip(["estimate", "ci_lo", "ci_hi", "p"],
                                                                     marginal(res, d, "reasoning", lev, "none"))))
                          for lev in ["written", "native"]])
        c["p_holm"] = multipletests(c.p, method="holm")[1]
    return t.assign(analysis=label), c.assign(analysis=label)


def load_checks(path):
    d = pd.DataFrame(S.read_jsonl(path))
    d["tier"] = d.model_alias
    d["e"] = d.E.astype(float) - 0.5
    d["r"] = d.R.astype(float) - 0.5
    docs = {i["id"]: i["source_document_key"] for i in S.load_json(S.PURE150)}
    d["doc"] = d.item_id.map(docs)
    return d


def admissible_sets(labels_dir):
    """Union (primary), intersection, cue rule, consolidated (if complete). Empty dict if no labels yet."""
    sa, sb = f"{labels_dir}/02_sheet_annotator_A.csv", f"{labels_dir}/02_sheet_annotator_B.csv"
    if not (os.path.exists(sa) and os.path.exists(sb)):
        return {}
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "pattern_fit"))
    from analyze_pattern_fit import COLMAP, admissible, optional_cue, read_sheet
    a, b = admissible(read_sheet(sa)), admissible(read_sheet(sb))
    union = {i: a[i] | b[i] for i in a}
    inputs = {i["id"]: i["messified_text"] for i in S.load_json(S.MESSIFIED)}
    sets = {"union (primary)": union, "intersection": {i: a[i] & b[i] for i in a},
            "cue rule for optional feature": {i: ({p for p in s if p != "optional-feature"} |
                                                  ({"optional-feature"} if optional_cue(inputs[i]) else set()))
                                              or {"ubiquitous"} for i, s in union.items()}}
    cons = f"{labels_dir}/03_consolidated.csv"
    if os.path.exists(cons) and (pd.read_csv(cons, dtype=str).fillna("")[list(COLMAP)] != "").all().all():
        sets["consolidated"] = admissible(read_sheet(cons))
    return sets


def fit_flag(d, s):
    return pd.Series([int(bool(c) and p in s[i]) for c, p, i in zip(d.compliant_itt, d.pattern_v2, d.item_id)],
                     index=d.index)


def run(checks_path, labels_dir, out):
    os.makedirs(out, exist_ok=True)
    d = load_checks(checks_path)
    assert d.duplicated(["item_id", "arm", "model_alias"]).sum() == 0
    man = manipulation(d)
    man.to_csv(f"{out}/01_manipulation_checks.csv", index=False)
    sets = admissible_sets(labels_dir)
    outcomes = {}
    if sets:
        outcomes["pattern fit, union (primary)"] = fit_flag(d, sets["union (primary)"])
    outcomes["checker compliance (secondary)"] = d.compliant_itt.astype(int)
    tests, contrasts, sens = [], [], []
    for lab, y in outcomes.items():
        dd = d.assign(y=y.values)
        t, c = primary(dd, "primary")
        tests.append(t.assign(outcome=lab))
        contrasts.append(c.assign(outcome=lab))
        for slab, kw, sub in [("logit link", dict(family=sm.families.Binomial()), dd),
                              ("clusters = source document, bias-reduced, t/F", dict(group="doc", small=True), dd),
                              (f"excluding {', '.join(SENSITIVE_ITEMS)}", {}, dd[~dd.item_id.isin(SENSITIVE_ITEMS)])]:
            st, sc = primary(sub, slab, **kw)
            sens += [st.assign(outcome=lab), sc.assign(outcome=lab)]
    for slab, s in sets.items():
        if slab == "union (primary)":
            continue
        st, sc = primary(d.assign(y=fit_flag(d, s).values), f"admissible set: {slab}")
        sens += [st.assign(outcome="pattern fit"), sc.assign(outcome="pattern fit")]
    pd.concat(tests).to_csv(f"{out}/02_primary_tests.csv", index=False)
    pd.concat(contrasts).to_csv(f"{out}/03_reasoning_contrasts.csv", index=False)
    pd.concat(sens).to_csv(f"{out}/06_sensitivity.csv", index=False)
    d.groupby(["arm", "tier"]).compliant_itt.mean().rename("checker_rate").reset_index() \
        .to_csv(f"{out}/04_rates_by_arm_tier.csv", index=False)
    d.groupby(["arm", "tier"]).pattern_v2.value_counts(dropna=False).rename("n").reset_index() \
        .to_csv(f"{out}/05_patterns.csv", index=False)
    print(man.to_string(index=False))
    print(pd.concat(tests).to_string(index=False))
    print(f"Wrote {out}/")


def simulate(tmp):
    """Simulated checks file: random compliance and patterns; written arms get reasoning text, native arms tokens."""
    import json
    rng = np.random.default_rng(2)
    arms = S.load_json("study2b/config/arms.json")["arms"]
    items = [i["id"] for i in S.load_json(S.MESSIFIED)]
    pats = ["ubiquitous", "event-driven", "unwanted-behaviour", "state-driven", "optional-feature"]
    path = f"{tmp}/checks_2b.jsonl"
    with open(path, "w") as f:
        for a in arms:
            for t in ["gpt-5.4-nano", "gpt-5.4-mini", "gpt-5.4"]:
                for i in items:
                    p = 0.85 + 0.05 * a["E"] + 0.03 * a["R"] + (0.02 if a["reasoning"] == "written" else 0)
                    f.write(json.dumps(dict(item_id=i, arm=a["arm"], E=a["E"], R=a["R"], reasoning=a["reasoning"],
                                            model_alias=t, compliant_itt=bool(rng.random() < p),
                                            pattern_v2=str(rng.choice(pats, p=[.5, .2, .1, .1, .1])),
                                            words_before_tag=int(rng.integers(20, 120)) if a["reasoning"] == "written" else 0,
                                            reasoning_tokens=int(rng.integers(50, 400)) if a["reasoning"] == "native" else 0,
                                            completion_tokens=int(rng.integers(20, 300)))) + "\n")
    return path


def main():
    if "--simulate" in sys.argv:
        tmp = tempfile.mkdtemp(prefix="study2b_sim_")
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "pattern_fit"))
        import analyze_pattern_fit as P
        P.simulate(tmp)  # random annotator sheets, so the pattern-fit outcome and its sensitivities run too
        run(simulate(tmp), tmp, f"{tmp}/analysis")
        print("SIMULATION ONLY: nothing written to the repository.")
        return
    S.load_json(SETTINGS_PATH)
    run(CHECKS, PATTERN_FIT_DIR, f"{RESULTS}/analysis")


if __name__ == "__main__":
    main()
