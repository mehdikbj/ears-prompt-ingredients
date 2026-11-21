#!/usr/bin/env python3
"""
Extract the graded requirement from each Study 2 output.

  python3 study2/scripts/extract_answers_study2.py           # full run
  python3 study2/scripts/extract_answers_study2.py --pilot   # pilot

Rule (frozen_settings.json -> extraction):
  final_line arms : the LAST "FINAL REQUIREMENT:" tag that starts a line (markdown
                    markers such as **, #, > allowed before it, case-insensitive);
                    if none starts a line, the last exact upper-case tag anywhere.
                    The answer is the first line after the tag that still has
                    text once markdown markers (* # _ ` >) and spaces are removed.
  final_json arm  : the same tag rule for "FINAL JSON:", then the JSON object after
                    it; its "requirement" field ("pattern" kept as the model's
                    self-report).
The first-tag rule (FIRST tag, case-insensitive, anywhere; first non-empty line) is
also stored as requirement_text_first_tag for the sensitivity analysis.

Completeness: the output must hold exactly one successful record for every
planned (item, arm, model) call, all from one prompt version per arm. Missing
or duplicated calls stop the script (exit 1) unless --allow-incomplete is
given, in which case missing calls are listed and get no row. A call whose
every attempt failed gets a row with extraction_ok=false (non-compliant).
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from s2common import EXTRACTED, RAW_FULL, RAW_PILOT, RESULTS, read_jsonl

MARKUP = "*#_`> \t"


def tag_res(tag):
    anchored = re.compile(rf"(?mi)^[{re.escape(MARKUP)}]*{tag}")
    anywhere_exact = re.compile(tag)
    first_tag = re.compile(tag, re.I)
    return anchored, anywhere_exact, first_tag


LINE_TAGS = tag_res("FINAL REQUIREMENT:")
JSON_TAGS = tag_res("FINAL JSON:")


def first_meaningful_line(text):
    """First line that still has text once markdown markers and spaces are stripped."""
    for line in text.split("\n"):
        if line.strip(MARKUP + "\r"):
            return line.strip()
    return ""


def first_tag_line(text):
    return next((l.strip() for l in text.split("\n") if l.strip()), "")


def find_tags(raw, res):
    anchored, exact, first_tag = res
    tags = list(anchored.finditer(raw))
    rule = "line_start"
    if not tags:
        tags, rule = list(exact.finditer(raw)), "exact_anywhere"
    return tags, rule, list(first_tag.finditer(raw))


def parse_json_after(raw, pos):
    m = re.search(r"\{.*\}", raw[pos:], re.S)
    if not m:
        return None, None, "no JSON object after FINAL JSON: tag"
    try:
        obj = json.loads(m.group(0))
    except json.JSONDecodeError as e:
        return None, None, f"JSON did not parse: {e}"
    if not isinstance(obj, dict):
        return None, None, "JSON is not an object"
    req = obj.get("requirement")
    if not isinstance(req, str) or not req.strip():
        return None, obj.get("pattern"), "JSON has no non-empty 'requirement'"
    return req.strip(), obj.get("pattern"), None


def empty(error, n=0, rule=None):
    return dict(requirement_text=None, requirement_text_first_tag=None, self_reported_pattern=None, n_tags=n,
                tag_rule=rule, extraction_ok=False, extraction_error=error)


def extract(rec):
    raw = rec.get("raw_output") or ""
    if rec["output_format"] == "final_json":
        tags, rule, s1 = find_tags(raw, JSON_TAGS)
        first = parse_json_after(raw, s1[0].end())[0] if s1 else None
        if not tags:
            return {**empty("no FINAL JSON: tag"), "requirement_text_first_tag": first}
        last, pat, err = parse_json_after(raw, tags[-1].end())
        return dict(requirement_text=last, requirement_text_first_tag=first, self_reported_pattern=pat,
                    n_tags=len(tags), tag_rule=rule, extraction_ok=err is None, extraction_error=err)
    tags, rule, s1 = find_tags(raw, LINE_TAGS)
    first = (first_tag_line(raw[s1[0].end():]) or None) if s1 else None
    if not tags:
        return {**empty("no FINAL REQUIREMENT: tag"), "requirement_text_first_tag": first}
    last = first_meaningful_line(raw[tags[-1].end():])
    err = None if last else "no text after the last FINAL REQUIREMENT: tag"
    return dict(requirement_text=last or None, requirement_text_first_tag=first, self_reported_pattern=None,
                n_tags=len(tags), tag_rule=rule, extraction_ok=err is None, extraction_error=err)


def planned_keys(pilot):
    from run_inference_study2 import build_plan
    plan, _ = build_plan(pilot)
    return {(t["item_id"], t["arm"], t["model_id"]): t["arm_prompt_sha256"] for t in plan}


def main():
    pilot = "--pilot" in sys.argv
    allow_incomplete = "--allow-incomplete" in sys.argv
    src = RAW_PILOT if pilot else RAW_FULL
    dst = f"{RESULTS}/pilot/extracted_pilot.jsonl" if pilot else EXTRACTED
    recs = read_jsonl(src)
    planned = planned_keys(pilot)

    problems, ok, failed = [], {}, {}
    for r in recs:
        k = (r["item_id"], r["arm"], r["model_id"])
        if k not in planned:
            problems.append(f"record not in the plan: {k}")
            continue
        if r.get("arm_prompt_sha256") != planned[k]:
            problems.append(f"record from a different prompt version: {k}")
            continue
        if r.get("error"):
            failed[k] = r
        elif k in ok:
            problems.append(f"duplicate successful record: {k}")
        else:
            ok[k] = r
    missing = sorted(k for k in planned if k not in ok and k not in failed)
    if problems or (missing and not allow_incomplete):
        for p in problems[:20]:
            print("  " + p)
        if missing:
            print(f"  {len(missing)} planned calls have no record, e.g. {missing[:3]}")
        sys.exit(f"ERROR: {len(problems)} inconsistent records, {len(missing)} missing calls. Nothing written.")

    keep = ("item_id", "arm", "family", "E", "C", "R", "output_format", "model_id", "model_alias", "model_tier",
            "finish_reason", "api_response_id", "arm_prompt_sha256")
    out = []
    for k in sorted(set(ok) | set(failed)):
        r = ok.get(k) or failed[k]
        res = extract(r) if k in ok else empty(f"API call failed: {r['error']}")
        out.append({**{f: r.get(f) for f in keep}, **res})
    with open(dst, "w", encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    n_fail = sum(not r["extraction_ok"] for r in out)
    multi = sum(r["n_tags"] > 1 for r in out)
    fallback = sum(r["tag_rule"] == "exact_anywhere" for r in out)
    print(f"{len(out)} outputs of {len(planned)} planned ({len(recs)} raw records): {len(out) - n_fail} extracted, "
          f"{n_fail} failures, {multi} with more than one tag, {fallback} found only by the mid-line fallback. "
          f"Wrote {dst}")
    if missing:
        print(f"INCOMPLETE: {len(missing)} planned calls missing (--allow-incomplete).")
    for r in out:
        if not r["extraction_ok"]:
            print(f"  FAIL {r['item_id']} {r['arm']} {r['model_alias']}: {r['extraction_error']}")


if __name__ == "__main__":
    main()
