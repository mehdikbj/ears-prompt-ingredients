#!/usr/bin/env python3
"""
Study 2b inference: 150 items x 12 arms x 3 pinned GPT-5.4 snapshots = 5,400 calls
(pilot: 5 items = 180 calls). Frozen on 2026-11-08 (ANALYSIS_PLAN.md).

  python3 study2b/scripts/run_inference_2b.py --dry-run     # no API call; plan + cost estimate
  python3 study2b/scripts/run_inference_2b.py --pilot       # 180 calls -> results/pilot/
  python3 study2b/scripts/run_inference_2b.py               # full run -> results/

Differences from Study 2's runner (study2/scripts/run_inference_study2.py):
  - reasoning_effort is passed explicitly on every call (settings.json: none / none / low);
  - temperature is omitted on every call (decision D1);
  - outputs go to study2b/results/, and the budget is Study 2b's own.
Same safeguards: manifest check, clean git tree for study2b/, budget cap, seeded call order,
resume without mixing prompt versions, every record fully logged.
"""
import argparse
import asyncio
import json
import os
import platform
import random
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from s2bcommon import (ARM_DIR, ARMS_PATH, RAW_FULL, RAW_PILOT, SETTINGS_PATH, S, git_state_2b,  # noqa: E402
                       spent_usd_2b, verify_manifest_2b)

MAX_CONCURRENCY = 5
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 5
# Conservative extra output tokens per call, on top of Study 2's logged usage (decision D3; README.md).
EXTRA_OUTPUT_TOKENS = {"none": 0, "written": 400, "native": 1000}
MARGIN = 1.2


def build_plan(pilot, arms_filter=None, models_filter=None):
    st = S.load_json(SETTINGS_PATH)
    lineup = S.load_json(S.LINEUP)
    items = S.load_json(S.MESSIFIED)
    if pilot:
        keep = set(st["pilot"]["item_ids"])
        items = [i for i in items if i["id"] in keep]
    arms = S.load_json(ARMS_PATH)["arms"]
    if arms_filter:
        arms = [a for a in arms if a["arm"] in arms_filter]
    tiers = lineup["tiers"]
    if models_filter:
        tiers = [t for t in tiers if t["name"] in models_filter]
    effort = st["api_call"]["reasoning_effort"]
    plan = []
    for a in arms:
        path = f"{ARM_DIR}/{a['arm']}.txt"
        system, user_t = S.parse_template(S.read_text(path))
        assert user_t == "{{messified_text}}", path
        sha = S.sha256_file(path)
        for it in items:
            for t in tiers:
                plan.append({"item_id": it["id"], "arm": a["arm"], "E": a["E"], "R": a["R"],
                             "reasoning": a["reasoning"], "reasoning_effort": effort[a["reasoning"]],
                             "output_format": "final_line", "model_id": t["dated_snapshot_id"],
                             "model_alias": t["model_id"], "model_tier": t["tier"], "arm_prompt_sha256": sha,
                             "system_prompt": system, "user_prompt": it["messified_text"]})
    random.Random(st["seeds"]["call_order_shuffle"]).shuffle(plan)
    return plan, st


def estimate_cost(plan):
    """Study 2's mean logged tokens per (tier, E, R) for the matching arm, plus EXTRA_OUTPUT_TOKENS."""
    import collections
    prices = S.price_table()
    raw = [r for r in S.read_jsonl(S.RAW_FULL) if not r.get("error")]
    arm_of = {(0, 0): "F_base", (1, 0): "F_E", (0, 1): "F_R", (1, 1): "F_ER"}
    acc = collections.defaultdict(lambda: [0, 0, 0])
    for r in raw:
        k = (r["model_id"], r["arm"])
        acc[k][0] += r["usage"]["prompt_tokens"]
        acc[k][1] += r["usage"]["completion_tokens"]
        acc[k][2] += 1
    total = 0.0
    for t in plan:
        p, c, n = acc[(t["model_id"], arm_of[(t["E"], t["R"])])]
        pt = p / n + (60 if t["reasoning"] == "written" else 0)
        ct = c / n + EXTRA_OUTPUT_TOKENS[t["reasoning"]]
        total += S.call_cost(t["model_id"], pt, ct, prices)
    return total * MARGIN


class Budget:
    def __init__(self, cap, already):
        self.cap, self.spent, self.stopped = cap, already, False

    def allow(self):
        if self.spent >= self.cap:
            self.stopped = True
        return not self.stopped

    def add(self, usd):
        self.spent += usd


async def call_one(client, sem, task, budget, prices, run_meta):
    async with sem:
        if not budget.allow():
            return None
        last_error = None
        for attempt in range(1, MAX_RETRIES + 1):
            start = time.monotonic()
            try:
                resp = await client.chat.completions.create(
                    model=task["model_id"],
                    messages=[{"role": "system", "content": task["system_prompt"]},
                              {"role": "user", "content": task["user_prompt"]}],
                    reasoning_effort=task["reasoning_effort"],
                )
                latency = time.monotonic() - start
                ch, u = resp.choices[0], resp.usage
                ctd = getattr(u, "completion_tokens_details", None) if u else None
                ptd = getattr(u, "prompt_tokens_details", None) if u else None
                usage = {"prompt_tokens": u.prompt_tokens if u else None,
                         "completion_tokens": u.completion_tokens if u else None,
                         "total_tokens": u.total_tokens if u else None,
                         "reasoning_tokens": getattr(ctd, "reasoning_tokens", None) if ctd else None,
                         "cached_tokens": getattr(ptd, "cached_tokens", None) if ptd else None}
                cost = S.call_cost(task["model_id"], usage["prompt_tokens"], usage["completion_tokens"], prices)
                budget.add(cost)
                return {**task, **run_meta, "raw_output": ch.message.content, "finish_reason": ch.finish_reason,
                        "api_response_id": resp.id, "api_model_returned": resp.model, "api_created": resp.created,
                        "api_system_fingerprint": getattr(resp, "system_fingerprint", None),
                        "service_tier": getattr(resp, "service_tier", None), "usage": usage,
                        "cost_usd": round(cost, 8), "temperature": "omitted",
                        "call_timestamp_utc": datetime.now(timezone.utc).isoformat(),
                        "latency_seconds": round(latency, 3), "attempt": attempt, "error": None}
            except Exception as e:  # noqa: BLE001 -- logged and retried, never silently dropped
                last_error = f"{type(e).__name__}: {e}"
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(RETRY_BACKOFF_SECONDS * attempt)
        return {**task, **run_meta, "call_timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "attempt": MAX_RETRIES, "error": last_error, "cost_usd": 0.0}


async def run(plan, out_path, budget, run_meta):
    from dotenv import load_dotenv
    from openai import AsyncOpenAI
    load_dotenv()
    if not os.environ.get("OPENAI_API_KEY"):
        sys.exit("ERROR: OPENAI_API_KEY not set (expected in .env). Nothing was called.")
    client, prices, sem = AsyncOpenAI(), S.price_table(), asyncio.Semaphore(MAX_CONCURRENCY)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    n_ok = n_err = n_skip = 0
    with open(out_path, "a", encoding="utf-8") as f:
        for coro in asyncio.as_completed([call_one(client, sem, t, budget, prices, run_meta) for t in plan]):
            rec = await coro
            if rec is None:
                n_skip += 1
                continue
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
            if rec["error"]:
                n_err += 1
                print(f"ERROR {rec['item_id']} {rec['arm']} {rec['model_alias']}: {rec['error']}")
            else:
                n_ok += 1
                if n_ok % 200 == 0:
                    print(f"  {n_ok} ok, spent ${budget.spent:.2f}")
    return n_ok, n_err, n_skip


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--arms", nargs="*")
    ap.add_argument("--models", nargs="*")
    args = ap.parse_args()
    if (args.arms or args.models) and not (args.dry_run or args.pilot):
        sys.exit("ERROR: --arms/--models only with --dry-run or --pilot.")
    st = S.load_json(SETTINGS_PATH)
    if st.get("status") != "frozen" and not args.dry_run:
        sys.exit("ERROR: settings.json is still a draft. Confirm the decisions, set status to 'frozen', rebuild the "
                 "manifest and commit the freeze first (study2b/README.md). Nothing was called.")
    verify_manifest_2b()
    commit, dirty = git_state_2b()
    if not args.dry_run and (commit is None or dirty):
        sys.exit("ERROR: study2b/ design files are not committed. Nothing was called.")
    out_path = RAW_PILOT if args.pilot else RAW_FULL
    plan, st = build_plan(args.pilot, args.arms, args.models)
    sha = {t["arm"]: t["arm_prompt_sha256"] for t in plan}
    existing = [r for r in S.read_jsonl(out_path) if not r.get("error")]
    stale = sorted({r["arm"] for r in existing if r["arm"] in sha and r["arm_prompt_sha256"] != sha[r["arm"]]})
    if stale:
        sys.exit(f"ERROR: {out_path} holds outputs from another version of arms {stale}. Nothing was called.")
    done = {(r["item_id"], r["arm"], r["model_id"]) for r in existing}
    n_before = len(plan)
    plan = [t for t in plan if (t["item_id"], t["arm"], t["model_id"]) not in done]
    cap, already = st["budget_usd_cap"], spent_usd_2b()
    est = estimate_cost(plan) if plan else 0.0
    print(f"Plan: {len(plan)} calls ({n_before - len(plan)} already done) -> {out_path}")
    print(f"Budget: cap ${cap:.2f}, already spent ${already:.2f}, estimate (incl. {MARGIN - 1:.0%} margin) ${est:.2f}")
    if args.dry_run:
        print(f"Dry run OK: git commit {commit}, design files dirty={dirty}. No API call made, nothing written.")
        return
    if not plan:
        print("Nothing to do.")
        return
    if already + est > cap:
        sys.exit(f"ERROR: estimated spend ${already + est:.2f} exceeds the ${cap:.2f} cap. Nothing was called.")
    import openai
    if tuple(int(x) for x in openai.__version__.split(".")[:2]) < (1, 58):
        sys.exit(f"ERROR: openai {openai.__version__} has no reasoning_effort parameter; install openai>=1.58,<2 "
                 "(Study 2 ran with 1.59.9). Nothing was called.")
    run_meta = {"run_label": "pilot" if args.pilot else "full", "git_commit": commit,
                "openai_sdk_version": openai.__version__, "python_version": platform.python_version()}
    n_ok, n_err, n_skip = asyncio.run(run(plan, out_path, Budget(cap, already), run_meta))
    print(f"Done: {n_ok} ok, {n_err} errors, {n_skip} skipped by the budget guard.")


if __name__ == "__main__":
    main()
