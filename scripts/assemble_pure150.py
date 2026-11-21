#!/usr/bin/env python3
"""
Phase 4 (final) of the PURE-150 extraction: verify every manually-selected
item in scripts/eligible_pool.py is a genuine verbatim substring of its
named source document, then assemble data/pure_150.json.

This is the integrity backstop for the whole pipeline: if any entry in
eligible_pool.py were mistyped, paraphrased, or otherwise not an exact
quote from PURE, this script fails loudly instead of silently writing a
fabricated "gold standard" item. Matching is done after collapsing
whitespace (spaces/newlines/tabs) to a single space on both sides, since
source PDFs/XML wrap lines and eligible_pool.py sometimes reflows an item
across lines for readability — but no other transformation is applied, so
a genuine wording mismatch still fails the check.

Each item is a (text, section, req_id) triple, or a (text, section, req_id,
strip) quadruple. `text` is always verified whole against the source first
— that check never changes. `strip`, when present, is a list of exact
substrings (e.g. an inline "[SRS197] " tag, or a leading "REQ-1: " label)
that are then removed from the verified `text` to produce the stored
`text` — used only to drop a source-document ID/label already captured in
`source_requirement_id`, never to reword content. Each strip substring must
itself be found in `text` (after the same whitespace normalization) or the
script fails — so a stripped tag is always something that was verifiably
really there, not a free-form edit.

Run: python3 scripts/assemble_pure150.py
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from eligible_pool import ELIGIBLE

PLAINTEXT_DIR = os.path.join("data", "interim", "pure_plaintext")
XML_DIR = os.path.join("data", "raw", "requirements_xml", "XMLZIPFile")
OUT_PATH = os.path.join("data", "pure_150.json")

# EIRENE-style trailing compliance marker: (M)andatory / (I)nformation /
# (O)ptional, as defined by the source document itself (EIRENE FRS §1.3.3).
# Real content (not an ID), so it's pulled into its own field rather than
# dropped — see the "Move to metadata" decision in the extraction log.
# NOTE: "Information" per the source's own wording — not "Informative".
# Per that same source definition, (I) items are "explanatory notes," which
# docs/item_selection.md's own rules already exclude (non-normative
# prose) — so no eligible eirene_fun_7 item should carry this tag; if one
# ever does, that's a sign eligible_pool.py needs re-reviewing, not that
# this label is wrong.
COMPLIANCE_MARKER_RE = re.compile(r"\s\(([MIO])\)$")
COMPLIANCE_LABELS = {"M": "Mandatory", "I": "Information", "O": "Optional"}


def normalize(s):
    return re.sub(r"\s+", " ", s).strip()


def load_source_text(source_file):
    if source_file.endswith(".xml"):
        path = os.path.join(XML_DIR, source_file)
    else:
        path = os.path.join(PLAINTEXT_DIR, source_file)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Source file not found: {path}")
    return open(path, encoding="utf-8", errors="ignore").read()


def main():
    dataset = []
    errors = []
    idx = 0

    # Deterministic order: alphabetical by doc key, then list order within
    # each doc (both fixed in eligible_pool.py — no randomness at this
    # stage, so re-running this script is fully reproducible).
    for doc_key in sorted(ELIGIBLE.keys()):
        entry = ELIGIBLE[doc_key]
        source_file = entry["source_file"]
        cap = entry["cap"]
        items = entry["items"]

        if len(items) != cap:
            errors.append(f"{doc_key}: {len(items)} items but cap is {cap}")
            continue

        source_text = load_source_text(source_file)
        norm_source = normalize(source_text)

        for item in items:
            text, section, req_id = item[0], item[1], item[2]
            strip = item[3] if len(item) > 3 else None

            norm_text = normalize(text)
            if norm_text not in norm_source:
                errors.append(
                    f"{doc_key}: TEXT NOT FOUND VERBATIM in {source_file}: {text[:100]!r}"
                )
                continue

            final_text = norm_text
            if strip:
                bad_strip = False
                for s in strip:
                    norm_s = normalize(s)
                    if norm_s not in final_text:
                        errors.append(
                            f"{doc_key}: STRIP PATTERN NOT FOUND in verified text: {s[:80]!r} (item: {text[:80]!r})"
                        )
                        bad_strip = True
                        continue
                    final_text = final_text.replace(norm_s, "")
                if bad_strip:
                    continue
                final_text = normalize(final_text)

            compliance_level = None
            marker_match = COMPLIANCE_MARKER_RE.search(final_text)
            if marker_match:
                compliance_level = COMPLIANCE_LABELS[marker_match.group(1)]
                final_text = normalize(COMPLIANCE_MARKER_RE.sub("", final_text))

            idx += 1
            dataset.append({
                "id": f"PURE-{idx:03d}",
                "text": final_text,
                "source_document": source_file,
                "source_document_key": doc_key,
                "source_section": section,
                "source_requirement_id": req_id,
                "compliance_level": compliance_level,
            })

    if errors:
        print(f"{len(errors)} INTEGRITY ERRORS — nothing written:\n")
        for e in errors:
            print(" -", e)
        sys.exit(1)

    if len(dataset) != 150:
        print(f"ERROR: assembled {len(dataset)} items, expected exactly 150")
        sys.exit(1)

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)

    print(f"All {len(dataset)} items verified verbatim against their source documents.")
    print(f"Wrote {OUT_PATH}")

    # Summary by document
    from collections import Counter
    counts = Counter(d["source_document_key"] for d in dataset)
    for k in sorted(counts):
        print(f"  {k:16s} {counts[k]}")


if __name__ == "__main__":
    main()
