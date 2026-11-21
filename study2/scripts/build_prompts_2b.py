#!/usr/bin/env python3
"""
Assemble the twelve Study 2b arm prompts and write the manifest.

  python3 study2b/scripts/build_prompts_2b.py           # (re)build arms + MANIFEST.json
  python3 study2b/scripts/build_prompts_2b.py --check   # verify only

Asserts that (a) every 'none' and 'native' arm is byte-identical to its Study 2 arm
(F_base, F_E, F_R, F_ER), and (b) every 'written' arm differs from its 'none' arm by
exactly the written-reasoning block.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from s2bcommon import ARM_DIR, ARMS_PATH, COMPONENTS_2B, MANIFEST_PATH, S2B, SETTINGS_PATH, S  # noqa: E402

FROZEN_EXTRA = [f"{S2B}/ANALYSIS_PLAN.md", f"{S2B}/scripts/s2bcommon.py", f"{S2B}/scripts/build_prompts_2b.py",
                f"{S2B}/scripts/run_inference_2b.py", f"{S2B}/scripts/extract_and_check_2b.py",
                f"{S2B}/scripts/analyze_study2b.py", f"{S2B}/pattern_fit/analyze_pattern_fit.py",
                f"{S2B}/pattern_fit/01_instructions.md", f"{S2B}/human_eval/build_sheets_2b.py",
                f"{S2B}/human_eval/analyze_human_2b.py", f"{S2B}/human_eval/02_equivalence_criterion.md",
                S.CHECKER_V2, S.MESSIFIED, S.PURE150, S.LINEUP, S.EXEMPLARS_PATH, "study2/config/frozen_settings.json",
                "study2/scripts/s2common.py", "study2/scripts/extract_answers_study2.py"]


def main():
    check_only = "--check" in sys.argv
    arms = S.load_json(ARMS_PATH)["arms"]
    block = open(f"{COMPONENTS_2B}/cot_written.txt", encoding="utf-8").read().strip()
    out_block = S.read_text(f"{S.COMPONENTS}/output_final_line.txt").strip()
    texts = {}
    none_text = {}
    for a in arms:
        if a["reasoning"] in ("none", "native"):
            t = S.read_text(f"{S.ARM_DIR}/{a['study2_prompt']}.txt")
            texts[a["arm"]] = t
            if a["reasoning"] == "none":
                none_text[(a["E"], a["R"])] = t
    for a in arms:
        if a["reasoning"] == "written":
            base = none_text[(a["E"], a["R"])]
            assert base.count(out_block) == 1
            t = base.replace(out_block, block + "\n\n" + out_block, 1)
            assert t.replace("\n\n" + block, "", 1) == base, a["arm"]
            texts[a["arm"]] = t
    assert len(texts) == 12
    for a in arms:  # one-factor pairs within each reasoning level: Study 2's build already proved one-block differences
        if a["reasoning"] == "native":
            assert texts[a["arm"]] == none_text[(a["E"], a["R"])]
    for name, text in texts.items():
        path = f"{ARM_DIR}/{name}.txt"
        if check_only:
            assert open(path, encoding="utf-8").read() == text, f"{path} differs from what the components produce"
        else:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
    files = sorted({f"{ARM_DIR}/{n}.txt" for n in texts} | {f"{COMPONENTS_2B}/cot_written.txt", ARMS_PATH,
                                                              SETTINGS_PATH, *FROZEN_EXTRA})
    missing = [p for p in files if not os.path.exists(p)]
    if missing:
        sys.exit("Missing files: " + ", ".join(missing))
    hashes = {p: S.sha256_file(p) for p in files}
    if check_only:
        man = S.load_json(MANIFEST_PATH)
        diff = [p for p in hashes if man["files"].get(p) != hashes[p]]
        sys.exit(f"MANIFEST differs: {diff}") if diff else print("MANIFEST OK")
        return
    import json
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump({"_comment": "SHA-256 of every Study 2b design file. Written by build_prompts_2b.py; committed in "
                               "the freeze commit. run_inference_2b.py refuses to call the API if any file changed.",
                   "files": hashes}, f, indent=2)
    print(f"Wrote {len(texts)} arms and {MANIFEST_PATH}")


if __name__ == "__main__":
    main()
