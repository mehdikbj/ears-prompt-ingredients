#!/usr/bin/env python3
"""
Pattern fit: agreement between the two annotators, and EARS compliance that also requires the
output's pattern to be admissible for its input. Written and committed BEFORE any annotation
sheet exists (study2b/ANALYSIS_PLAN.md, section P).

  python3 study2b/pattern_fit/analyze_pattern_fit.py              # needs both sheets (+ consolidated)
  python3 study2b/pattern_fit/analyze_pattern_fit.py --simulate   # pipeline test on random labels -> a temp dir

Outcome: pattern_fit = checker v2 compliant AND pattern_v2 is admissible for the item.
Admissible sets: union of A and B (PRIMARY: the most lenient towards WHERE outputs, because both
annotators, R1 and R3, have seen Study 2 outputs and know the hypothesis); consolidated; intersection;
and "cue rule", where Optional feature is admissible only if the input matches a pre-registered
lexical cue (OPTIONAL_CUES) and the other patterns come from the union.
Applied to Study 2 (all 4,500 outputs; secondary analysis of existing data, labels blind to outputs)
and, if present, to Study 2b.
"""
import os
import sys
import tempfile

import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
from s2bcommon import CHECKS as CHECKS_2B, PATTERN_FIT_DIR, S  # noqa: E402
import analyze_study2 as A  # noqa: E402  (Study 2 helpers on sys.path via s2bcommon)

import re

# Pre-registered lexical cues for an optional feature (committed before any label exists). Crude and
# deliberately lenient: a match makes Optional feature admissible in the "cue rule" set.
OPTIONAL_CUES = [r"\boptional(ly)?\b", r"\bat all\b", r"\bnot every\b", r"\bnot all\b",
                 r"\bsome (sites|installations|customers|clients|networks|versions|products|configurations|deployments|users)\b",
                 r"\bconfigurable\b", r"\b(turn|switch)(ed)? (it )?(on|off)\b", r"\badd-?on\b", r"\bplug-?in\b",
                 r"\bif (they|we|you|the customer|the site|the client)\b.{0,30}\b(buy|purchase|order|choose|opt|pay)\b",
                 r"\bif (it|the system|the \w+) (has|have|includes?|supports?|offers?)\b"]


def optional_cue(text):
    return any(re.search(c, text, re.I) for c in OPTIONAL_CUES)


COLMAP = {"adm_ubiquitous": "ubiquitous", "adm_event_driven": "event-driven",
          "adm_unwanted_behaviour": "unwanted-behaviour", "adm_state_driven": "state-driven",
          "adm_optional_feature": "optional-feature", "adm_complex": "complex"}


def read_sheet(path):
    d = pd.read_csv(path, encoding="utf-8-sig", dtype=str).fillna("")
    assert len(d) == 150 and d.item_id.nunique() == 150, f"{path}: needs 150 distinct items"
    for c in COLMAP:
        bad = d[~d[c].str.strip().isin(["0", "1"])]
        assert bad.empty, f"{path}: {c} must be 0 or 1 (e.g. {bad.item_id.head(3).tolist()})"
        d[c] = d[c].astype(int)
    assert (d[list(COLMAP)].sum(axis=1) > 0).all(), f"{path}: every item needs at least one admissible pattern"
    for r in d.itertuples():
        col = [k for k, v in COLMAP.items() if v == r.best_pattern.strip()]
        assert col and getattr(r, col[0]) == 1, f"{path}: {r.item_id} best_pattern must be marked admissible"
    return d.set_index("item_id").sort_index()


def admissible(d):
    return {i: {COLMAP[c] for c in COLMAP if row[c] == 1} for i, row in d.iterrows()}


def agreement(a, b):
    rows = []
    for c, name in COLMAP.items():
        x, y = a[c].values, b[c].values
        k = cohen_kappa_score(x, y) if len(set(x) | set(y)) > 1 else np.nan
        rows.append(dict(measure=f"admissible: {name}", n_A=int(x.sum()), n_B=int(y.sum()),
                         agreement=float((x == y).mean()), cohen_kappa=k))
    k = cohen_kappa_score(a.best_pattern, b.best_pattern)
    rows.append(dict(measure="best pattern", n_A=np.nan, n_B=np.nan,
                     agreement=float((a.best_pattern == b.best_pattern).mean()), cohen_kappa=k))
    return pd.DataFrame(rows)


def apply(checks, sets, label):
    d = checks.copy()
    d["pattern_fit"] = [int(bool(c) and (p in sets[i])) for c, p, i in zip(d.compliant_itt, d.pattern_v2, d.item_id)]
    return d.assign(admissible_set=label)


def study2_tests(d):
    d = d.copy()
    d["y"] = d.pattern_fit
    fac = d[d.arm.isin(A.FACTORIAL)]
    prim = A.primary_tests(A.gee(fac, A.FORMULA), "pattern fit")
    x = d[d.arm.isin(["F_base", "A0_name_only"])].copy()
    x["x"] = (x.arm == "F_base").astype(float) - 0.5
    est, lo, hi, _, p = A.coef(A.gee(x, "y ~ x * C(tier, Sum)"), "x")
    ref = pd.DataFrame([dict(test="F_base - A0_name_only", estimate=est, ci_lo=lo, ci_hi=hi, p=p)])
    return prim, ref


def run(dir_in, out):
    os.makedirs(out, exist_ok=True)
    a = read_sheet(f"{dir_in}/02_sheet_annotator_A.csv")
    b = read_sheet(f"{dir_in}/02_sheet_annotator_B.csv")
    assert list(a.index) == list(b.index)
    agreement(a, b).to_csv(f"{out}/01_agreement.csv", index=False)
    union = {i: s1 | s2 for (i, s1), s2 in zip(admissible(a).items(), admissible(b).values())}
    inputs = {i["id"]: i["messified_text"] for i in S.load_json(S.MESSIFIED)}
    cue = {i: ({p for p in s if p != "optional-feature"} | ({"optional-feature"} if optional_cue(inputs[i]) else set()))
           or {"ubiquitous"} for i, s in union.items()}
    sets = {"union (primary)": union,
            "intersection": {i: s1 & s2 for (i, s1), s2 in zip(admissible(a).items(), admissible(b).values())},
            "cue rule for optional feature": cue}
    cons_path = f"{dir_in}/03_consolidated.csv"
    cons = pd.read_csv(cons_path, dtype=str).fillna("") if os.path.exists(cons_path) else None
    if cons is not None and (cons[list(COLMAP)] != "").all().all():
        sets["consolidated"] = admissible(read_sheet(cons_path))
    hum = pd.Series({i: "optional-feature" in s for i, s in union.items()})
    cue_s = pd.Series({i: optional_cue(inputs[i]) for i in union})
    pd.DataFrame([dict(items_optional_by_union=int(hum.sum()), items_optional_by_cue=int(cue_s.sum()),
                       both=int((hum & cue_s).sum()), agreement=float((hum == cue_s).mean()),
                       cohen_kappa=cohen_kappa_score(hum, cue_s) if hum.nunique() > 1 and cue_s.nunique() > 1 else np.nan)]) \
        .to_csv(f"{out}/01b_optional_feature_humans_vs_cue_rule.csv", index=False)
    s2 = A.load()
    rates, tests, refs = [], [], []
    for label, st in sets.items():
        d = apply(s2, st, label)
        rates.append(d.groupby(["arm", "tier"]).pattern_fit.mean().rename("rate").reset_index().assign(set=label))
        prim, ref = study2_tests(d)
        tests.append(prim.assign(set=label))
        refs.append(ref.assign(set=label))
    pd.concat(rates).to_csv(f"{out}/02_study2_pattern_fit_rates.csv", index=False)
    pd.concat(tests).to_csv(f"{out}/03_study2_primary_tests_pattern_fit.csv", index=False)
    pd.concat(refs).to_csv(f"{out}/04_study2_base_vs_name_only_pattern_fit.csv", index=False)
    if os.path.exists(CHECKS_2B):
        c2b = pd.DataFrame(S.read_jsonl(CHECKS_2B))
        pd.concat([apply(c2b, st, lab) for lab, st in sets.items()]) \
            .groupby(["admissible_set", "arm", "model_alias"]).pattern_fit.mean().rename("rate").reset_index() \
            .to_csv(f"{out}/05_study2b_pattern_fit_rates.csv", index=False)
    print(f"Sets: {list(sets)}. Wrote {out}/")


def simulate(tmp):
    rng = np.random.default_rng(1)
    items = sorted(i["id"] for i in S.load_json(S.MESSIFIED))
    for who in ["A", "B"]:
        best = rng.choice(list(COLMAP.values())[:5], size=150, p=[.5, .2, .1, .15, .05])
        d = pd.DataFrame({"item_id": items, "input": ""})
        for c, name in COLMAP.items():
            d[c] = ((best == name) | (rng.random(150) < .1)).astype(int)
        d["best_pattern"], d["notes"] = best, ""
        d.to_csv(f"{tmp}/02_sheet_annotator_{who}.csv", index=False)


def main():
    if "--simulate" in sys.argv:
        tmp = tempfile.mkdtemp(prefix="pattern_fit_sim_")
        simulate(tmp)
        run(tmp, f"{tmp}/results")
        print("SIMULATION ONLY: random labels, nothing written to the repository.")
        return
    run(PATTERN_FIT_DIR, f"{PATTERN_FIT_DIR}/results")


if __name__ == "__main__":
    main()
