# Item selection: 150 requirements from PURE

Source: PURE (Ferrari, Spagnolo and Gnesi, 2017; https://doi.org/10.5281/zenodo.1414117), 79 documents.
Output: `data/pure_150.json` (fields: `id`, `text`, `source_document`, `source_section`,
`source_requirement_id`, `compliance_level`).

## Documents

`scripts/scan_requirement_density.py` counts, per document, sentences with "shall", sentences with "must" and
numbered requirement IDs (`data/interim/requirement_density_scan.csv`). About 30 documents are dense on at least
one count (≥20 "shall", ≥20 "must" or ≥10 IDs). Nineteen of them were kept, covering six domain clusters:

| Document | Domain | Items |
|---|---|---:|
| 2001 - npac | Telecom regulatory | 13 |
| 1999 - tcs | Defense | 13 |
| 2000 - nasa x38 | Aerospace | 10 |
| 2005 - clarus low | Environmental | 8 |
| 2007 - eirene fun 7 | Rail | 8 |
| 2007 - nde | Aerospace/satellite | 8 |
| 2005 - pontis | Transportation infrastructure | 8 |
| 1995 - gemini | Astronomy | 8 |
| 2009 - peppol | E-government | 8 |
| 2009 - inventory 2.0 | Enterprise software | 8 |
| 2005 - phin | Public health | 8 |
| 2008 - keepass | Consumer software | 8 |
| 2007 - ertms | Rail | 6 |
| 2004 - rlcs | Transportation | 6 |
| 2010 - fishing | Maritime regulatory | 6 |
| 2009 - warc III | Web archiving | 6 |
| 2006 - stewards | Environmental/agriculture | 6 |
| 2008 - peering | Networking | 6 |
| 2009 - video search | Consumer software | 6 |
| **Total** | | **150** |

## What counts as one item

**Include** a sentence if it:

1. states a single, atomic capability, behaviour or constraint of the system (functional or non-functional);
2. is self-contained, given its section heading;
3. carries exactly one requirement-bearing predicate (one shall/must/will clause);
4. appears in a section framed as normative requirements, or in a numbered requirement list.

**Exclude:**

- headers and titles alone;
- glossary and definition entries;
- non-normative prose: rationale, assumptions, notes, examples, background, conventions;
- use-case steps describing a human actor's actions rather than system behaviour;
- compound requirements with two or more independent obligations (excluded, not split);
- requirements given only in a table or diagram;
- duplicates and near-duplicates, within or across documents;
- fragments and conversion artefacts;
- non-English text;
- obligations on the project or contractor rather than the system (e.g. "The contractor shall deliver…");
- items labelled "Information" in EIRENE, which the source defines as explanatory notes.

## Procedure

| Step | Script | Output |
|---|---|---|
| 1. Collect every shall/must sentence and labelled requirement, verbatim (plain text; XML for the 9 documents that have it) | `scripts/extract_candidates.py`, `scripts/extract_candidates_xml.py` | candidate pools (regenerated; need the raw PURE files) |
| 2. Deterministic exclusion filters (length, non-normative headings, compound modals, duplicates); text never rewritten | `scripts/screen_candidates.py` | `data/interim/screened/` |
| 3. Shortlist per document, about 2.5 × its quota, spread evenly across the document | `scripts/build_shortlist.py` | `data/interim/shortlist.json`, `shortlist_review.txt` |
| 4. Review of the shortlist against the criteria above; items kept up to the quota (Section 3.2 and Table 2 of the paper: no random draw) | — | `scripts/eligible_pool.py` |
| 5. Verify that every item is a verbatim substring of its source, then assign `PURE-001` … `PURE-150` | `scripts/assemble_pure150.py` | `data/pure_150.json` |

Step 5 fails and writes nothing if an item is not found in its source. Where a candidate contains more than one
requirement, a heading or a page number, the item is the verbatim substring covering the one requirement.
Requirement IDs written inline (e.g. `shall [SRS197] support`, `(3.1.18)`, `REQ-1:`) are removed through an
explicit list of exact substrings, each checked against the verified text; the ID is kept in
`source_requirement_id`. EIRENE's trailing `(M)`/`(O)` tags are moved to `compliance_level`. For
`2005 - clarus low`, plain text was extracted with `pdftotext -raw`, because `-layout` mixed the columns of its
requirements table into the sentences.

To rebuild `data/pure_150.json` from the repository root: download PURE into `data/raw/` (see
`data/raw/README.md`); run `python3 scripts/scan_requirement_density.py`, which writes the plain text to
`data/interim/pure_plaintext/` (needs `pdftotext`, and macOS `textutil` for DOC, RTF and HTML); re-extract
`2005 - clarus low` with `pdftotext -raw`; then run `python3 scripts/assemble_pure150.py`.
