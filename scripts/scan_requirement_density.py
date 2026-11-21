#!/usr/bin/env python3
"""
Scan PURE's 79 source documents for requirement-statement density.

Converts each document (PDF/DOC/RTF/HTML) to plain text via `pdftotext`
(poppler) or `textutil` (macOS), then counts three signals used in
docs/item_selection.md to rank candidate source documents:

  - `labeled`:  explicitly numbered/labeled requirement IDs (REQ-1, FR-2, R14, ...)
  - `shall`:    sentences containing the modal verb "shall"
  - `must`:     sentences containing the modal verb "must"

Output: one row per document, written to data/interim/requirement_density_scan.csv
and printed to stdout sorted by `shall` count (descending).

Requires: pdftotext (poppler-utils; `brew install poppler` on macOS) and,
on macOS, the built-in `textutil` for .doc/.rtf/.htm/.html conversion.
"""
import csv
import glob
import os
import re
import subprocess
import sys

RAW_DOCS_DIR = os.path.join("data", "raw", "requirements_txt", "req")
PLAINTEXT_DIR = os.path.join("data", "interim", "pure_plaintext")
OUTPUT_CSV = os.path.join("data", "interim", "requirement_density_scan.csv")

LABELED_RE = re.compile(r"\b(?:REQ|FR|NFR|SR|UC|R)[-_ ]?\d{1,4}\b")
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def convert_to_text(src_path, out_path):
    ext = os.path.splitext(src_path)[1].lower()
    if ext == ".pdf":
        subprocess.run(["pdftotext", "-layout", src_path, out_path], check=True)
    elif ext in (".doc", ".rtf", ".htm", ".html"):
        with open(out_path, "w", encoding="utf-8") as f:
            subprocess.run(["textutil", "-convert", "txt", "-stdout", src_path],
                            stdout=f, check=True)
    else:
        raise ValueError(f"Unhandled extension: {ext}")


def scan_document(text):
    n_chars = len(text)
    labeled = len(LABELED_RE.findall(text))
    sentences = SENTENCE_SPLIT_RE.split(text)
    shall = sum(1 for s in sentences if re.search(r"\bshall\b", s, re.I))
    must = sum(1 for s in sentences if re.search(r"\bmust\b", s, re.I))
    return n_chars, labeled, shall, must, len(sentences)


def main():
    os.makedirs(PLAINTEXT_DIR, exist_ok=True)
    rows = []
    for src_path in sorted(glob.glob(os.path.join(RAW_DOCS_DIR, "*"))):
        filename = os.path.basename(src_path)
        base, ext = os.path.splitext(filename)
        # Keep the extension in the plaintext filename to avoid collisions
        # between same-named docs in different formats (e.g. "library.doc"
        # and "library.pdf").
        out_path = os.path.join(PLAINTEXT_DIR, f"{base} [{ext.lstrip('.')}].txt")
        try:
            convert_to_text(src_path, out_path)
        except (subprocess.CalledProcessError, ValueError) as e:
            print(f"FAILED: {filename} ({e})", file=sys.stderr)
            continue
        text = open(out_path, encoding="utf-8", errors="ignore").read()
        n_chars, labeled, shall, must, n_sentences = scan_document(text)
        rows.append({
            "document": filename,
            "chars": n_chars,
            "labeled_ids": labeled,
            "shall_sentences": shall,
            "must_sentences": must,
            "total_sentences": n_sentences,
        })

    rows.sort(key=lambda r: -r["shall_sentences"])
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"{'document':45s} {'chars':>8s} {'labeled':>8s} {'shall':>6s} {'must':>6s}")
    for r in rows:
        print(f"{r['document'][:45]:45s} {r['chars']:8d} {r['labeled_ids']:8d} "
              f"{r['shall_sentences']:6d} {r['must_sentences']:6d}")
    print(f"\nWrote {len(rows)} rows to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
