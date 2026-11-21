#!/usr/bin/env python3
"""
Extract the answer and run the frozen checker v2 and secondary measures on Study 2b outputs.
Reuses Study 2's extraction (extract_answers_study2.extract) and checker unchanged, and adds the
manipulation-check fields (words before the answer tag, reasoning tokens).

  python3 study2b/scripts/extract_and_check_2b.py [--pilot] [--raw PATH --out PATH]
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from s2bcommon import CHECKS, RAW_FULL, RAW_PILOT, RESULTS, S  # noqa: E402
import extract_answers_study2 as X  # noqa: E402  (on sys.path via s2bcommon)


def words_before_last_tag(raw):
    tags, _, _ = X.find_tags(raw or "", X.LINE_TAGS)
    return len((raw or "")[:tags[-1].start()].split()) if tags else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--raw")
    ap.add_argument("--out")
    a = ap.parse_args()
    src = a.raw or (RAW_PILOT if a.pilot else RAW_FULL)
    dst = a.out or (f"{RESULTS}/pilot/checks_pilot_2b.jsonl" if a.pilot else CHECKS)
    v2 = S.load_checker_v2()
    assert v2.selftest(), "EARS v2 self-tests failed"
    fz = S.load_json(S.FROZEN_PATH)["secondary_measures"]
    terms = fz["register_leakage"]["LEAK_TERMS"]
    n_gram, thr = fz["transcription"]["n"], fz["transcription"]["threshold"]
    inputs = {i["id"]: i["messified_text"] for i in S.load_json(S.MESSIFIED)}
    out = []
    for r in S.read_jsonl(src):
        if r.get("error"):
            continue
        e = X.extract(r)
        rec = {k: r[k] for k in ("item_id", "arm", "E", "R", "reasoning", "reasoning_effort", "model_id",
                                 "model_alias", "finish_reason")}
        rec.update(e)
        rec["words_before_tag"] = words_before_last_tag(r.get("raw_output"))
        rec["reasoning_tokens"] = (r.get("usage") or {}).get("reasoning_tokens") or 0
        rec["completion_tokens"] = (r.get("usage") or {}).get("completion_tokens")
        rec["extraction_failure"] = not e["extraction_ok"]
        if e["extraction_ok"]:
            c = v2.check_one(e["requirement_text"])
            norm = c["normalized_text"]
            rec.update(normalized_text=norm, pattern_v2=c["pattern_v2"], fail_reasons=c["fail_reasons"],
                       ears_v2_compliant=c["ears_v2_compliant"], template_slot="template_slot" in c["fail_reasons"],
                       register_leakage=S.has_leak(norm, terms),
                       copy_share=round(S.copy_share(norm, inputs[r["item_id"]], n_gram), 4),
                       length_words=len(norm.split()))
            rec["transcription"] = rec["copy_share"] >= thr
        else:
            rec.update(normalized_text=None, pattern_v2=None, fail_reasons=["extraction_failure"],
                       ears_v2_compliant=False, template_slot=None, register_leakage=None, copy_share=None,
                       transcription=None, length_words=None)
        rec["compliant_itt"] = bool(rec["ears_v2_compliant"])
        out.append(rec)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, "w", encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"{len(out)} outputs checked -> {dst}")


if __name__ == "__main__":
    main()
