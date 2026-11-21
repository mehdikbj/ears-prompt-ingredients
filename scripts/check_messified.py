#!/usr/bin/env python3
"""
Automated QC gate for messified inputs (task 1.7), per
docs/inputs.md Section 5. Runs BEFORE task 1.8's human
review — this catches mechanical leakage/consistency problems so the human
review is checking realism and faithfulness, not doing the mechanical check
by eye.

Checks per item (joined against data/pure_150.json by id):
  - HARD FAIL: literal "shall" present (case-insensitive)
  - HARD FAIL: a shared contiguous span of 6+ words with the source text
  - SOFT FLAG: literal "must" present
  - SOFT FLAG: word count outside [25, 70]
  - SOFT FLAG: no vagueness marker from a small lexicon found

Usage: python3 scripts/check_messified.py [path/to/messified.json]
Defaults to data/pure_150_messified.json. Exits non-zero if any item
hard-fails (a hard-fail means that item must be regenerated, not shipped).
"""
import json
import re
import sys

PURE_150_PATH = "data/pure_150.json"
DEFAULT_MESSIFIED_PATH = "data/pure_150_messified.json"

VAGUE_LEXICON = [
    "kind of", "sort of", "probably", "something like", "not sure exactly",
    "i guess", "i think", "maybe", "roughly", "or so", "some way",
    "pretty much", "basically", "at some point", "a bit", "a while",
    "not exactly sure", "some kind of", "i mean", "you know", "oh, and",
    "quick", "quickly", "soon", "eventually", "somehow",
    "or whatever", "whatever", "whatnot", "kinda", "gonna", "some kind",
    "not a huge deal", "or something", "whichever", "somewhere",
    "doesn't have to be", "nothing crazy", "not exactly", "not forced",
    "just there if", "whoever", "not just", "like a", "like,",
]


def word_count(text):
    return len(text.split())


def shared_span(a, b, min_words=6):
    """Return True if a and b share a contiguous run of >= min_words words."""
    wa = re.findall(r"\S+", a.lower())
    wb = re.findall(r"\S+", b.lower())
    set_b_ngrams = set()
    for i in range(len(wb) - min_words + 1):
        set_b_ngrams.add(tuple(wb[i:i + min_words]))
    for i in range(len(wa) - min_words + 1):
        if tuple(wa[i:i + min_words]) in set_b_ngrams:
            return True, " ".join(wa[i:i + min_words])
    return False, None


def check_item(source_text, messified_text):
    hard_fails = []
    soft_flags = []

    if re.search(r"\bshall\b", messified_text, re.I):
        hard_fails.append("contains 'shall'")

    overlap, span = shared_span(source_text, messified_text, min_words=6)
    if overlap:
        hard_fails.append(f"shares 6+ word span with source: {span!r}")

    if re.search(r"\bmust\b", messified_text, re.I):
        soft_flags.append("contains 'must'")

    wc = word_count(messified_text)
    if not (25 <= wc <= 70):
        soft_flags.append(f"word count {wc} outside [25, 70]")

    lower = messified_text.lower()
    if not any(term in lower for term in VAGUE_LEXICON):
        soft_flags.append("no vagueness marker found")

    return hard_fails, soft_flags


def main():
    messified_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_MESSIFIED_PATH

    source = {d["id"]: d["text"] for d in json.load(open(PURE_150_PATH, encoding="utf-8"))}
    messified = json.load(open(messified_path, encoding="utf-8"))

    results = []
    n_hard = 0
    n_soft = 0
    for m in messified:
        item_id = m["id"]
        if item_id not in source:
            results.append({"id": item_id, "hard_fails": [f"unknown id, not in {PURE_150_PATH}"], "soft_flags": []})
            n_hard += 1
            continue
        hard_fails, soft_flags = check_item(source[item_id], m["messified_text"])
        results.append({"id": item_id, "hard_fails": hard_fails, "soft_flags": soft_flags})
        if hard_fails:
            n_hard += 1
        if soft_flags:
            n_soft += 1

    print(f"{len(messified)} items checked: {n_hard} hard-fail, {n_soft} soft-flag (may overlap)\n")
    for r in results:
        if r["hard_fails"] or r["soft_flags"]:
            print(f"{r['id']}:")
            for f in r["hard_fails"]:
                print(f"  HARD FAIL: {f}")
            for f in r["soft_flags"]:
                print(f"  soft flag: {f}")

    out_path = messified_path.replace(".json", "_qc_report.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nFull report written to {out_path}")

    if n_hard:
        sys.exit(1)


if __name__ == "__main__":
    main()
