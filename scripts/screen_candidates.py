#!/usr/bin/env python3
"""
Phase 2a of the PURE-150 extraction: apply the DETERMINISTIC half of
docs/item_selection.md's exclusion rules to every raw candidate from
Phase 1 (extract_candidates.py / extract_candidates_xml.py), so the
remaining pool is small enough for a human (me) to actually read and judge
on the rules that need real understanding — atomicity, whether the subject
is the system vs. a human actor, whether it's genuinely self-contained.

This script only ever REMOVES candidates or PASSES them through verbatim —
it never rewrites or trims text, so everything that survives is guaranteed
to still be an exact substring of the source document.

Deterministic rules applied here:
  - length bounds (too short = fragment/header; too long = almost certainly
    multiple bundled sentences glued together by extraction)
  - heading-based non-normative exclusion (definitions, rationale,
    background, examples, conventions, ...)
  - multiple modal verbs in one candidate = likely compound/bundled
  - exact and near-duplicate text within a document

Output: data/interim/screened/<document>.json — list of candidates with
verdict "pass" or "reject:<reason>". Only "pass" candidates move to the
manual review step.
"""
import glob
import json
import os
import re

CANDIDATE_DIRS = [
    os.path.join("data", "interim", "candidates"),
    os.path.join("data", "interim", "candidates_xml"),
]
OUT_DIR = os.path.join("data", "interim", "screened")

MIN_WORDS = 6
MAX_WORDS = 55

NON_NORMATIVE_HEADING_RE = re.compile(
    r"definition|glossary|terminolog|acronym|abbreviation|rationale|"
    r"background|purpose|scope\b|overview|convention|assumption|"
    r"reference\b|revision history|document history|change (log|control)|"
    r"table of contents|introduction\b|example|note\b",
    re.I,
)

MODAL_RE = re.compile(r"\bshall\b|\bmust\b", re.I)


def word_count(text):
    return len(text.split())


def normalize_for_dedup(text):
    t = text.lower()
    t = re.sub(r"^(req|fr|nfr|sr|r)[-_ ]?\d+\s*:?\s*", "", t)
    t = re.sub(r"[^a-z0-9 ]", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def screen_document(candidates):
    results = []
    seen_norm = {}
    for c in candidates:
        text = c["text"]
        heading = c.get("nearest_heading") or ""
        wc = word_count(text)
        norm_text = normalize_for_dedup(text)

        verdict = "pass"
        reason = None

        if wc < MIN_WORDS:
            verdict, reason = "reject", "too_short"
        elif wc > MAX_WORDS:
            verdict, reason = "reject", "too_long_likely_compound"
        elif NON_NORMATIVE_HEADING_RE.search(heading):
            verdict, reason = "reject", "non_normative_heading"
        elif len(MODAL_RE.findall(text)) >= 2:
            verdict, reason = "reject", "multiple_modals_likely_compound"
        elif re.search(r"\bshall\b.*\band\b.*\bshall\b", text, re.I):
            verdict, reason = "reject", "compound_multiple_shall"
        elif not norm_text:
            verdict, reason = "reject", "empty_after_normalization"
        elif norm_text in seen_norm:
            verdict, reason = "reject", f"duplicate_of_{seen_norm[norm_text]}"
        else:
            seen_norm[norm_text] = c["id"]

        results.append({**c, "verdict": verdict, "reject_reason": reason})
    return results


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    total_pass = 0
    total_all = 0
    for cand_dir in CANDIDATE_DIRS:
        for path in sorted(glob.glob(os.path.join(cand_dir, "*.json"))):
            candidates = json.load(open(path, encoding="utf-8"))
            screened = screen_document(candidates)
            out_name = os.path.basename(path)
            out_path = os.path.join(OUT_DIR, out_name)
            # If both candidate dirs produce a same-named doc (shouldn't,
            # given naming), don't silently overwrite.
            if os.path.exists(out_path):
                out_path = os.path.join(OUT_DIR, f"xml_{out_name}")
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(screened, f, indent=2, ensure_ascii=False)
            n_pass = sum(1 for r in screened if r["verdict"] == "pass")
            print(f"{out_name:45s} {len(screened):5d} raw -> {n_pass:4d} pass")
            total_pass += n_pass
            total_all += len(screened)
    print(f"\nTotal: {total_all} raw -> {total_pass} pass")


if __name__ == "__main__":
    main()
