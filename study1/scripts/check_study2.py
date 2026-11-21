#!/usr/bin/env python3
"""
Automatic checks on every extracted Study 2 requirement.

  python3 study2/scripts/check_study2.py           # full run
  python3 study2/scripts/check_study2.py --pilot   # pilot

Primary outcome: ears_v2_compliant from the unchanged EARS v2 checker
(scripts/check_ears_compliance_v2.py, SHA-256 verified on load; its 26
self-tests run first). An extraction failure counts as non-compliant
(compliant_itt = False) and is also flagged separately.

Secondary measures (definitions frozen in config/frozen_settings.json):
template_slot, register_leakage, transcription (>=0.5 of tokens in copied
word 4-grams), extraction_failure, length_words. All are computed on the
checker's normalized text. The first-tag extraction rule is also checked
(ears_v2_compliant_first_tag) for the sensitivity analysis.
"""
import csv
import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from s2common import CHECKS, EXTRACTED, FROZEN_PATH, MESSIFIED, RESULTS, copy_share, has_leak, load_checker_v2, \
    load_json, read_jsonl


def main():
    pilot = "--pilot" in sys.argv
    src = f"{RESULTS}/pilot/extracted_pilot.jsonl" if pilot else EXTRACTED
    dst = f"{RESULTS}/pilot/checks_pilot.jsonl" if pilot else CHECKS
    summ = f"{RESULTS}/pilot/checks_pilot_summary.csv" if pilot else f"{RESULTS}/checks_study2_summary.csv"

    v2 = load_checker_v2()
    if not v2.selftest():
        sys.exit("EARS v2 self-tests failed")
    fz = load_json(FROZEN_PATH)["secondary_measures"]
    terms = fz["register_leakage"]["LEAK_TERMS"]
    n_gram, thr = fz["transcription"]["n"], fz["transcription"]["threshold"]
    inputs = {i["id"]: i["messified_text"] for i in load_json(MESSIFIED)}

    out = []
    for r in read_jsonl(src):
        rec = dict(r)
        rec["extraction_failure"] = not r["extraction_ok"]
        if r["extraction_ok"]:
            c = v2.check_one(r["requirement_text"])
            norm = c["normalized_text"]
            rec.update({
                "normalized_text": norm, "pattern_v2": c["pattern_v2"], "fail_reasons": c["fail_reasons"],
                "flags": c["flags"], "shall_count": c["shall_count"], "formatting_noise": c["formatting_noise"],
                "compound_predicate_suspected": c["compound_predicate_suspected"],
                "ears_v2_compliant": c["ears_v2_compliant"],
                "template_slot": "template_slot" in c["fail_reasons"],
                "register_leakage": has_leak(norm, terms),
                "copy_share": round(copy_share(norm, inputs[r["item_id"]], n_gram), 4),
                "length_words": len(norm.split()),
            })
            rec["transcription"] = rec["copy_share"] >= thr
        else:
            rec.update({"normalized_text": None, "pattern_v2": None, "fail_reasons": ["extraction_failure"],
                        "flags": [], "ears_v2_compliant": False, "template_slot": None, "register_leakage": None,
                        "copy_share": None, "transcription": None, "length_words": None})
        rec["compliant_itt"] = bool(rec["ears_v2_compliant"])
        ft = r.get("requirement_text_first_tag")
        rec["ears_v2_compliant_first_tag"] = bool(ft) and v2.check_one(ft)["ears_v2_compliant"]
        out.append(rec)

    with open(dst, "w", encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    g = defaultdict(lambda: defaultdict(float))
    for r in out:
        s = g[(r["model_alias"], r["arm"])]
        s["n"] += 1
        s["compliant"] += r["compliant_itt"]
        s["extraction_failure"] += r["extraction_failure"]
        s["extractable"] += r["extraction_ok"]
        for m in ("template_slot", "register_leakage", "transcription"):
            s[m] += bool(r[m])
    with open(summ, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        # EARS v2 rate over all outputs (failure = non-compliant); secondary rates over extractable outputs.
        w.writerow(["model", "arm", "n", "ears_v2_rate", "extraction_failures", "n_extractable",
                    "template_slot_rate", "register_leakage_rate", "transcription_rate"])
        for (m, a), s in sorted(g.items()):
            n, ne = s["n"], max(s["extractable"], 1)
            w.writerow([m, a, int(n), f"{s['compliant'] / n:.3f}", int(s["extraction_failure"]), int(s["extractable"]),
                        f"{s['template_slot'] / ne:.3f}", f"{s['register_leakage'] / ne:.3f}",
                        f"{s['transcription'] / ne:.3f}"])
    print(f"{len(out)} outputs checked. Wrote {dst} and {summ}")


if __name__ == "__main__":
    main()
