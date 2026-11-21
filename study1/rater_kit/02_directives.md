# Rating directives

They interpret the anchors in `01_criteria.md`; they do not change them. Apply them to every row of your sheet.

1. **Formatting.** Markdown emphasis and labels such as "EARS:" are ignored
   for every criterion.
2. **Generic objects.** A requirement that leaves its object generic (e.g.
   "data products") scores 3 on Unambiguity, even when the input is equally
   generic.
3. **"shall be able to".** It weakens the obligation: −1 on EARS
   well-formedness, even when the pattern is valid.
4. **Informal wording.** Slightly informal wording costs 1 point on
   Unambiguity. Colloquial wording carried over wholesale from the input
   scores 1 on Unambiguity.
5. **Unbounded superlatives.** "maximize", "to the greatest extent
   possible" and similar score 3 on Unambiguity.
6. **Invented content.** Implementation mechanisms the input does not state
   or imply count as invented content for Faithfulness, also when they are
   introduced as "e.g." examples.
7. **Faithfulness reference.** Faithfulness is judged against the messified
   input only. Keeping a vagueness that is already in the input, or
   re-using the input's wording, is faithful.
8. **Singularity.** Browse-and-search wording ("looking through and
   searching") is one behaviour. A goal and the means to reach it in one
   obligation count as more than one behaviour.
9. **Circular conditions.** A response that is a distinct action is
   well-formed EARS even when it follows directly from the condition (not
   logged in → require login). A response that only repeats or negates the
   trigger is malformed: EARS 3 and Unambiguity 3.
10. **Incomplete state clause.** A state clause without a state ("WHILE
    backup mode") scores 2 on EARS well-formedness.
