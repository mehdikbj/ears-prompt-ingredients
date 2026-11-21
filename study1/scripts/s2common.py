"""
Shared helpers for Study 2. Every Study 2 script imports this module and is
run from the repository root, e.g. `python3 study2/scripts/build_prompts.py`.

Nothing here makes an API call.
"""
import hashlib
import importlib.util
import json
import os
import re
import subprocess

S2 = "study2"
ARMS_PATH = f"{S2}/config/arms.json"
EXEMPLARS_PATH = f"{S2}/config/fewshot_exemplars.json"
FROZEN_PATH = f"{S2}/config/frozen_settings.json"
COMPONENTS = f"{S2}/prompts/components"
ARM_DIR = f"{S2}/prompts/arms"
MANIFEST_PATH = f"{S2}/prompts/MANIFEST.json"
RESULTS = f"{S2}/results"
RAW_FULL = f"{RESULTS}/raw_inference_study2.jsonl"
RAW_PILOT = f"{RESULTS}/pilot/raw_inference_pilot.jsonl"
EXTRACTED = f"{RESULTS}/extracted_study2.jsonl"
CHECKS = f"{RESULTS}/checks_study2.jsonl"

# Name-only reference prompt (arm A0): byte-identical copy of the zero-shot prompt of the prior
# exploratory run (archive/study1/prompts/zero_shot.txt).
NAME_ONLY_REF = f"{S2}/prompts/reference/name_only.txt"
NAME_ONLY_REF_SHA256 = "f3748dafc3de1bbef3dcea001adf2718123a28465b84f1c212e1d6e32b528b2a"
CHECKER_V2 = "scripts/check_ears_compliance_v2.py"
CHECKER_V2_SHA256 = "4a9bb37b78851e01bf600f65d117f74c9583412f4f1f5938233daaa477c20e8f"
MESSIFIED = "data/pure_150_messified.json"
PURE150 = "data/pure_150.json"
LINEUP = "config/model_lineup.json"
# Logged usage of the prior exploratory run; only used by estimate_cost.py.
PRIOR_RUN_RAW = "archive/study1/results/raw_inference.jsonl"

TIER_SHORT = {"gpt-5.4-nano": "nano", "gpt-5.4-mini": "mini", "gpt-5.4": "gpt-5.4"}


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def read_jsonl(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def sha256_file(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_text(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------- prompts

def render_examples(exemplars):
    """Examples block: heading, then one 'Description / FINAL REQUIREMENT' pair per exemplar."""
    heading = read_text(f"{COMPONENTS}/examples_heading.txt").strip()
    pairs = [f"Description: {e['messified_input']}\nFINAL REQUIREMENT: {e['ears_output']}" for e in exemplars]
    return heading + "\n\n" + "\n\n".join(pairs)


def assemble_arm(arm, exemplars):
    """Return the full [SYSTEM]/[USER] template text for one arm."""
    if arm["family"] == "reference":
        return read_text(NAME_ONLY_REF)
    comp = lambda name: read_text(f"{COMPONENTS}/{name}.txt").strip()
    sections = [comp("header"), comp("patterns")]
    if arm["E"]:
        sections.append(render_examples(exemplars))
    if arm["R"]:
        sections.append(comp("rules"))
    if arm["C"]:
        sections.append(comp("cot"))
    sections.append(comp("output_final_json" if arm["output"] == "final_json" else "output_final_line"))
    return "[SYSTEM]\n" + "\n\n".join(sections) + "\n\n[USER]\n{{messified_text}}\n"


def parse_template(text):
    m = re.search(r"\[SYSTEM\]\s*(.*?)\s*\[USER\]\s*(.*)", text, re.S)
    if not m:
        raise ValueError("Could not parse [SYSTEM]/[USER] sections")
    return m.group(1).strip(), m.group(2).strip()


# ---------------------------------------------------------------- provenance

def git_state(paths=(S2,)):
    """(commit hash, True if the given paths have uncommitted changes). None if git is unavailable."""
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain", "--", *paths], capture_output=True, text=True,
                               check=True).stdout.strip()
        # results/ is expected to change during the run; only design files must be clean.
        ignore = (f"{S2}/results/", f"{S2}/rater_kit/", "__pycache__", ".DS_Store")
        dirty_lines = [l for l in dirty.splitlines() if not any(s in l for s in ignore)]
        return commit, bool(dirty_lines)
    except Exception:
        return None, None


def verify_manifest():
    """Raise if any frozen file differs from MANIFEST.json. Returns the manifest."""
    man = load_json(MANIFEST_PATH)
    bad = []
    for path, expected in man["files"].items():
        if not os.path.exists(path):
            bad.append(f"missing {path}")
        elif sha256_file(path) != expected:
            bad.append(f"changed {path}")
    if bad:
        raise RuntimeError("Frozen design files do not match MANIFEST.json:\n  " + "\n  ".join(bad))
    return man


# ---------------------------------------------------------------- cost

def price_table():
    lineup = load_json(LINEUP)
    return {t["dated_snapshot_id"]: t["price_per_million_tokens_usd"] for t in lineup["tiers"]}


def call_cost(model_id, prompt_tokens, completion_tokens, prices=None):
    p = (prices or price_table())[model_id]
    return (prompt_tokens or 0) / 1e6 * p["input"] + (completion_tokens or 0) / 1e6 * p["output"]


def spent_usd():
    total = 0.0
    for path in (RAW_PILOT, RAW_FULL):
        for r in read_jsonl(path):
            total += r.get("cost_usd") or 0.0
    return total


# ---------------------------------------------------------------- checks

def load_checker_v2():
    if sha256_file(CHECKER_V2) != CHECKER_V2_SHA256:
        raise RuntimeError(f"{CHECKER_V2} differs from the frozen v2 checker")
    spec = importlib.util.spec_from_file_location("ears_v2", CHECKER_V2)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _tok(s):
    return re.findall(r"[a-z0-9']+", s.lower())


def has_leak(text, terms):
    t = " " + text.lower() + " "
    return any(re.search(r"(?<![a-z])" + re.escape(h) + r"(?![a-z])", t) for h in terms)


def copy_share(out, inp, n=4):
    o, i = _tok(out), _tok(inp)
    grams = {tuple(i[k:k + n]) for k in range(len(i) - n + 1)}
    cov = [0] * len(o)
    for k in range(len(o) - n + 1):
        if tuple(o[k:k + n]) in grams:
            cov[k:k + n] = [1] * n
    return sum(cov) / max(len(o), 1)
