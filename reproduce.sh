#!/usr/bin/env bash
# Re-runs every analysis of the paper from the committed raw API records, then
# checks that the regenerated results match the committed ones.
#
#   pip install -r requirements.txt
#   ./reproduce.sh
#
# No API call is made. The repository is not modified: the pipeline runs on a
# temporary copy that uses the folder names the scripts were frozen with
# (study2/ = Study 1, study2b/ = Study 2; see README.md).
set -euo pipefail

REPO="$(cd "$(dirname "$0")" && pwd)"
PY="${PYTHON:-python3}"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

cp -R "$REPO/study1" "$WORK/study2"
cp -R "$REPO/study2" "$WORK/study2b"
cp -R "$REPO/data" "$REPO/scripts" "$REPO/config" "$WORK/"
mkdir -p "$WORK/paper/sections" "$WORK/paper/figures"

run() { echo "+ $*"; "$PY" -B "$@"; }
cd "$WORK"

echo "== Checker self-test"
run scripts/check_ears_compliance_v2.py --selftest

echo "== Study 1"
run study2/scripts/extract_answers_study2.py --pilot
run study2/scripts/check_study2.py --pilot
run study2/scripts/extract_answers_study2.py
run study2/scripts/check_study2.py
run study2/scripts/analyze_study2.py
run study2/scripts/analyze_human_study2.py --no-git
run study2/scripts/analyze_post_hoc.py

echo "== Study 2"
run study2b/scripts/extract_and_check_2b.py --pilot
run study2b/scripts/extract_and_check_2b.py \
    --raw study2b/results/pilot_effort_low/raw_inference_pilot_2b.jsonl \
    --out study2b/results/pilot_effort_low/checks_pilot_2b.jsonl
run study2b/scripts/extract_and_check_2b.py
run study2b/scripts/analyze_study2b.py
run study2b/pattern_fit/analyze_pattern_fit.py
run study2b/human_eval/analyze_human_2b.py --no-git
run study2b/scripts/analyze_post_hoc_2b.py
run study2b/scripts/analyze_post_hoc_ph14.py

echo "== Tables and figures of the paper"
run study2/scripts/make_paper_results.py
run study2b/scripts/make_paper_results_2b.py
run study2b/scripts/make_paper_example.py

cd "$REPO"
echo "== Frozen design files"
"$PY" -B tools/check_frozen.py "$WORK"
echo "== Regenerated results vs committed results"
"$PY" -B tools/compare_results.py "$WORK" "$REPO"
