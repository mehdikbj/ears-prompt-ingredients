# Inputs: informal paraphrases of the 150 items

The models never see the PURE items, only these paraphrases. Output: `data/pure_150_messified.json` (fields:
`id`, `messified_text`, `word_count`, `generator_model`, `generated_date`), joined to `data/pure_150.json` by `id`.

## Generation

Generator: Claude Sonnet 5 (`claude-sonnet-5`), in 19 batches, one per source document. Every batch used the
template below, word for word; only the `ITEMS` list changed. The generation cannot be replayed; the prompts and
outputs of each batch are archived in `data/interim/messify_batches/` (`<document>_prompt.txt`,
`<document>.json`). `scripts/assemble_messified.py` builds `data/pure_150_messified.json` from them.

````
You are generating "messified" inputs for an empirical requirements-engineering study. Each of the items below is a clean, formal software requirement (verbatim from the PURE dataset). Your job: rewrite each one as a rambling, informal, ambiguous description of what a non-technical stakeholder wants, as if they were describing it out loud in a meeting or a quick verbal walkthrough — NOT a written user story, NOT bullet points.

RULES (apply to every item):

PERSONA/REGISTER: first-person, informal, conversational. Natural filler is expected ("oh, and," "I guess," "yeah, so"). Same register for every item — don't vary between email/chat/meeting-notes styles.

LENGTH: 25-70 words, one paragraph, no bullets/numbering.

ALWAYS REMOVE OR REWORD:
- The modal verb "shall"/"must" -> replace with natural obligation language ("I want," "we need," "it should probably," "it'd be nice if").
- Formal EARS trigger keywords used as a structured clause opener (WHEN/WHILE/IF/WHERE at the start of a formal condition) -> reword as casual conditional language. Ordinary conversational "if"/"when" elsewhere in the sentence is fine.
- The source's exact clause structure and subject naming (e.g. "the user," "the system") -> reword in the stakeholder's own words ("someone," "the thing," "it").
- At least one precise term replaced with something vaguer where the source has one (a threshold, a count, a qualifier) — EXCEPT exact numeric/quantitative values, see next rule.

ALWAYS PRESERVE:
- The underlying actor, trigger condition, action, and response — reworded, never deleted. A competent reader must be able to reconstruct the original requirement's meaning from your messified version.
- EXACT numeric/quantitative values (e.g. "327.68 microseconds," "59 characters," "3 rate groups") verbatim — casualize the FRAMING around a number, never round, invent, or drop the number itself. Where a source item is dense with technical constants, lean on "the engineers will know what I mean about the exact number" framing rather than pretending a stakeholder would casually restate it precisely.

HARD CONSTRAINT: never use the literal word "shall" anywhere in your output. Never copy a contiguous run of 6+ words verbatim from the source text.

WORKED EXAMPLES:
Source: "Where EIRENE facilities are not available within the currently selected network, the user shall be given a visible indication."
Messified: "Oh, and if someone's on a network that doesn't actually have EIRENE, they need some way to know — like, something on the screen so they're not just sitting there wondering if it's working."

Source: "The scheduler shall support up to 3 rate groups per vehicle mode."
Messified: "For the scheduling side, I think we need it to juggle a few rate groups per vehicle mode — three should cover it, that's the max we'd realistically need."

Source: "Privileged users shall be able to delete an existing inspection unless it is "locked down"."
Messified: "If someone's got the right permissions they should be able to get rid of an old inspection — unless it's been locked, obviously, then just leave it alone."

Source: "Sequence's length must not be more than a line (59 characters)"
Messified: "Also, that auto-type sequence thing — keep it to one line, nothing crazy long, so like under 60 characters or so."

Source: "The maximum time-out value shall be 327.68 microseconds (256 counts of the least significant bit of the fault tolerant clock which is 1.28 microseconds)."
Messified: "There's also a timeout thing tied to the clock — it has to work out to exactly 327.68 microseconds, based on 256 ticks where each tick's 1.28 microseconds. I know that sounds oddly specific but that's the number the engineers need."

YOUR TASK: messify each of the following items. Return ONLY a raw JSON array (no markdown fences, no commentary) with one object per item: {"id": "...", "messified_text": "..."}. Preserve the ids exactly as given. Output must be valid JSON parseable by json.loads.

ITEMS:
[... that batch's PURE-XXX items as a JSON array of {"id": ..., "text": ...} ...]
````

## Checks

`scripts/check_messified.py` writes `data/pure_150_messified_qc_report.json`:

- rejected: the word "shall"; six or more consecutive words copied from the source;
- flagged for a manual look: "must"; a length outside 25–70 words; no informal marker.

Every input passed. The inputs have 21 to 55 words. Each input was then checked by hand against its source.
