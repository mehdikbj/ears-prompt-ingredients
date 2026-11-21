#!/usr/bin/env python3
"""
Study 2 inference: 150 messified items x 10 arms x 3 pinned GPT-5.4 snapshots
= 4,500 calls (pilot: 5 frozen items = 150 calls).

  python3 study2/scripts/run_inference_study2.py --dry-run           # no API calls; validates the plan
  python3 study2/scripts/run_inference_study2.py --pilot             # 150 calls -> results/pilot/
  python3 study2/scripts/run_inference_study2.py                     # full run -> results/

Same call as the prior exploratory run (archive/study1/scripts/run_inference.py):
chat.completions, system =
arm prompt, user = messified text, temperature 0, no max_tokens, no
reasoning_effort (the API default, 'none' for these snapshots). Pinned
dated snapshot IDs from config/model_lineup.json, never the alias.

Safeguards (all before the first API call):
  - every frozen file must match prompts/MANIFEST.json;
  - the study2/ design files must be committed (clean git tree), so every
    record can point to the exact commit that produced it;
  - the estimated cost of the remaining plan must fit in the budget cap
    (frozen_settings.json, $15 for pilot + full run together);
  - during the run, no new call starts once logged spend reaches the cap.

Every record logs the assembled prompts, raw output, all model/version
fields the API returns, token usage including reasoning and cached tokens,
the cost, the arm's prompt SHA-256, the git commit, and the SDK version.
Records are appended as they complete; re-running resumes and skips
completed (item, arm, model) triples. Calls are issued in a seeded random
order so that time-of-run is not confounded with arm or tier.
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
from estimate_cost import estimate
from s2common import (ARM_DIR, ARMS_PATH, FROZEN_PATH, LINEUP, MESSIFIED, RAW_FULL, RAW_PILOT, call_cost, git_state,
                      load_json, parse_template, price_table, read_jsonl, read_text, sha256_file, spent_usd,
                      verify_manifest)

MAX_CONCURRENCY = 5
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 5


def build_plan(pilot, arms_filter=None, models_filter=None):
    frozen = load_json(FROZEN_PATH)
    lineup = load_json(LINEUP)
    if not lineup.get("locked"):
        raise RuntimeError("config/model_lineup.json is not locked")
    items = load_json(MESSIFIED)
    if pilot:
        keep = set(frozen["pilot"]["item_ids"])
        items = [i for i in items if i["id"] in keep]
    arms = load_json(ARMS_PATH)["arms"]
    if arms_filter:
        arms = [a for a in arms if a["arm"] in arms_filter]
    tiers = lineup["tiers"]
    if models_filter:
        tiers = [t for t in tiers if t["name"] in models_filter or t["model_id"] in models_filter]
    plan = []
    for arm in arms:
        path = f"{ARM_DIR}/{arm['arm']}.txt"
        system, user_t = parse_template(read_text(path))
        if user_t != "{{messified_text}}":
            raise ValueError(f"{path}: user message must be exactly {{{{messified_text}}}}")
        prompt_sha = sha256_file(path)
        for item in items:
            for t in tiers:
                plan.append({
                    "item_id": item["id"], "arm": arm["arm"], "family": arm["family"],
                    "E": arm["E"], "C": arm["C"], "R": arm["R"], "output_format": arm["output"],
                    "model_id": t["dated_snapshot_id"], "model_alias": t["model_id"], "model_tier": t["tier"],
                    "arm_prompt_sha256": prompt_sha,
                    "system_prompt": system, "user_prompt": item["messified_text"],
                })
    random.Random(frozen["seeds"]["call_order_shuffle"]).shuffle(plan)
    return plan, frozen


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
                    temperature=0,
                )
                latency = time.monotonic() - start
                ch = resp.choices[0]
                u = resp.usage
                ctd = getattr(u, "completion_tokens_details", None) if u else None
                ptd = getattr(u, "prompt_tokens_details", None) if u else None
                usage = {
                    "prompt_tokens": u.prompt_tokens if u else None,
                    "completion_tokens": u.completion_tokens if u else None,
                    "total_tokens": u.total_tokens if u else None,
                    "reasoning_tokens": getattr(ctd, "reasoning_tokens", None) if ctd else None,
                    "cached_tokens": getattr(ptd, "cached_tokens", None) if ptd else None,
                }
                cost = call_cost(task["model_id"], usage["prompt_tokens"], usage["completion_tokens"], prices)
                budget.add(cost)
                return {**task, **run_meta,
                        "raw_output": ch.message.content, "finish_reason": ch.finish_reason,
                        "api_response_id": resp.id, "api_model_returned": resp.model, "api_created": resp.created,
                        "api_system_fingerprint": getattr(resp, "system_fingerprint", None),
                        "service_tier": getattr(resp, "service_tier", None),
                        "usage": usage, "cost_usd": round(cost, 8), "temperature": 0,
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
    client = AsyncOpenAI()
    prices = price_table()
    sem = asyncio.Semaphore(MAX_CONCURRENCY)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    n_ok = n_err = n_skipped = 0
    with open(out_path, "a", encoding="utf-8") as f:
        for coro in asyncio.as_completed([call_one(client, sem, t, budget, prices, run_meta) for t in plan]):
            rec = await coro
            if rec is None:
                n_skipped += 1
                continue
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
            if rec["error"]:
                n_err += 1
                print(f"ERROR {rec['item_id']} {rec['arm']} {rec['model_alias']}: {rec['error']}")
            else:
                n_ok += 1
                if n_ok % 100 == 0:
                    print(f"  {n_ok} ok, spent ${budget.spent:.2f}")
    return n_ok, n_err, n_skipped


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", action="store_true", help="Run the 5 frozen pilot items only (output under results/pilot/).")
    ap.add_argument("--dry-run", action="store_true", help="Build and validate the plan; no API call, nothing written.")
    ap.add_argument("--arms", nargs="*", help="Subset of arms (debugging only; not for the reported run).")
    ap.add_argument("--models", nargs="*", help="Subset of tiers by name, e.g. nano (debugging only).")
    args = ap.parse_args()
    if (args.arms or args.models) and not (args.dry_run or args.pilot):
        sys.exit("ERROR: --arms/--models are for debugging and only allowed with --dry-run or --pilot.")

    verify_manifest()
    commit, dirty = git_state()
    if not args.dry_run and (commit is None or dirty):
        sys.exit("ERROR: study2/ design files are not committed (or git is unavailable). "
                 "Commit the freeze first (see study2/RUNBOOK.md). Nothing was called.")

    out_path = RAW_PILOT if args.pilot else RAW_FULL
    plan, frozen = build_plan(args.pilot, args.arms, args.models)
    current_sha = {t["arm"]: t["arm_prompt_sha256"] for t in plan}
    existing = [r for r in read_jsonl(out_path) if not r.get("error")]
    stale = sorted({r["arm"] for r in existing if r["arm"] in current_sha and r["arm_prompt_sha256"] != current_sha[r["arm"]]})
    if stale:
        sys.exit(f"ERROR: {out_path} holds outputs from a different version of arms {stale}. Results from two prompt "
                 "versions must never be mixed: log the deviation and write to a new output file. Nothing was called.")
    done = {(r["item_id"], r["arm"], r["model_id"]) for r in existing}
    before = len(plan)
    plan = [t for t in plan if (t["item_id"], t["arm"], t["model_id"]) not in done]

    cap = frozen["budget_usd_cap"]
    already = spent_usd()
    n_items = len({t["item_id"] for t in plan}) or 0
    _, est_full = estimate(150)
    est = est_full * len(plan) / 4500 if plan else 0.0
    print(f"Plan: {len(plan)} calls to make ({before - len(plan)} already done) -> {out_path}")
    print(f"Budget: cap ${cap:.2f}, already spent ${already:.2f}, estimate for this plan ${est:.2f}")
    if args.dry_run:
        arms = sorted({t["arm"] for t in plan})
        print(f"Dry run OK: {n_items} items, {len(arms)} arms, git commit {commit}, design files dirty={dirty}. "
              "No API call made, nothing written.")
        return
    if not plan:
        print("Nothing to do.")
        return
    if already + est > cap:
        sys.exit(f"ERROR: estimated spend ${already + est:.2f} exceeds the ${cap:.2f} cap. Nothing was called.")

    import openai
    run_meta = {"run_label": "pilot" if args.pilot else "full", "git_commit": commit,
                "openai_sdk_version": openai.__version__, "python_version": platform.python_version()}
    budget = Budget(cap, already)
    n_ok, n_err, n_skip = asyncio.run(run(plan, out_path, budget, run_meta))
    print(f"\nDone: {n_ok} ok, {n_err} errors, {n_skip} not started (budget). Total spent ${budget.spent:.2f}.")
    if budget.stopped:
        print("STOPPED: budget cap reached. Report this as a deviation before raising the cap.")
    if n_err:
        print("Re-run the same command to retry failed calls (completed ones are skipped).")


if __name__ == "__main__":
    main()
