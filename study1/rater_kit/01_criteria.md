# Rating criteria

Rater-facing instrument for sheet 1 of the human ratings (Study 1 and Study 2). The directives in
`02_directives.md` interpret these anchors.

## What you are rating

Each item shows two things only:

- **Messified input** — a rambling, conversational stakeholder request.
- **Generated requirement** — one candidate EARS-style requirement a
  language model produced from that input.

You are **not** shown the original clean gold-standard requirement, the
model that produced the candidate, the prompting strategy used, or
whether it passed any automatic check. Judge each candidate only against
the messified input and your own judgment of requirement quality — not
against a hidden reference.

## The four criteria

Score every item on all four criteria, each on a **1–5 Likert scale**
(1 = poor, 5 = excellent), independently of each other — a low score on
one criterion should not automatically pull down another.

### 1. Faithfulness

Does the requirement accurately capture what the messified input asked
for, without inventing content the input doesn't support (actors,
conditions, numeric thresholds, scope) and without dropping something the
input clearly asked for?

| Score | Anchor |
|---|---|
| 1 | Contradicts the input, or is essentially unrelated to it. |
| 2 | A substantial invented detail (e.g. a specific number, condition, or actor not implied by the input) or a clear omission of something the input asked for. |
| 3 | Mostly faithful; one minor invented detail or interpretive stretch that doesn't change the core meaning. |
| 4 | Faithful; at most a small, defensible inference already implied by the input's wording. |
| 5 | Fully faithful — captures exactly what the input describes, nothing invented, nothing missing. |

### 2. Unambiguity

Is the requirement's language precise enough that two competent readers
would agree on what satisfies it, or does it lean on vague/subjective
terms ("sufficient," "quickly," "as needed," "appropriate")?

| Score | Anchor |
|---|---|
| 1 | Pervasively vague; unclear what would actually satisfy the requirement. |
| 2 | Multiple vague terms, or one vague term sitting in a load-bearing part of the sentence (the trigger or the core action). |
| 3 | One vague or subjective term, but overall intent is still clear. |
| 4 | Precise throughout; wording could be tightened stylistically but there's no real ambiguity. |
| 5 | Fully precise — no vague or subjective terms, unambiguous to any reader. |

### 3. Singularity

Does the requirement express exactly one atomic, testable behavior,
rather than bundling multiple distinct obligations into one "shall"?

| Score | Anchor |
|---|---|
| 1 | Bundles several clearly distinct or unrelated capabilities into one sentence. |
| 2 | Contains at least two behaviors that would need separate acceptance tests. |
| 3 | Mostly one behavior, but one closely-related sub-action is folded in (borderline call). |
| 4 | Single behavior; at most a small connective clause (e.g. a "so that" rationale) that doesn't add a separately-testable obligation. |
| 5 | Cleanly atomic — one shall, one behavior, one clear test. |

### 4. EARS well-formedness (holistic)

Does this read as a proper EARS-pattern statement — correct pattern for
its trigger/condition, "shall" as the operative modal, a coherent
trigger-to-action structure — in your own judgment?

**Ignore incidental formatting noise** (stray markdown like `**EARS:**`
prefixes, asterisks, bold markers left over from extraction) unless it
actually obscures the requirement's structure.

| Score | Anchor |
|---|---|
| 1 | Not recognizable as an EARS-pattern requirement. |
| 2 | Attempts an EARS pattern but it's misapplied, or the modal/structure is broken. |
| 3 | Correct pattern chosen, but with a structural flaw (e.g. the trigger and the shall-clause aren't properly connected). |
| 4 | Correct, well-formed EARS statement; only a cosmetic issue (formatting, stray markup) if present. |
| 5 | Textbook EARS statement — correct pattern, single "shall," clean structure. |
