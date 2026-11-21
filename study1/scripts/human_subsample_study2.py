#!/usr/bin/env python3
"""
Study 2 paired human subsample.

  python3 study2/scripts/human_subsample_study2.py select        # BEFORE any API call; output is frozen
  python3 study2/scripts/human_subsample_study2.py build-sheets  # AFTER check_study2.py on the full run

select: draws 50 of the 150 items, stratified by PURE source document with
proportional allocation (largest-remainder rounding, ties broken in a seeded
random order), then a seeded random draw within each document. Depends only
on item metadata, never on model outputs. Writes
study2/config/human_subsample_items.json.

build-sheets: for each selected item, takes the outputs of the three rated
arms (F_base, F_E, F_R) on all three tiers = 450 outputs. Each output gets a
neutral ID; each rater gets the same 450 outputs in a different order. IDs and
orders come from a secret random salt drawn at build time, so the key cannot be
rebuilt from the repository. Writes the blind rater kit (study2/rater_kit/) and
the hidden key (study2/results/human_eval_key_study2.jsonl: git-ignored until
all ratings are back, never shared with raters).
Outputs with no extractable requirement are not rated and are listed in the
key with rated=false.
"""
import csv
import json
import os
import random
import secrets
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from s2common import CHECKS, FROZEN_PATH, MESSIFIED, PURE150, RESULTS, S2, load_json, read_jsonl

SELECTION = f"{S2}/config/human_subsample_items.json"
KIT = f"{S2}/rater_kit"
KEY = f"{RESULTS}/human_eval_key_study2.jsonl"
N_ITEMS = 50
RATED_ARMS = ["F_base", "F_E", "F_R"]
# Two raters (author decision, 2026-11-07). R2 took part in the 2026-10-01 calibration only.
RATERS = {"R1": "R1", "R3": "R3"}
CRITERIA = ["faithfulness", "unambiguity", "singularity", "ears_wellformedness"]


def select():
    seed = load_json(FROZEN_PATH)["seeds"]["human_subsample"]
    rng = random.Random(seed)
    items = load_json(PURE150)
    by_doc = {}
    for it in items:
        by_doc.setdefault(it["source_document_key"], []).append(it["id"])
    docs = sorted(by_doc)
    quota = {d: N_ITEMS * len(by_doc[d]) / len(items) for d in docs}
    alloc = {d: int(quota[d]) for d in docs}
    order = docs[:]
    rng.shuffle(order)  # tie-break order for equal remainders
    rank = sorted(order, key=lambda d: -(quota[d] - alloc[d]))
    for d in rank[: N_ITEMS - sum(alloc.values())]:
        alloc[d] += 1
    chosen = []
    for d in docs:
        chosen += rng.sample(sorted(by_doc[d]), alloc[d])
    chosen.sort()
    assert len(chosen) == N_ITEMS and len(set(chosen)) == N_ITEMS
    out = {
        "_comment": "Paired human subsample for Study 2. Drawn by human_subsample_study2.py select from item metadata "
                    "only, before any Study 2 API call. Frozen in the freeze commit.",
        "seed": seed, "n_items": N_ITEMS, "stratified_by": "source_document_key",
        "allocation": "proportional, largest-remainder rounding, seeded tie-break",
        "rated_arms": RATED_ARMS, "tiers": "all three", "raters": RATERS,
        "per_document": {d: alloc[d] for d in docs},
        "item_ids": chosen,
    }
    with open(SELECTION, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
        f.write("\n")
    print(f"Selected {len(chosen)} items from {len(docs)} documents -> {SELECTION}")
    print(dict(Counter({d: alloc[d] for d in docs})))


def build_sheets():
    sel = load_json(SELECTION)
    inputs = {i["id"]: i["messified_text"] for i in load_json(MESSIFIED)}
    checks = {(r["item_id"], r["arm"], r["model_alias"]): r for r in read_jsonl(CHECKS)}
    if not checks:
        sys.exit(f"{CHECKS} not found: run check_study2.py on the full run first")
    tiers = sorted({k[2] for k in checks})
    units = [(i, a, t) for i in sel["item_ids"] for a in RATED_ARMS for t in tiers]
    missing = [u for u in units if u not in checks]
    if missing:
        sys.exit(f"{len(missing)} required outputs missing from {CHECKS}, e.g. {missing[:3]}")
    salt = secrets.randbits(64)  # recorded only in the hidden key
    rng = random.Random(salt)
    shuffled = units[:]
    rng.shuffle(shuffled)
    key, sample = [], []
    for n, (i, a, t) in enumerate(shuffled, 1):
        c = checks[(i, a, t)]
        sid = f"T{n:04d}"
        rated = bool(c["extraction_ok"])
        key.append({"sample_id": sid, "salt": salt, "item_id": i, "arm": a, "model_alias": t, "rated": rated,
                    "ears_v2_compliant": c["ears_v2_compliant"], "requirement_text": c["requirement_text"]})
        if rated:
            sample.append({"sample_id": sid, "messified_input": inputs[i], "generated_requirement": c["requirement_text"]})
    os.makedirs(KIT, exist_ok=True)
    with open(KEY, "w", encoding="utf-8") as f:
        for k in key:
            f.write(json.dumps(k, ensure_ascii=False) + "\n")
    with open(f"{KIT}/03_study2_sample.jsonl", "w", encoding="utf-8") as f:
        for s in sorted(sample, key=lambda s: s["sample_id"]):
            f.write(json.dumps(s, ensure_ascii=False) + "\n")
    for k, (rid, name) in enumerate(RATERS.items()):
        rows = sample[:]
        random.Random(salt + k + 1).shuffle(rows)
        with open(f"{KIT}/04_study2_rating_sheet_{name}.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["sample_id", "messified_input", "generated_requirement", *CRITERIA, "notes"])
            for s in rows:
                w.writerow([s["sample_id"], s["messified_input"], s["generated_requirement"], "", "", "", "", ""])
    n_unrated = sum(not k["rated"] for k in key)
    print(f"{len(units)} outputs ({len(sample)} to rate, {n_unrated} not rateable). "
          f"Wrote {KIT}/ (blind) and {KEY} (hidden key: never share).")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "select":
        select()
    elif cmd == "build-sheets":
        build_sheets()
    else:
        sys.exit(__doc__)
