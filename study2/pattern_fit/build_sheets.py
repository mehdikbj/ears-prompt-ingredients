#!/usr/bin/env python3
"""
Build the blank pattern-admissibility sheets for annotators A and B (150 inputs each,
different seeded orders) and the consolidation template. No model output is shown.

  python3 study2b/pattern_fit/build_sheets.py
"""
import csv
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
from s2bcommon import PATTERN_FIT_DIR, S  # noqa: E402

COLS = ["item_id", "input", "adm_ubiquitous", "adm_event_driven", "adm_unwanted_behaviour", "adm_state_driven",
        "adm_optional_feature", "adm_complex", "best_pattern", "notes"]
SEEDS = {"A": 202611081, "B": 202611082}


def main():
    items = [(i["id"], i["messified_text"]) for i in S.load_json(S.MESSIFIED)]
    assert len(items) == 150
    for who, seed in SEEDS.items():
        order = items[:]
        random.Random(seed).shuffle(order)
        path = f"{PATTERN_FIT_DIR}/02_sheet_annotator_{who}.csv"
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(COLS)
            for iid, text in order:
                w.writerow([iid, text, "", "", "", "", "", "", "", ""])
        with open(f"{PATTERN_FIT_DIR}/04_time_log_{who}.csv", "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows([["date", "start_local_time", "end_local_time", "items_done"]])
    with open(f"{PATTERN_FIT_DIR}/03_consolidated.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(COLS + ["resolution_note"])
        for iid, text in sorted(items):
            w.writerow([iid, text] + [""] * 8 + [""])
    print("Wrote sheets for A and B, time logs, and 03_consolidated.csv")


if __name__ == "__main__":
    main()
