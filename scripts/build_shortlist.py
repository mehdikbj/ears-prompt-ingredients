#!/usr/bin/env python3
"""
Phase 2b: reduce each of the 19 primary documents' "pass" pool down to a
reviewable shortlist (~2.5x the document's target cap from
docs/item_selection.md), so a human can actually read and judge every
candidate against the rules that need real understanding (atomicity,
system- vs. actor-subject, genuine self-containedness) rather than reading
hundreds of raw hits per document.

Selection within a document: prefer the least ambiguous match types first
(an explicit <req> XML tag or a labeled REQ-/FR-/R-numbered line beats a
bare modal-verb sentence pulled from a "requirements" section, which beats
a modal-verb sentence found anywhere in the document), then spread evenly
across the document (every Nth surviving candidate) rather than just taking
the first K, so the shortlist isn't biased toward one part of the document.

For the 9 documents with an XML counterpart, only the XML-derived pool is
used (per docs/item_selection.md Step 2, criterion (c) — the XML pool
avoids pdftotext header/body mashing). The plaintext pool for those 9 is
intentionally NOT used here.

Output: data/interim/shortlist.json — {document: [candidate, ...]}
"""
import json
import os

SCREENED_DIR = os.path.join("data", "interim", "screened")
OUT_PATH = os.path.join("data", "interim", "shortlist.json")

# document_id -> (screened filename, target cap)
# Uses the XML-derived screened file for the 9 documents that have one.
DOC_CONFIG = {
    "npac":            ("2001 - npac [doc].json", 12),
    "tcs":             ("1999 - tcs.json", 12),
    "nasa_x38":        ("2000 - nasa x38 [doc].json", 10),
    "clarus_low":      ("2005 - clarus low [pdf].json", 8),
    "eirene_fun_7":    ("2007-eirene_fun_7-2.json", 8),
    "nde":             ("2007 - nde [pdf].json", 8),
    "ertms":           ("2007-ertms.json", 6),
    "pontis":          ("2005 - pontis [pdf].json", 8),
    "rlcs":            ("2004 - rlcs [pdf].json", 6),
    "gemini":          ("1995 - gemini.json", 8),
    "peppol":          ("2009 - peppol approved.json", 8),
    "fishing":         ("2010 - fishing [pdf].json", 6),
    "inventory_2_0":   ("2009 - inventory 2.0 [pdf].json", 8),
    "phin":            ("2005 - phin.json", 8),
    "warc_iii":        ("2009 - warc III [pdf].json", 6),
    "stewards":        ("2006 - stewards [pdf].json", 6),
    "keepass":         ("2008 - keepass.json", 8),
    "peering":         ("2008 - peering.json", 6),
    "video_search":    ("2009 - video search.json", 6),
}

MATCH_TYPE_PRIORITY = {
    "xml_req_tag": 0,
    "labeled_id": 1,
    "xml_item_requirements_section": 1,
    "xml_text_body_requirements_section": 1,
    "xml_item_modal": 2,
    "xml_text_body_modal": 2,
    "modal_verb": 3,
}

SHORTLIST_MULTIPLIER = 2.5


def main():
    shortlist = {}
    for doc_key, (screened_file, cap) in DOC_CONFIG.items():
        path = os.path.join(SCREENED_DIR, screened_file)
        rows = json.load(open(path, encoding="utf-8"))
        passed = [r for r in rows if r["verdict"] == "pass"]

        target_n = max(int(cap * SHORTLIST_MULTIPLIER), cap + 5)
        priorities_present = sorted(set(MATCH_TYPE_PRIORITY.get(r["match_type"], 9) for r in passed))

        tiered = []
        for p in priorities_present:
            tiered += [r for r in passed if MATCH_TYPE_PRIORITY.get(r["match_type"], 9) == p]
            if len(tiered) >= target_n:
                break

        pool = tiered if tiered else passed
        if len(pool) > target_n:
            step = len(pool) / target_n
            pool = [pool[int(i * step)] for i in range(target_n)]

        shortlist[doc_key] = {
            "cap": cap,
            "screened_source": screened_file,
            "n_passed_total": len(passed),
            "n_shortlisted": len(pool),
            "candidates": pool,
        }
        print(f"{doc_key:16s} cap={cap:2d}  passed={len(passed):5d}  shortlisted={len(pool):3d}")

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(shortlist, f, indent=2, ensure_ascii=False)
    print(f"\nWrote {OUT_PATH}")


if __name__ == "__main__":
    main()
