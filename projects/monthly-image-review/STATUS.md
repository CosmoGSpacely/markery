# Monthly Image Review — Project Status

**Last updated:** 2026-06-06

---

## Galleries Completed

| Month | Design marks queried | Gallery |
|---|---|---|
| January 1930 | 22 | `output/jan1930/gallery.html` |
| February 1930 | 18 | `output/feb1930/gallery.html` |
| March 1930 | 17 | `output/mar1930/gallery.html` |
| April 1930 | 27 | `output/apr1930/gallery.html` |
| May 1930 | 39 | `output/may1930/gallery.html` |
| June 1930 | 7 | `output/june1930/gallery.html` |

---

## Next Action

Run July–December 1930 months. Command pattern:

```bash
markery enhance gallery \
  --where "cf.mark_draw_cd LIKE '3%' AND cf.filing_dt BETWEEN DATE '1930-07-01' AND DATE '1930-07-31'" \
  --out projects/monthly-image-review/output/july1930/gallery.html \
  --title "Design Marks, July 1930"
```

---

## Research Leads Surfaced

Marks of interest identified through gallery review that may connect to active projects. Move to the relevant project's `RESEARCH-AGENDA.md` when confirmed as a lead.

| Serial | Mark | Filed | Interest |
|---|---|---|---|
| 71299042 | CHICAGO PNEUMATIC CP DEPEND UPON THAT NAME | 1930-04-18 | Full workflow test: essay + Wikipedia draft complete. Enhanced image at `output/apr1930-enhanced/71299042.png`. |

---

## Wikipedia Edits (Phase 16 Track A)

| # | Article | Change | Revision | Date | Status |
|---|---|---|---|---|---|
| 1/5 | Chicago Pneumatic (Stage 4b) | Add TSDR external link for CP trademark (USPTO Serial No. 71299042) | [1355562959](https://en.wikipedia.org/w/index.php?diff=1355562959) | 2026-05-22 | Live, unreverted (confirmed 2026-06-07) — STATUS.md previously mislabeled as "Library Bureau" |
| 2/5 | Library Bureau | Resolve `{{Citation needed}}` — office network citation (1921 catalog) | [1357391696](https://en.wikipedia.org/w/index.php?diff=1357391696) | 2026-06-02 | Live, unreverted (confirmed 2026-06-07) |
| 3/5 | Library Bureau | Add absorption citation — LA Times ad, June 21, 1927, p. 23 | [1357570204](https://en.wikipedia.org/w/index.php?diff=1357570204) | 2026-06-02 | Live, unreverted (confirmed 2026-06-07) |
| 4/5 | Rolodex | Wheeldex trademark citation (USPTO Serial No. 71321669) | [1357918452](https://en.wikipedia.org/w/index.php?diff=1357918452) | 2026-06-05 | Live, unreverted (confirmed 2026-06-07) |
| 5/5 | Remington Rand | Filing systems section — primary sources for filing cabinet and card index products | [1358111560](https://en.wikipedia.org/w/index.php?diff=1358111560) | 2026-06-06 | Live, unreverted (confirmed 2026-06-07) |
| D023 | Chicago Pneumatic | CP monogram trademark citation (USPTO Serial No. 71299042, April 1930) | [1358151236](https://en.wikipedia.org/w/index.php?diff=1358151236) | 2026-06-06 | Live, unreverted (confirmed 2026-06-07) |

---

## Deep-Dive Files

| Serial | Essay | Wikipedia draft |
|---|---|---|
| 71299042 | `essays/chicago-pneumatic-cp.md` | `wikipedia/chicago-pneumatic-cp.wiki` |
