#!/usr/bin/env python3
"""
Conservative cost estimate for Study 2, calibrated on the logged usage of the
prior exploratory run (archive/study1/results/raw_inference.jsonl).

  python3 study2/scripts/estimate_cost.py            # full run (150 items)
  python3 study2/scripts/estimate_cost.py --items 5  # pilot

Input tokens per call  = prior-run zero-shot prompt tokens for that item's tier
                         + extra system-prompt characters / 4.0 chars per token
                         (the prior run measured 4.5-5.0, so 4.0 over-estimates).
Output tokens per call = prior-run mean completion tokens for that tier:
                         chain-of-thought arms -> prior-run CoT x 1.5 (free-form
                         "think step by step" may run longer than the prior run's
                         three-step CoT); JSON arm -> zero-shot + 25 tokens;
                         other arms -> zero-shot.
A 20% margin is added on top.
"""
import argparse
import os
import statistics as st
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from s2common import (ARM_DIR, ARMS_PATH, NAME_ONLY_REF, PRIOR_RUN_RAW, load_json, parse_template, price_table,
                      read_jsonl, read_text)

CHARS_PER_TOKEN = 4.0
COT_FACTOR = 1.5
JSON_EXTRA = 25
MARGIN = 1.20


def estimate(n_items=150):
    prior = read_jsonl(PRIOR_RUN_RAW)
    prices = price_table()
    zs_sys = parse_template(read_text(NAME_ONLY_REF))[0]
    by = {}
    for r in prior:
        by.setdefault((r["strategy"], r["model_id"]), []).append(r["usage"])
    arms = load_json(ARMS_PATH)["arms"]
    rows, total = [], 0.0
    for model_id in prices:
        zs_in = st.mean(u["prompt_tokens"] for u in by[("zero_shot", model_id)])
        zs_out = st.mean(u["completion_tokens"] for u in by[("zero_shot", model_id)])
        cot_out = st.mean(u["completion_tokens"] for u in by[("chain_of_thought", model_id)])
        tier_cost = 0.0
        for a in arms:
            system = parse_template(read_text(f"{ARM_DIR}/{a['arm']}.txt"))[0]
            tin = zs_in + max(0, len(system) - len(zs_sys)) / CHARS_PER_TOKEN
            if a["C"]:
                tout = cot_out * COT_FACTOR
            elif a["output"] == "final_json":
                tout = zs_out + JSON_EXTRA
            else:
                tout = zs_out
            p = prices[model_id]
            c = n_items * (tin / 1e6 * p["input"] + tout / 1e6 * p["output"]) * MARGIN
            rows.append((model_id, a["arm"], round(tin), round(tout), c))
            tier_cost += c
        total += tier_cost
    return rows, total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", type=int, default=150)
    args = ap.parse_args()
    rows, total = estimate(args.items)
    print(f"{'model':26s} {'arm':14s} {'in_tok':>7s} {'out_tok':>7s} {'cost_usd':>9s}")
    for m, a, i, o, c in rows:
        print(f"{m:26s} {a:14s} {i:7d} {o:7d} {c:9.3f}")
    print(f"\nEstimated total for {args.items} items x {len(rows)} arm-model cells: ${total:.2f} (includes 20% margin)")


if __name__ == "__main__":
    main()
