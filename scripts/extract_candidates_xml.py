#!/usr/bin/env python3
"""
Phase 1b of the PURE-150 extraction: for the 9 documents that have a
structured XML counterpart in PURE's XML subset (data/raw/requirements_xml),
extract candidates from the XML instead of the pdftotext-converted plain
text. The XML preserves clean paragraph/heading boundaries (<title>,
<text_body>, <itemize>/<item>, and — for 4 of the 9 — an explicit
<req id="N"><text_body>REQ-N: ...</text_body></req> tag), which avoids the
header/body mashing that pdftotext -layout introduces on multi-column or
dense-heading PDF pages. See docs/item_selection.md Step 2, criterion
(c).

Output: same shape as extract_candidates.py — one JSON file per document in
data/interim/candidates_xml/, {id, document, nearest_heading, text,
match_type}. All text is a verbatim copy of XML element text content
(whitespace-normalized only).
"""
import json
import os
import re
import xml.etree.ElementTree as ET

XML_DIR = os.path.join("data", "raw", "requirements_xml", "XMLZIPFile")
OUT_DIR = os.path.join("data", "interim", "candidates_xml")
NS = {"r": "req_document.xsd"}

DOCS = [
    "1999 - tcs.xml",
    "2007-eirene_fun_7-2.xml",
    "2007-ertms.xml",
    "1995 - gemini.xml",
    "2009 - peppol approved.xml",
    "2005 - phin.xml",
    "2008 - keepass.xml",
    "2008 - peering.xml",
    "2009 - video search.xml",
]

SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
MODAL_RE = re.compile(r"\bshall\b|\bmust\b|\bwill\b", re.I)
LABELED_RE = re.compile(r"\b(?:REQ|FR|NFR|SR|UC|R)[-_ ]?\d{1,4}\b")
REQUIREMENTS_HEADING_RE = re.compile(r"requirement", re.I)


def norm(s):
    return re.sub(r"\s+", " ", s or "").strip()


def local(tag):
    return tag.split("}")[-1] if "}" in tag else tag


def in_requirements_section(heading_stack):
    return any(h and REQUIREMENTS_HEADING_RE.search(h) for h in heading_stack)


def walk(elem, heading_stack, out, doc_id, counter):
    tag = local(elem.tag)

    if tag == "p":
        title_elem = elem.find("r:title", NS)
        title_text = norm(title_elem.text) if title_elem is not None else None
        new_stack = heading_stack + [title_text] if title_text else heading_stack
    else:
        new_stack = heading_stack

    if tag == "req":
        text_body = elem.find("r:text_body", NS)
        full_text = norm("".join(text_body.itertext())) if text_body is not None else norm("".join(elem.itertext()))
        if full_text:
            counter[0] += 1
            out.append({
                "id": f"{doc_id}__X{counter[0]:04d}",
                "document": doc_id,
                "nearest_heading": " > ".join(h for h in heading_stack if h) or None,
                "text": full_text,
                "match_type": "xml_req_tag",
            })

    elif tag == "text_body":
        # Direct text of this text_body (excluding nested <itemize>, which
        # is walked separately below via the generic recursion).
        direct_text = norm(elem.text or "")
        if direct_text:
            under_req_heading = in_requirements_section(new_stack)
            for sent in SENTENCE_SPLIT_RE.split(direct_text):
                sent = norm(sent)
                if not sent:
                    continue
                if under_req_heading or MODAL_RE.search(sent) or LABELED_RE.search(sent):
                    counter[0] += 1
                    out.append({
                        "id": f"{doc_id}__X{counter[0]:04d}",
                        "document": doc_id,
                        "nearest_heading": " > ".join(h for h in new_stack if h) or None,
                        "text": sent,
                        "match_type": "xml_text_body_requirements_section" if under_req_heading else "xml_text_body_modal",
                    })

    elif tag == "item":
        item_text = norm("".join(elem.itertext()))
        under_req_heading = in_requirements_section(heading_stack)
        if item_text and (under_req_heading or MODAL_RE.search(item_text) or LABELED_RE.search(item_text)):
            counter[0] += 1
            out.append({
                "id": f"{doc_id}__X{counter[0]:04d}",
                "document": doc_id,
                "nearest_heading": " > ".join(h for h in heading_stack if h) or None,
                "text": item_text,
                "match_type": "xml_item_requirements_section" if under_req_heading else "xml_item_modal",
            })
        # Don't recurse further into item's children individually — the
        # itertext() above already captured the full item, including any
        # nested itemize.
        return

    for child in elem:
        walk(child, new_stack, out, doc_id, counter)


def extract_from_document(xml_filename):
    path = os.path.join(XML_DIR, xml_filename)
    tree = ET.parse(path)
    root = tree.getroot()
    doc_id = os.path.splitext(xml_filename)[0]
    out = []
    counter = [0]
    walk(root, [], out, doc_id, counter)
    # De-duplicate exact repeats (e.g. an item's modal sentence captured
    # once via item and not double-counted via text_body, but headings can
    # repeat text across close-by nodes in some docs).
    seen = set()
    deduped = []
    for c in out:
        if c["text"] in seen:
            continue
        seen.add(c["text"])
        deduped.append(c)
    return deduped


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    total = 0
    for doc in DOCS:
        candidates = extract_from_document(doc)
        out_path = os.path.join(OUT_DIR, os.path.splitext(doc)[0] + ".json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(candidates, f, indent=2, ensure_ascii=False)
        print(f"{doc:35s} {len(candidates):5d} candidates -> {out_path}")
        total += len(candidates)
    print(f"\nTotal: {total}")


if __name__ == "__main__":
    main()
