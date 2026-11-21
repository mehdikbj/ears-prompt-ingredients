#!/usr/bin/env python3
"""
Part H (ANALYSIS_PLAN.md): blind rating sheets for R1 and R3 on 150 NEW Study 2b outputs that
neither rater has seen: the 50 Study 2 sample items x the three reasoning levels of the base prompt
(B_base_none, B_base_written, B_base_native). Each item is assigned one tier by a seeded balanced draw,
so the three outputs of an item come from the same tier. Run after study2b/results/checks_2b.jsonl exists.

  python3 study2b/human_eval/build_sheets_2b.py

Writes sheets/04_sheet1_criteria_<R1|R3>.csv (four criteria vs the informal input),
sheets/05_sheet2_equivalence_<R1|R3>.csv (equivalence to the PURE source; send only after sheet 1 is
committed), and the git-ignored key key_2b.jsonl with its SHA-256 in key_2b.sha256.
"""
import csv
import hashlib
import json
import os
import random
import secrets
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
from s2bcommon import CHECKS, S  # noqa: E402

ARMS = ["B_base_none", "B_base_written", "B_base_native"]
TIERS = ["gpt-5.4-nano", "gpt-5.4-mini", "gpt-5.4"]
RATERS = ["R1", "R3"]
TIER_SEED = 202611083
SHEET1 = ["sample_id", "messified_input", "generated_requirement", "faithfulness", "unambiguity", "singularity",
          "ears_wellformedness", "notes"]
SHEET2 = ["sample_id", "original_requirement", "generated_requirement", "equivalence", "notes"]


def main(checks_path=CHECKS):
    key_path = f"{HERE}/key_2b.jsonl"
    if os.path.exists(key_path):
        sys.exit(f"{key_path} exists: sheets were already built. Never rebuild after sheets are sent.")
    items = sorted(S.load_json("study2/config/human_subsample_items.json")["item_ids"])
    assert len(items) == 50
    order = items[:]
    random.Random(TIER_SEED).shuffle(order)
    tier_of = {i: TIERS[k % 3] for k, i in enumerate(order)}
    rows = {(r["item_id"], r["arm"], r["model_alias"]): r for r in S.read_jsonl(checks_path)}
    inputs = {i["id"]: i["messified_text"] for i in S.load_json(S.MESSIFIED)}
    gold = {g["id"]: g["text"] for g in S.load_json(S.PURE150)}
    salt = secrets.randbits(64)
    rng = random.Random(salt)
    key, missing = [], []
    for i in items:
        for a in ARMS:
            r = rows.get((i, a, tier_of[i]))
            if r is None or not r.get("extraction_ok"):
                missing.append((i, a, tier_of[i]))
                continue
            key.append(dict(item_id=i, arm=a, model_alias=tier_of[i], rated=True,
                            ears_v2_compliant=r["ears_v2_compliant"], requirement_text=r["requirement_text"]))
    ids = [f"V{n:04d}" for n in range(1, len(key) + 1)]
    rng.shuffle(ids)
    for k, sid in zip(key, ids):
        k.update(sample_id=sid, salt=salt)
    os.makedirs(f"{HERE}/sheets", exist_ok=True)
    for rater in RATERS:
        for name, cols, row in [("04_sheet1_criteria", SHEET1,
                                 lambda k: [k["sample_id"], inputs[k["item_id"]], k["requirement_text"], "", "", "", "", ""]),
                                ("05_sheet2_equivalence", SHEET2,
                                 lambda k: [k["sample_id"], gold[k["item_id"]], k["requirement_text"], "", ""])]:
            shuffled = key[:]
            rng.shuffle(shuffled)
            with open(f"{HERE}/sheets/{name}_{rater}.csv", "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(cols)
                w.writerows(row(k) for k in shuffled)
    with open(key_path, "w", encoding="utf-8") as f:
        f.write("".join(json.dumps(k, ensure_ascii=False) + "\n" for k in key))
    h = hashlib.sha256(open(key_path, "rb").read()).hexdigest()
    with open(f"{HERE}/key_2b.sha256", "w") as f:
        f.write(f"{h}  key_2b.jsonl\n")
    print(f"{len(key)} outputs per sheet ({len(missing)} not extractable, not rated: {missing}); key SHA-256 {h}")


if __name__ == "__main__":
    main()
