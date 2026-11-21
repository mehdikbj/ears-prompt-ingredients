# Criterion 5: equivalence to the source requirement (sheet 2)

Use this sheet **only after** your sheet 1 (the four criteria) has been
returned and committed. Do not change sheet 1 afterwards.

Each row shows the **original requirement** from the source specification
and a **generated requirement**. The model never saw the original: it saw an
informal paraphrase of it. Score whether the generated requirement says the
same thing as the original, ignoring EARS form, wording and style.

| Score | Meaning |
|---|---|
| 5 | Same obligation: same actor, trigger or condition, response and constraints. |
| 4 | Same obligation; a detail is vaguer or slightly more specific, without changing what a tester would check. |
| 3 | Core obligation kept, but a condition, value or constraint is missing, changed or added, so a test would differ. |
| 2 | Related but different obligation (e.g. a different response, actor or trigger). |
| 1 | Unrelated, contradictory, or not a requirement. |

Rules:

- A number or name that the informal input had already lost (the paraphrase
  dropped it) still counts as missing: score what the generated requirement
  says, not whose fault it is.
- A WHERE clause that turns an unconditional requirement into an optional
  one changes the obligation (3 at most).
- Work alone, without AI tools; do not discuss items with the other rater
  until both sheets are committed.
