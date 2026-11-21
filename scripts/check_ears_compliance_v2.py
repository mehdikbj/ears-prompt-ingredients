#!/usr/bin/env python3
"""
Corrected EARS-syntax checker (v2). Post-hoc bug fix of
scripts/check_ears_compliance.py (v1), which is kept unchanged and still
reported for transparency.

WHY v2 EXISTS (defects found in v1, 25 Oct 2026)
  1. v1's pattern check is inert: its "ubiquitous" fallback regex matches
     any text containing "shall", so matched_pattern is never None
     (0 of 1,350 outputs). A requirement with a trailing or embedded
     condition ("The system shall X when Y") passes as ubiquitous.
  2. v1 passes outputs that contain an unfilled template slot such as
     "<system>" (30 of 31 such outputs passed).
  3. v1 folds a compound-predicate heuristic (a singularity proxy) into
     "EARS compliance".

SPECIFICATION (fixed on 25 Oct 2026, before v2 was run on the experimental
outputs; derived from the EARS templates of Mavin et al. 2009, not tuned on
results). Any later change to these rules must be logged in CHANGELOG below.

  Normalization (formatting noise is not an EARS error, matching the
  human-rating guideline): strip a leading "EARS:" label, markdown "*" and
  backticks, surrounding quotes; collapse whitespace. formatting_noise=True
  if anything was stripped. Matching is case-insensitive (EARS keywords are
  conventionally upper-case, but case is not a structural property, and
  requiring it would reward one prompt's typography).

  A requirement is ears_v2_compliant iff ALL of:
    R1 template_slot      : no unfilled "<...>" slot anywhere.
    R2 single_shall       : exactly one whole-word "shall".
    R3 single_sentence    : one sentence (no ". X" / "? X" / "! X" break).
    R4 structure          : the text before "shall" ("pre") is one of
       - EARS-keyword-led: pre starts with WHEN / WHILE / WHERE / IF, the
         keyword is followed by a non-empty clause, and the subject (text
         after the last comma in pre, minus a leading THEN) is non-empty
         and does not itself start with a keyword. pattern = event-driven /
         state-driven / optional-feature / unwanted-behaviour; "complex"
         if comma-separated clauses start with two different keywords
         (Mavin et al.'s complex requirements). For IF, a missing THEN is
         recorded (then_missing) but does not fail. A missing comma is
         recorded (comma_missing) but does not fail.
       - ubiquitous: pre contains no condition word (when, whenever, if,
         while, unless, before, after, during, once, upon, until,
         "in case", "in the event", "as soon as", "prior to").
       Fails as non_ears_leading_condition if pre starts with one of the
       non-EARS condition words (e.g. "Whenever", "Before", "During"), and
       as condition_inside_subject if a condition word occurs inside a
       ubiquitous subject.
    R5 no_misplaced_condition : the text after "shall" contains no
       trigger/state clause opener: when, whenever, if, unless, "in case",
       "in the event", or "while" not followed by an -ing word. Exempt:
       "if any", "if applicable", and a relative "when" after a time noun
       (time/date/moment/point/instant/period/day/hour). EARS requires the
       condition in the leading clause.
    R6 non_empty_response : at least one word after "shall".

  Reported but NOT part of ears_v2_compliant:
    compound_predicate_suspected : v1's heuristic, unchanged. It measures
       singularity, not EARS syntax (human Singularity tracks v1 more
       closely than human EARS well-formedness does).

CHANGELOG
  2026-10-25  v2 specified and implemented; self-tests written first.
  2026-10-25  After the first full run, before any analysis of v2 results:
              the label stripper also removes a bracketed "[EARS]" label
              (2 outputs), which the spec's "strip a leading EARS label"
              intended. No compliance decision changes (verified: the
              1,350-item ears_v2_compliant vector is identical). One output
              (PURE-142, CoT, nano) loses the reason condition_inside_subject,
              still fails on shall_count_not_1 and misplaced_condition, and
              its pattern_v2 changes from None to event-driven.

Output: results/ears_compliance_v2.jsonl, results/ears_compliance_v2_summary.csv
Run:    python3 scripts/check_ears_compliance_v2.py            (full run)
        python3 scripts/check_ears_compliance_v2.py --selftest (rule tests only)
"""
import csv
import json
import re
import sys
from collections import Counter, defaultdict

INPUT_PATH = "results/extracted_answers.jsonl"
V1_PATH = "results/ears_compliance.jsonl"
OUTPUT_PATH = "results/ears_compliance_v2.jsonl"
SUMMARY_PATH = "results/ears_compliance_v2_summary.csv"

# v1 compound-predicate heuristic, copied verbatim from check_ears_compliance.py
RESPONSE_VERBS = (
    r"provide|allow|display|notify|support|enable|prevent|require|generate|"
    r"reject|accept|store|log|send|receive|return|update|create|delete|"
    r"perform|execute|calculate|validate|check|set|configure|limit|restrict|"
    r"apply|maintain|report|trigger|initiate|record|process|manage|assign|"
    r"produce|convert|migrate|schedule|monitor|encrypt|authenticate"
)
COMPOUND_RE = re.compile(
    rf"\bshall\b.*?\b(?:{RESPONSE_VERBS})\b[^.]*?\b(?:and|or)\b\s+(?:{RESPONSE_VERBS})\b",
    re.I,
)

SHALL_RE = re.compile(r"\bshall\b", re.I)
SLOT_RE = re.compile(r"<[^<>]{1,40}>")
LABEL_RE = re.compile(r"^\W*EARS\W*?[:\]]\W*", re.I)   # "EARS:", "**EARS:**", "[EARS]"
SENT_BREAK_RE = re.compile(r"(?<!\be\.g)(?<!\bi\.e)(?<!\betc)(?<!\bvs)(?<!\bNo)[.!?]\s+[A-Z]")
EARS_KW = {"when": "event-driven", "while": "state-driven", "where": "optional-feature", "if": "unwanted-behaviour"}
KW_START_RE = re.compile(r"^(when|while|where|if)\b\s*(.*)$", re.I | re.S)
NON_EARS_COND = r"whenever|before|after|during|once|upon|until|unless|in case|in the event|as soon as|prior to"
NON_EARS_START_RE = re.compile(rf"^(?:{NON_EARS_COND})\b", re.I)
SUBJECT_COND_RE = re.compile(rf"\b(?:when|if|while|{NON_EARS_COND})\b", re.I)
EXEMPT_RE = re.compile(
    r"\bif any\b|\bif applicable\b|\b(?:time|date|moment|point|instant|period|day|hour)s? when\b", re.I)
POST_COND_RE = re.compile(r"\b(?:when|whenever|if|unless|in case|in the event)\b|\bwhile\b(?!\s+\w+ing\b)", re.I)


def normalize(text):
    t = text.strip()
    orig = t
    t = LABEL_RE.sub("", t)
    t = t.replace("*", "").replace("`", "")
    t = re.sub(r"\s+", " ", t).strip()
    t = t.strip("\"'“”‘’ ").strip()
    return t, (t != re.sub(r"\s+", " ", orig).strip())


def check_one(text):
    norm, noise = normalize(text)
    reasons, flags = [], []
    if SLOT_RE.search(norm):
        reasons.append("template_slot")
    shall_count = len(SHALL_RE.findall(norm))
    if shall_count != 1:
        reasons.append("shall_count_not_1")
    if SENT_BREAK_RE.search(norm):
        reasons.append("multiple_sentences")

    pattern = None
    if shall_count >= 1:
        m = SHALL_RE.search(norm)
        pre, post = norm[: m.start()].strip(), norm[m.end():].strip()
        km = KW_START_RE.match(pre)
        if km:
            kw = km.group(1).lower()
            if "," in pre:
                segs = [s.strip() for s in pre.split(",")]
                if not KW_START_RE.match(segs[0]).group(2).strip():
                    reasons.append("empty_condition")
                subject = segs[-1]
                cond_kws = {EARS_KW[s.split()[0].lower()] for s in segs[:-1]
                            if s and s.split()[0].lower() in EARS_KW}
                then_present = bool(re.match(r"^then\b", subject, re.I))
                subject = re.sub(r"^then\b\s*", "", subject, flags=re.I)
                if not subject:
                    reasons.append("empty_subject")
                elif KW_START_RE.match(subject):
                    reasons.append("subject_starts_with_keyword")
                pattern = "complex" if len(cond_kws) > 1 else EARS_KW[kw]
                if kw == "if" and not then_present and not re.search(r"\bthen\b", pre, re.I):
                    flags.append("then_missing")
            else:
                if not km.group(2).strip():
                    reasons.append("empty_condition")
                pattern = EARS_KW[kw]
                flags.append("comma_missing")
                if kw == "if" and not re.search(r"\bthen\b", pre, re.I):
                    flags.append("then_missing")
        elif NON_EARS_START_RE.match(pre):
            reasons.append("non_ears_leading_condition")
        elif SUBJECT_COND_RE.search(pre):
            reasons.append("condition_inside_subject")
        else:
            pattern = "ubiquitous"
        post_scan = EXEMPT_RE.sub(" ", post)
        if POST_COND_RE.search(post_scan):
            reasons.append("misplaced_condition")
        if not re.search(r"\w", post):
            reasons.append("empty_response")

    return {
        "normalized_text": norm,
        "formatting_noise": noise,
        "shall_count": shall_count,
        "pattern_v2": pattern,
        "fail_reasons": reasons,
        "flags": flags,
        "ears_v2_compliant": not reasons,
        "compound_predicate_suspected": bool(COMPOUND_RE.search(norm)),
    }


SELFTEST = [
    ("The system shall log every failed login attempt.", True, "ubiquitous"),
    ("When the user presses Save, the system shall store the record.", True, "event-driven"),
    ("WHEN the user presses Save, the system shall store the record.", True, "event-driven"),
    ("**EARS:** *When the user presses Save, the system shall store the record.*", True, "event-driven"),
    ("IF the checksum is invalid, THEN the system shall reject the packet.", True, "unwanted-behaviour"),
    ("If the checksum is invalid, the system shall reject the packet.", True, "unwanted-behaviour"),
    ("While in maintenance mode, the system shall suspend alerts.", True, "state-driven"),
    ("Where a printer is attached, the system shall print receipts.", True, "optional-feature"),
    ("While in flight mode, when a fault occurs, the FCC shall switch channels.", True, "complex"),
    ("When the alarm sounds the system shall notify the operator.", True, "event-driven"),
    ("The system shall display errors, if any, on the console.", True, "ubiquitous"),
    ("The system shall record the time when the fault occurred.", True, "ubiquitous"),
    ("The system shall keep logging while maintaining throughput.", True, "ubiquitous"),
    ("Pontis shall export inspection data in CSV format.", True, "ubiquitous"),
    ("[EARS] When the door opens, the system shall sound a chime.", True, "event-driven"),
    ("The <system> shall encrypt stored passwords.", False, None),
    ("The system shall store the record when the user presses Save.", False, "ubiquitous"),
    ("The system shall reject the packet if the checksum is invalid.", False, "ubiquitous"),
    ("The system, when the user presses Save, shall store the record.", False, None),
    ("Whenever a call arrives, the system shall beep.", False, None),
    ("During start-up, the system shall run a self-test.", False, None),
    ("The system shall validate input and shall log errors.", False, "ubiquitous"),
    ("The system should validate input.", False, None),
    ("The system shall validate input. It must also log errors.", False, "ubiquitous"),
    ("When , the system shall beep.", False, "event-driven"),
    ("When the user logs in, shall the system greet them.", False, "event-driven"),
]


def selftest():
    bad = 0
    for text, exp_ok, exp_pat in SELFTEST:
        r = check_one(text)
        ok = r["ears_v2_compliant"] == exp_ok and (exp_pat is None or r["pattern_v2"] == exp_pat)
        if not ok:
            bad += 1
            print("FAIL:", text, "->", r["ears_v2_compliant"], r["pattern_v2"], r["fail_reasons"])
    print(f"selftest: {len(SELFTEST) - bad}/{len(SELFTEST)} passed")
    return bad == 0


def main():
    if not selftest():
        sys.exit(1)
    if "--selftest" in sys.argv:
        return
    records = [json.loads(l) for l in open(INPUT_PATH, encoding="utf-8") if l.strip()]
    v1 = {(r["item_id"], r["strategy"], r["model_alias"]): r for r in
          (json.loads(l) for l in open(V1_PATH, encoding="utf-8") if l.strip())}
    out = []
    for r in records:
        key = (r["item_id"], r["strategy"], r["model_alias"])
        base = {k: r[k] for k in ("item_id", "strategy", "model_id", "model_alias")}
        if not r["extraction_ok"]:
            out.append({**base, "pipeline_failure": True, "ears_v2_compliant": None})
            continue
        res = check_one(r["requirement_text"])
        out.append({**base, "pipeline_failure": False, "requirement_text": r["requirement_text"], **res,
                    "v1_fully_compliant": v1[key]["fully_compliant"]})
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    groups = defaultdict(lambda: Counter())
    for r in out:
        g = groups[(r["model_alias"], r["strategy"])]
        g["n"] += 1
        if r["pipeline_failure"]:
            g["pipeline_failures"] += 1
            continue
        g["v1_compliant"] += r["v1_fully_compliant"]
        g["v2_compliant"] += r["ears_v2_compliant"]
        g["v2_and_no_compound"] += r["ears_v2_compliant"] and not r["compound_predicate_suspected"]
        for reason in r["fail_reasons"]:
            g["fail_" + reason] += 1
    reasons = sorted({k for g in groups.values() for k in g if k.startswith("fail_")})
    with open(SUMMARY_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["model", "strategy", "n", "pipeline_failures", "v1_compliance_rate", "v2_compliance_rate",
                    "v2_and_no_compound_rate"] + reasons)
        for (model, strategy), g in sorted(groups.items()):
            n = g["n"]
            w.writerow([model, strategy, n, g["pipeline_failures"], f"{g['v1_compliant'] / n:.3f}",
                        f"{g['v2_compliant'] / n:.3f}", f"{g['v2_and_no_compound'] / n:.3f}"] + [g[k] for k in reasons])
    print(f"{len(out)} items checked. Wrote {OUTPUT_PATH} and {SUMMARY_PATH}\n")
    print(f"{'model':14s} {'strategy':18s} {'v1':>6s} {'v2':>6s}")
    for (model, strategy), g in sorted(groups.items()):
        print(f"{model:14s} {strategy:18s} {g['v1_compliant'] / g['n']:6.1%} {g['v2_compliant'] / g['n']:6.1%}")


if __name__ == "__main__":
    main()
