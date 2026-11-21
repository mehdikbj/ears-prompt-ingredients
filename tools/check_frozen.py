#!/usr/bin/env python3
"""
Checks the design files against the SHA-256 hashes recorded in the two frozen manifests
(Study 1: study1/prompts/MANIFEST.json; Study 2: study2/prompts/MANIFEST.json). The manifests list the files
under the folder names used when they were frozen (study2/ = Study 1, study2b/ = Study 2), so the check runs in
the temporary copy made by reproduce.sh, which uses those names.

Two differences are expected and documented in README.md:
  - study2/config/human_subsample_items.json and study2/scripts/human_subsample_study2.py (Study 1): the raters'
    first names were replaced by their codes (R1, R3) before publication; nothing else changed;
  - archive/study1/results/raw_inference.jsonl: output of the preliminary run, which the paper does not report
    and which is not in this repository.

  python3 tools/check_frozen.py WORK_DIR
"""
import hashlib
import json
import os
import sys

EXPECTED = {
    "study2/config/human_subsample_items.json": "rater names replaced by codes",
    "study2/scripts/human_subsample_study2.py": "rater names replaced by codes",
    "archive/study1/results/raw_inference.jsonl": "preliminary run, not included",
}


def sha256(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def main(work):
    unexpected = []
    for study, manifest in [("Study 1", "study2/prompts/MANIFEST.json"), ("Study 2", "study2b/prompts/MANIFEST.json")]:
        with open(os.path.join(work, manifest), encoding="utf-8") as f:
            files = json.load(f)["files"]
        ok, notes = 0, []
        for rel, h in files.items():
            p = os.path.join(work, rel)
            if os.path.exists(p) and sha256(p) == h:
                ok += 1
            elif rel in EXPECTED:
                notes.append(f"{rel} ({EXPECTED[rel]})")
            else:
                unexpected.append(f"{study}: {rel} {'missing' if not os.path.exists(p) else 'differs'}")
        print(f"{study}: {ok} of {len(files)} frozen files match their recorded hash"
              + (f"; expected exceptions: {'; '.join(notes)}" if notes else ""))
    if unexpected:
        print("UNEXPECTED:\n  " + "\n  ".join(unexpected))
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1])
