# PURE dataset (raw)

**Not included in this repository.** The analyses do not need it: `data/pure_150.json` holds the 150
items. To re-run the item-selection scripts in `scripts/`, download `requirements.zip` and
`requirements-xml.zip` from the Zenodo record below into this folder and unzip them as described under Contents.

Source: Ferrari, A., Spagnolo, G. O., & Gnesi, S. (2017). *PURE: a Dataset of
Public Requirements Documents*. Presented at the 2017 IEEE 25th International
Requirements Engineering Conference (RE), Lisbon, Portugal.

- Zenodo record: https://doi.org/10.5281/zenodo.1414117
- License: Creative Commons Attribution 4.0 International (CC BY 4.0)
- 79 publicly available natural language requirements documents, 34,268
  sentences.

## Contents

- `requirements.zip` (33.6 MB, MD5 `bc319fe28619f6290badff328ca159dd`) — the
  79 source documents in their original formats (62 PDF, 13 DOC, 2 HTML,
  1 RTF, 1 HTM), extracted into `requirements_txt/req/`.
- `requirements-xml.zip` (378.7 kB, MD5 `c81235c40f88a2c947ae66e0eddad585`) —
  an 18-document subset with structural XML markup (title / text_body /
  itemize-item), extracted into `requirements_xml/XMLZIPFile/`.

Both checksums match the values published on the Zenodo record.

## Attribution

If you use this data, cite the original paper:

> A. Ferrari, G. O. Spagnolo and S. Gnesi, "PURE: A Dataset of Public
> Requirements Documents," 2017 IEEE 25th International Requirements
> Engineering Conference (RE), Lisbon, Portugal, 2017, pp. 502-505.

This project's own MIT license (see repository root `LICENSE`) does not
apply to this directory's contents.

## Source-match check of the 150 items (`data/pure_150.json`)

- 78 items match their source text exactly, 62 after whitespace
  normalisation, and 10 after removing an inline requirement-ID tag.
- For two of these 10, the automatic check failed and the match was checked
  by hand. Both come from `requirements_txt/req/2000 - nasa x38.doc`
  (a binary Word file), where the requirement number sits after "shall":
  - PURE-061: source `The FTPP system shall (3.1.18) be capable of powering up
    and operating with any combination of 3 of the 5 FCR's active.`
  - PURE-062: source `The maximum time-out value shall (3.2.2.3.7) be 327.68
    microseconds (256 counts of the least significant bit of the fault
    tolerant clock which is 1.28 microseconds).`
  With the ` (3.1.18)` and ` (3.2.2.3.7)` tags removed, each source string
  is identical to the item text, and each occurs once in the file (decoded
  as cp1252).
