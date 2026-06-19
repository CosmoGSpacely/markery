# John Deere — Trademark Registration Citation

**Target article:** John Deere
**Target section:** History (the leaping-deer logo/trademark paragraph)
**Edit type:** One-sentence addition with a `<ref>` USPTO citation
**Source project:** animal-marks-1930 / `john-deere-moline-ill-us979019a`

---

## DB evidence

| Field | Value |
|---|---|
| Serial number | 71055630 |
| Mark | JOHN DEERE MOLINE, ILL. |
| Filing date | April 8, 1911 |
| Registration | 0088248 (September 10, 1912) |
| Owner | DEERE & COMPANY |
| Goods | PLOWS, CULTIVATORS, HARROWS, MOWERS, REAPERS, GRAIN HARVESTERS … (full farm-implement line) |

Contemporaneous patent (not cited in this edit — kept off the logo paragraph as
off-scope): US979019A "Reversible-Disk Plow", Deere & Co, granted 1910-12-20.

## Why this edit is sound

- The article's History section discusses the leaping-deer logo (images captioned
  "used between 1876 and 1912" and "used between 1912 and 1936") but cites **no USPTO
  records at all**. Adding the precise registration of the 1911-filed / 1912-registered
  "JOHN DEERE MOLINE, ILL." mark substantiates the existing "1912" claim with a primary
  source — additive, on-topic, low revert risk.
- Trademark-only citation (like the Soundex precedent). No patent/embodiment claim is
  forced into a logo paragraph.
- Period-correct: owner is **Deere & Company**, the filing-date owner of record.

## The edit (find-and-replace)

**Find** (unique in article, line 124, logo paragraph):

```
Over the years, the logo has had minor changes and pieces removed.
```

**Replace with:**

```
Over the years, the logo has had minor changes and pieces removed. The "JOHN DEERE MOLINE, ILL." trademark (USPTO Serial No. 71055630), covering plows and a range of farm implements, was filed on April 8, 1911 and registered on September 10, 1912.<ref>{{cite web|url=https://tsdr.uspto.gov/#caseNumber=71055630&caseType=SERIAL_NO&searchType=statusSearch|title=Trademark Serial No. 71055630 — JOHN DEERE MOLINE, ILL.|publisher=USPTO Trademark Status and Document Retrieval|access-date=2026-06-18}}</ref>
```

## Command

```
markery wikipedia replace "John Deere" \
  --project animal-marks-1930 \
  --find 'Over the years, the logo has had minor changes and pieces removed.' \
  --replace 'Over the years, the logo has had minor changes and pieces removed. The "JOHN DEERE MOLINE, ILL." trademark (USPTO Serial No. 71055630), covering plows and a range of farm implements, was filed on April 8, 1911 and registered on September 10, 1912.<ref>{{cite web|url=https://tsdr.uspto.gov/#caseNumber=71055630&caseType=SERIAL_NO&searchType=statusSearch|title=Trademark Serial No. 71055630 — JOHN DEERE MOLINE, ILL.|publisher=USPTO Trademark Status and Document Retrieval|access-date=2026-06-18}}</ref>' \
  --summary 'Add primary-source USPTO citation for the JOHN DEERE MOLINE, ILL. trademark (Serial No. 71055630, filed 1911, registered 1912)'
```

Run without `--yes` to review the live diff and confirm interactively before the POST.
Records to `projects/animal-marks-1930/wikipedia/submissions.jsonl`.

---

## Result (2026-06-19) — LIVE

Submitted as **[rev 1360151379](https://en.wikipedia.org/w/index.php?diff=1360151379)**;
verified live by `markery wikipedia check-revision`.

**Correction applied at submit time:** the mark was rendered in **normal case**
("John Deere Moline, Ill.") rather than the all-caps DB form. The first attempt with
the all-caps mark name tripped Wikipedia's AbuseFilter #50 ("Shouting") — a *warn*
action, so nothing was saved — and the title-case re-submit went through. This matches
[MOS:TM](https://en.wikipedia.org/wiki/MOS:TM) (don't render trademarks in all caps).
The `--find`/`--replace`/`--summary` above should use the title-case form.
