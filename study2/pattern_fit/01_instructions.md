# Which EARS patterns does each input admit? Instructions for annotators

You will read 150 short, informal descriptions of what someone wants from a
software system. For each one, decide **which EARS patterns a correct
requirement written from it could use**. You do not see any generated
requirement. While you annotate, do not open any model output, rating sheet,
result file or the paper, and judge each description on its own, not on
what you remember of earlier outputs.

Work alone. Do not discuss items with the other annotator or anyone else
until both sheets are committed. Do not use an AI assistant. Annotator A
(R3) starts first; annotator B (R1) never sees sheet A before committing
sheet B.

## The five EARS patterns (Mavin et al., 2009)

| Pattern | Use it when the description … | Template |
|---|---|---|
| Ubiquitous | states something that always holds, with no condition | The \<system\> shall \<response\>. |
| Event-driven | ties the behaviour to a triggering event (something happens, a user does something) | WHEN \<trigger\>, the \<system\> shall \<response\>. |
| Unwanted behaviour | ties the behaviour to an undesired situation (failure, error, fault, misuse) | IF \<trigger\>, THEN the \<system\> shall \<response\>. |
| State-driven | ties the behaviour to a state that holds for a while (while in a mode, while a condition lasts) | WHILE \<state\>, the \<system\> shall \<response\>. |
| Optional feature | says, or clearly implies, that the feature may or may not be present in a given product, installation or configuration | WHERE \<feature is included\>, the \<system\> shall \<response\>. |
| Complex | needs a combination of the above (e.g. WHILE … WHEN …) | — |

Decision rules:

1. Judge from the description only, as the model saw it. Do not use outside
   knowledge of the system.
2. Mark **every** pattern a competent requirements engineer could defend for
   this description (1 = admissible, 0 = not). Usually one pattern fits; mark
   more than one only when the description genuinely supports both.
3. **Optional feature** is admissible only if the description says or clearly
   implies that the feature is optional, configurable per installation, or
   present only in some products ("if the network has text messaging at all",
   "for sites that buy the reporting module"). A feature that is simply wanted
   is **not** optional. A deployment context ("when deployed", "on our
   servers") is not an optional feature.
4. A condition that is only background ("since people use it over the web")
   does not make a conditional pattern admissible; Ubiquitous then fits.
5. In `best_pattern`, write the single pattern you would choose (one of:
   ubiquitous, event-driven, unwanted-behaviour, state-driven,
   optional-feature, complex). It must be one you marked admissible.
6. Use `notes` for anything that made the item hard.

## Your sheet

`02_sheet_annotator_<A|B>.csv` has one row per description, in a random order
that differs between annotators. Fill the columns `adm_ubiquitous`,
`adm_event_driven`, `adm_unwanted_behaviour`, `adm_state_driven`,
`adm_optional_feature`, `adm_complex` with 0 or 1, then `best_pattern` and
`notes`. Do not change any other column.

Expect about 2–3 hours in total (`04_time_log_<A|B>.csv` is optional).

## After both sheets are returned

Each sheet is committed unmodified, with its SHA-1, before anyone compares
them. The primary analysis uses the **union** of the two sheets, which needs
no discussion. The two annotators may then resolve their disagreements
together in `03_consolidated.csv` (one `resolution_note` per item); the
consolidated set is used only in a sensitivity analysis.
