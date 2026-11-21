#!/usr/bin/env python3
"""
Assemble the ten Study 2 arm prompts from the shared components and write
the freeze manifest.

  python3 study2/scripts/build_prompts.py           # (re)build arms + MANIFEST.json
  python3 study2/scripts/build_prompts.py --check   # verify only, write nothing

Every factorial arm = header + five EARS patterns + [examples] + [rules] +
[chain-of-thought] + output instruction, so any two arms that differ in one
factor differ by exactly one text block. The script asserts this.

MANIFEST.json records the SHA-256 of every file the design depends on. The
inference script refuses to run if any of them changed after the freeze
commit.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from s2common import (ARM_DIR, ARMS_PATH, CHECKER_V2, CHECKER_V2_SHA256, COMPONENTS, EXEMPLARS_PATH, FROZEN_PATH,
                      LINEUP, MANIFEST_PATH, MESSIFIED, NAME_ONLY_REF, NAME_ONLY_REF_SHA256, PRIOR_RUN_RAW, PURE150, S2,
                      assemble_arm, load_json, render_examples, sha256_file)

FROZEN_EXTRA = [
    f"{S2}/ANALYSIS_PLAN.md",
    f"{S2}/scripts/s2common.py",
    f"{S2}/scripts/build_prompts.py",
    f"{S2}/scripts/estimate_cost.py",
    f"{S2}/scripts/run_inference_study2.py",
    f"{S2}/scripts/extract_answers_study2.py",
    f"{S2}/scripts/check_study2.py",
    f"{S2}/scripts/analyze_study2.py",
    f"{S2}/scripts/human_subsample_study2.py",
    f"{S2}/config/human_subsample_items.json",
    PRIOR_RUN_RAW,  # prior exploratory run's logged usage, used by estimate_cost.py
]


def main():
    check_only = "--check" in sys.argv
    arms = load_json(ARMS_PATH)["arms"]
    exemplars = load_json(EXEMPLARS_PATH)["exemplars"]

    assert sha256_file(NAME_ONLY_REF) == NAME_ONLY_REF_SHA256, "name-only reference prompt changed"
    assert sha256_file(CHECKER_V2) == CHECKER_V2_SHA256, "checker v2 changed"
    assert [e["pattern"] for e in exemplars] == ["ubiquitous", "event-driven", "unwanted-behaviour",
                                                 "state-driven", "optional-feature"]

    texts = {a["arm"]: assemble_arm(a, exemplars) for a in arms}

    # One-block-difference check: for every pair of factorial arms that differ in one factor,
    # deleting that factor's block from the longer prompt must give exactly the shorter prompt.
    factor_block = {
        0: render_examples(exemplars),
        1: open(f"{COMPONENTS}/cot.txt", encoding="utf-8").read().strip(),
        2: open(f"{COMPONENTS}/rules.txt", encoding="utf-8").read().strip(),
    }
    fac = {(a["E"], a["C"], a["R"]): a["arm"] for a in arms if a["family"] == "factorial"}
    assert len(fac) == 8
    n_pairs = 0
    for levels, name in fac.items():
        for f in range(3):
            if levels[f] == 0:
                continue
            lower = list(levels)
            lower[f] = 0
            other = fac[tuple(lower)]
            block = "\n\n" + factor_block[f]
            assert texts[name].count(block) == 1, f"{name}: factor block {f} not found exactly once"
            assert texts[name].replace(block, "", 1) == texts[other], f"{name} vs {other}: differ by more than one block"
            n_pairs += 1
    assert n_pairs == 12
    out_line = open(f"{COMPONENTS}/output_final_line.txt", encoding="utf-8").read().strip()
    out_json = open(f"{COMPONENTS}/output_final_json.txt", encoding="utf-8").read().strip()
    assert texts["F_base"].replace(out_line, out_json, 1) == texts["J_json"], "J_json must differ from F_base only in the output block"
    assert texts["A0_name_only"] == open(NAME_ONLY_REF, encoding="utf-8").read()

    for name, text in texts.items():
        path = f"{ARM_DIR}/{name}.txt"
        if check_only:
            assert open(path, encoding="utf-8").read() == text, f"{path} is not what the components produce"
        else:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)

    files = {}
    for p in sorted(os.listdir(COMPONENTS)):
        files[f"{COMPONENTS}/{p}"] = None
    for name in texts:
        files[f"{ARM_DIR}/{name}.txt"] = None
    for p in [ARMS_PATH, EXEMPLARS_PATH, FROZEN_PATH, NAME_ONLY_REF, CHECKER_V2, MESSIFIED, PURE150, LINEUP,
              *FROZEN_EXTRA]:
        files[p] = None
    missing = [p for p in files if not os.path.exists(p)]
    if missing:
        sys.exit("Missing files: " + ", ".join(missing))
    files = {p: sha256_file(p) for p in files}

    if check_only:
        man = load_json(MANIFEST_PATH)
        diff = [p for p in files if man["files"].get(p) != files[p]]
        print("MANIFEST OK" if not diff else "MANIFEST MISMATCH:\n  " + "\n  ".join(diff))
        sys.exit(1 if diff else 0)

    manifest = {
        "_comment": "SHA-256 of every file the Study 2 design depends on. Written by build_prompts.py; committed in "
                    "the freeze commit. run_inference_study2.py refuses to call the API if any listed file changed.",
        "arms": {name: {"sha256": files[f"{ARM_DIR}/{name}.txt"], "chars": len(texts[name])} for name in texts},
        "files": files,
    }
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")
    for name in texts:
        print(f"{name:14s} {len(texts[name]):5d} chars  {files[f'{ARM_DIR}/{name}.txt'][:12]}")
    print(f"Wrote {len(texts)} arm prompts and {MANIFEST_PATH} ({len(files)} files)")


if __name__ == "__main__":
    main()
