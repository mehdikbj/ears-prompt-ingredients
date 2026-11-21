#!/usr/bin/env python3
"""
Phase 1 of the PURE-150 extraction (docs/item_selection.md, Step 4.1-2):
mechanically collect the RAW candidate pool per source document — every
shall/must sentence and every explicitly labeled requirement ID — verbatim,
with a best-effort nearby heading for context.

This step does NOT apply the inclusion/exclusion judgment calls (compound
statements, non-normative prose, process obligations, duplicates, etc.) —
that happens in a separate review pass over this script's output, precisely
so that "which text is real" (this script, deterministic) stays separate
from "which text qualifies" (judgment, reviewed separately and verified
against this script's output afterward).

Output: one JSON file per document in data/interim/candidates/, containing
a list of {id, document, nearest_heading, text} objects. `text` is always a
verbatim substring of the source plaintext.
"""
import json
import os
import re

PLAINTEXT_DIR = os.path.join("data", "interim", "pure_plaintext")
OUT_DIR = os.path.join("data", "interim", "candidates")

LABELED_RE = re.compile(r"\b(?:REQ|FR|NFR|SR|UC|R)[-_ ]?\d{1,4}\b")
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
HEADING_RE = re.compile(r"^\s{0,4}(\d+(\.\d+)*\.?\s+\S.{0,80}|[A-Z][A-Z0-9 /\-]{4,60})\s*$")

# Primary 19 documents approved in docs/item_selection.md, Section 2.
PRIMARY_DOCS = [
    "2001 - npac [doc].txt",
    "1999 - tcs [pdf].txt",
    "2000 - nasa x38 [doc].txt",
    "2005 - clarus low [pdf].txt",
    "2007 - eirene fun 7 [pdf].txt",
    "2007 - nde [pdf].txt",
    "2007 - ertms [pdf].txt",
    "2005 - pontis [pdf].txt",
    "2004 - rlcs [pdf].txt",
    "1995 - gemini [pdf].txt",
    "2009 - peppol [pdf].txt",
    "2010 - fishing [pdf].txt",
    "2009 - inventory 2.0 [pdf].txt",
    "2005 - phin [pdf].txt",
    "2009 - warc III [pdf].txt",
    "2006 - stewards [pdf].txt",
    "2008 - keepass [pdf].txt",
    "2008 - peering [pdf].txt",
    "2009 - video search [pdf].txt",
]

# Documented backups, in case a primary document underdelivers after review.
BACKUP_DOCS = [
    "2006 - eirene sys 15 [pdf].txt",
    "2001 - hats [pdf].txt",
    "2004 - grid bgc [pdf].txt",
    "2007 - mdot [pdf].txt",
]


def nearest_heading_before(lines, line_idx, window=15):
    for i in range(line_idx, max(-1, line_idx - window), -1):
        line = lines[i].strip()
        if line and HEADING_RE.match(line) and len(line.split()) <= 12:
            return line
    return None


def extract_from_document(doc_filename):
    path = os.path.join(PLAINTEXT_DIR, doc_filename)
    text = open(path, encoding="utf-8", errors="ignore").read()
    lines = text.split("\n")

    # Map each character offset to a line index for heading lookup.
    line_start_offsets = []
    offset = 0
    for line in lines:
        line_start_offsets.append(offset)
        offset += len(line) + 1

    def line_index_for_offset(char_offset):
        lo, hi = 0, len(line_start_offsets) - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if line_start_offsets[mid] <= char_offset:
                lo = mid
            else:
                hi = mid - 1
        return lo

    candidates = []
    seen_texts = set()
    doc_id = os.path.splitext(doc_filename)[0]
    counter = 0

    # Sentence-level shall/must candidates.
    sentences = SENTENCE_SPLIT_RE.split(text)
    cursor = 0
    for sent in sentences:
        start = text.find(sent, cursor)
        if start == -1:
            start = cursor
        cursor = start + len(sent)
        clean = sent.strip().replace("\n", " ")
        clean = re.sub(r"\s+", " ", clean)
        if not clean or clean in seen_texts:
            continue
        if re.search(r"\bshall\b|\bmust\b", clean, re.I):
            li = line_index_for_offset(start)
            heading = nearest_heading_before(lines, li)
            counter += 1
            candidates.append({
                "id": f"{doc_id}__C{counter:04d}",
                "document": doc_filename,
                "nearest_heading": heading,
                "text": clean,
                "match_type": "modal_verb",
            })
            seen_texts.add(clean)

    # Explicitly labeled items (REQ-1, FR3, R14, ...): capture the labeled
    # token's containing line as a candidate too, since labeled items are
    # sometimes phrased without shall/must.
    for i, line in enumerate(lines):
        if LABELED_RE.search(line):
            clean = line.strip()
            clean = re.sub(r"\s+", " ", clean)
            if not clean or clean in seen_texts or len(clean.split()) < 4:
                continue
            heading = nearest_heading_before(lines, i)
            counter += 1
            candidates.append({
                "id": f"{doc_id}__C{counter:04d}",
                "document": doc_filename,
                "nearest_heading": heading,
                "text": clean,
                "match_type": "labeled_id",
            })
            seen_texts.add(clean)

    return candidates


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    all_docs = PRIMARY_DOCS + BACKUP_DOCS
    summary = []
    for doc in all_docs:
        path = os.path.join(PLAINTEXT_DIR, doc)
        if not os.path.exists(path):
            print(f"MISSING: {doc}")
            continue
        candidates = extract_from_document(doc)
        out_path = os.path.join(OUT_DIR, os.path.splitext(doc)[0] + ".json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(candidates, f, indent=2, ensure_ascii=False)
        summary.append((doc, len(candidates)))
        print(f"{doc:45s} {len(candidates):5d} raw candidates -> {out_path}")

    print(f"\nTotal raw candidates: {sum(n for _, n in summary)}")


if __name__ == "__main__":
    main()
