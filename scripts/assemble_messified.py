#!/usr/bin/env python3
"""
Assembles data/pure_150_messified.json from the raw generated items in
data/interim/messify_batches/_combined_raw.json, adding the schema fields
from docs/inputs.md Section 6 (word_count, generator_model,
generated_date), and validates:
  - exactly 150 items, ids PURE-001..PURE-150, no duplicates/missing
  - every id exists in data/pure_150.json

Run scripts/check_messified.py afterward for the no-leak/consistency gate
(kept separate since that script is also meant to be re-run standalone).
"""
import json
import os

PURE_150_PATH = "data/pure_150.json"
RAW_PATH = "data/interim/messify_batches/_combined_raw.json"
OUT_PATH = "data/pure_150_messified.json"

GENERATOR_MODEL = "claude-sonnet-5"
GENERATED_DATE = "2026-08-27"


def main():
    source_ids = {d["id"] for d in json.load(open(PURE_150_PATH, encoding="utf-8"))}
    raw = json.load(open(RAW_PATH, encoding="utf-8"))

    seen = set()
    dataset = []
    errors = []

    for item in raw:
        item_id = item["id"]
        text = item["messified_text"]
        if item_id in seen:
            errors.append(f"duplicate id: {item_id}")
            continue
        seen.add(item_id)
        if item_id not in source_ids:
            errors.append(f"id not in {PURE_150_PATH}: {item_id}")
            continue
        dataset.append({
            "id": item_id,
            "messified_text": text,
            "word_count": len(text.split()),
            "generator_model": GENERATOR_MODEL,
            "generated_date": GENERATED_DATE,
        })

    missing = source_ids - seen
    if missing:
        errors.append(f"missing ids: {sorted(missing)}")

    if errors:
        print("ERRORS:")
        for e in errors:
            print(" -", e)
        raise SystemExit(1)

    dataset.sort(key=lambda d: int(d["id"].split("-")[1]))

    if len(dataset) != 150:
        print(f"ERROR: expected 150 items, got {len(dataset)}")
        raise SystemExit(1)

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)

    print(f"Wrote {len(dataset)} items to {OUT_PATH}")


if __name__ == "__main__":
    main()
