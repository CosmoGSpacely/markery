# D023 — Chicago Pneumatic Inline Citation

**Target article:** Chicago Pneumatic  
**Target section:** History (paragraph covering the 1920s–1930s branding period)  
**Edit type:** One sentence addition with `<ref>` citation  
**Status:** Draft ready. Pending: verify Stage 4b still live, verify account edit count ≥5, then submit.

---

## Sentence to add

```wikitext
The CP monogram design trademark (USPTO Serial No. 71299042) was filed on April 18, 1930, covering pneumatic tools, air compressors, and related apparatus.<ref>{{cite web|url=https://tsdr.uspto.gov/#caseNumber=71299042&caseType=SERIAL_NO&searchType=statusSearch|title=Trademark Serial No. 71299042|publisher=USPTO Trademark Status and Document Retrieval|access-date=2026-06-01}}</ref>
```

---

## Insertion point

The sentence belongs in the History section, in a paragraph about the company's branding or trademark activity in the 1920s–1930s. It should follow any mention of the CP monogram or the company's product branding. If no such sentence exists nearby, it can be added at the end of the paragraph covering that period.

**Do not** insert it into the infobox or the Products section. It is a historical fact about when the mark was formally registered, appropriate for the narrative History section.

---

## Edit summary

```
Add primary source citation for CP monogram trademark (USPTO Serial 71299042, April 1930)
```

---

## Submission procedure (markery wikipedia tooling)

```bash
# 1. Fetch current article text
markery wikipedia fetch "Chicago Pneumatic"
# → writes projects/monthly-image-review/wikipedia/chicago-pneumatic-current.wiki

# 2. Edit the fetched file: insert the sentence above into the History section
#    Insertion point: after the 1925 oil-well drilling paragraph, before the 1939 impact wrench paragraph

# 3. Generate and review diff
markery wikipedia diff "Chicago Pneumatic" chicago-pneumatic-current.wiki

# 4. Submit after reviewing diff
markery wikipedia submit "Chicago Pneumatic" \
  --summary "Add primary source citation for CP monogram trademark (USPTO Serial 71299042, April 1930)"
```

**Alternative (manual):** Open https://en.wikipedia.org/wiki/Chicago_Pneumatic in the edit interface, find the History section paragraph covering 1925, and insert the sentence after the oil-well drilling sentence.

---

## Pre-submission checklist

- [x] Stage 4b external link still present and unreverted — confirmed 2026-06-01 (live since 2026-05-22)
- [ ] Account has ≥5 confirmed non-reverted mainspace edits — **BLOCKED**: 1 of 5 (need 4 more)
- [x] The insertion point exists (after 1925 oil-well drilling paragraph, before 1939 impact wrench paragraph)
- [x] Article title corrected: "Chicago Pneumatic" (not "Chicago Pneumatic Tool Company")
- [ ] Diff reviewed before submitting
- [ ] After submitting: monitor for 48 hours; record edit URL in STATUS.md
