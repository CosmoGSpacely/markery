# D024 — Soundex Article Addition

**Target article:** Soundex  
**Target section:** History  
**Edit type:** One or two sentence addition with `<ref>` citations  
**Depends on:** D023 complete and live ≥48 hours unreverted  
**Status:** Draft ready. Pending D023 completion.

---

## DB evidence (Phase 16 P2 finding)

The SOUNDEX trademark filing is fully documented in `data/trademarks.duckdb`:

| Field | Value |
|---|---|
| Serial number | 71246709 |
| Mark | SOUNDEX |
| Filing date | March 31, 1927 |
| Filing entity | RAND KARDEX BUREAU, INC. (574 Main St, Tonawanda, NY) |
| Goods description | Blank and partially-printed cards and forms for indexes; index guide cards and separator cards of the type used for phonetic indexes; frames and holders for index cards |
| Registration number | 0230958 |
| Registration date | August 9, 1927 |

The Russell-Odell patent (US1261167A) was granted April 2, 1918, assigned to Remington Typewriter Company. The 9-year gap between patent grant (1918) and trademark filing (1927) spans the period in which Rand Kardex Bureau emerged as the commercial vehicle for the product.

---

## Sentences to add

Place in the **History** section, after the sentence describing Russell and Odell's patent and before (or within) any discussion of the system's adoption or government use.

```wikitext
The Russell-Odell phonetic indexing algorithm was patented in 1918 (US 1,261,167) by Robert C. Russell and Margaret K. Odell, assigned to Remington Typewriter Company.<ref>{{cite patent|country=US|number=1261167|inventor=Russell, Robert C.; Odell, Margaret K.|assign1=Remington Typewriter Company|title=Index|gdate=1918-04-02}}</ref> The SOUNDEX trademark was subsequently filed on March 31, 1927, by Rand Kardex Bureau, Inc., covering index cards, forms, and holders used for phonetic indexing systems.<ref>{{cite web|url=https://tsdr.uspto.gov/#caseNumber=71246709&caseType=SERIAL_NO&searchType=statusSearch|title=Trademark Serial No. 71246709 — SOUNDEX|publisher=USPTO Trademark Status and Document Retrieval|access-date=2026-06-01}}</ref>
```

**If the patent sentence already exists** (the article may already cite US1261167), use only the trademark sentence:

```wikitext
The SOUNDEX trademark (USPTO Serial No. 71246709) was filed on March 31, 1927, by Rand Kardex Bureau, Inc., covering index cards and forms for phonetic indexing systems.<ref>{{cite web|url=https://tsdr.uspto.gov/#caseNumber=71246709&caseType=SERIAL_NO&searchType=statusSearch|title=Trademark Serial No. 71246709 — SOUNDEX|publisher=USPTO Trademark Status and Document Retrieval|access-date=2026-06-01}}</ref>
```

---

## Entity name note

Use **Rand Kardex Bureau** or **Rand Kardex Bureau, Inc.** — not "Remington Rand." The Remington-Rand merger (which created Remington Rand Inc.) closed in mid-1927, after the March 31 filing date. The DB `owner` table lists RAND KARDEX BUREAU, INC. as the filing-date owner, with no Remington Rand Inc. owner record. This is consistent with `RESEARCH.md §SOUNDEX Ownership Timeline`.

---

## Edit summary

```
Add primary source citations for SOUNDEX patent and trademark filing (USPTO 71246709, 1927, Rand Kardex Bureau)
```

---

## Confirmed insertion point (verified 2026-06-01)

Use the **trademark-only variant** — the 1918 patent (US1261167) is already cited in the article with `{{US patent reference|number=1261167|...}}`. There is no mention of the trademark filing or Rand Kardex Bureau.

Insert the trademark-only sentence immediately after the existing 1922 patent sentence:
> "...and 1922.<ref>{{US patent reference|number= 1435663...}}</ref>"

The full paragraph after the insertion will read:
> "Soundex was developed by Robert C. Russell and Margaret King Odell and patented in 1918 and 1922. The SOUNDEX trademark (USPTO Serial No. 71246709) was filed on March 31, 1927, by Rand Kardex Bureau, Inc., covering index cards and forms for phonetic indexing systems. A variation, American Soundex, was used in the 1930s..."

---

## Pre-submission checklist

- [ ] D023 (Chicago Pneumatic citation) is live and unreverted ≥48 hours
- [x] Insertion point confirmed: after 1922 patent sentence, before "A variation, American Soundex" sentence
- [x] Patent already cited — use trademark-only variant
- [ ] Diff reviewed before submitting
- [ ] After submitting: record edit URL and timestamp in `projects/information-systems/STATUS.md`
