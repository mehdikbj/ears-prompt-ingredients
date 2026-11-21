"""
Shared paths and helpers for Study 2b. Run every script from the repository root.
Reuses Study 2's helpers (study2/scripts/s2common.py) unchanged; only paths differ.
Nothing here makes an API call.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "study2", "scripts"))
import s2common as S  # noqa: E402,F401  (Study 2 helpers: load_json, read_jsonl, sha256_file, parse_template, ...)

S2B = "study2b"
ARMS_PATH = f"{S2B}/config/arms.json"
SETTINGS_PATH = f"{S2B}/config/settings.json"
COMPONENTS_2B = f"{S2B}/prompts/components"
ARM_DIR = f"{S2B}/prompts/arms"
MANIFEST_PATH = f"{S2B}/prompts/MANIFEST.json"
RESULTS = f"{S2B}/results"
RAW_FULL = f"{RESULTS}/raw_inference_2b.jsonl"
RAW_PILOT = f"{RESULTS}/pilot/raw_inference_pilot_2b.jsonl"
CHECKS = f"{RESULTS}/checks_2b.jsonl"
PATTERN_FIT_DIR = f"{S2B}/pattern_fit"
PATTERNS = ["ubiquitous", "event-driven", "unwanted-behaviour", "state-driven", "optional-feature"]


def git_state_2b():
    """(commit, dirty) for study2b/ design files. Outputs under study2b/results/ may change during a run (as in
    Study 2, where study2/results/ is ignored), so an interrupted run can resume without committing partial output."""
    import subprocess
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
        st = subprocess.run(["git", "status", "--porcelain", "--", S2B], capture_output=True, text=True,
                            check=True).stdout.splitlines()
        ignore = (f"{S2B}/results/", "__pycache__", ".DS_Store")
        return commit, any(not any(x in l for x in ignore) for l in st)
    except Exception:
        return None, None


def spent_usd_2b():
    return sum((r.get("cost_usd") or 0.0) for p in (RAW_PILOT, RAW_FULL) for r in S.read_jsonl(p))


def verify_manifest_2b():
    man = S.load_json(MANIFEST_PATH)
    bad = [p for p, h in man["files"].items() if not os.path.exists(p) or S.sha256_file(p) != h]
    if bad:
        raise RuntimeError("Study 2b design files do not match MANIFEST.json: " + ", ".join(bad))
    return man
