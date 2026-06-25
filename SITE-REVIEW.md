# Site Review — Phase 31 (design pass + annual-review rebuild)

Working doc for Phase 31: rebuild the annual-review project on the post-Phase-28/29
data + library, refresh the site design, and prove the rebuild path. Archived to
`archive/` on completion.

---

## 1. Rebuild verification (the gate) — DONE

`projects/annual-design-review` was restored from git history (pre-Phase-27
archival) and rebuilt on the new stack:

- `markery site build-all` → 1929 (254 marks) + 1930 (240 marks) rendered; the
  portal lists both reviews.
- **Mark images resolve from the externalized assets** (`data/assets/marks/*.png`
  via the Phase 28 `mark_images.file` column) — 254 image files written for 1929,
  proving the blob→file externalization works in the real render path.
- `markery site check annual-design-review` → 0 broken, 0 orphans. Clean.

The chrome (global bar, project bar, project nav, footer, search box) all render.

## 2. Fix: review content was not searchable — DONE

`build_all` produced **0 search records** for annual reviews — the pages showed a
search box but searching found nothing. Fixed: `build_all` now appends a search
record for each review year landing + each of its 12 months. (`search.json` went
from 0 → 26 records for two years; covered by a hermetic test.)

## 3. Adding a review year (1928) — steps + friction

Task: add 1928 to the annual review. Recorded for the "grows with little
supervision" goal.

**Steps (low friction):**
1. Edit `projects/annual-design-review/project.json` → `review_years: [1928, 1929, 1930]`.
2. `markery site build-all`.
3. Result: 1928 rendered (278 marks, 12 months); `search.json` 26 → 39 records;
   `site check` clean (39 pages, 0 broken/orphans).

**Friction observed:**
- **Sparse images on a new year.** 1928 rendered **278 marks but only 7 images**
  (~2.5%), because mark drawings are fetched on-demand (the `mark_images` table is
  ~2.4% of the corpus) and 1928 was never enriched. The page is correct (graceful
  placeholders) but visually thin. *Implication:* adding a review year should be
  paired with a design-mark **image backfill** for that year — a natural job for
  the Phase 30 discovery loop (or a `trademark enrich`-style sweep over the year's
  `mark_draw_cd LIKE '3%'` serials). Logged as a follow-up (D075).
- **No "add a year" command.** `review_years` is hand-edited in `project.json`
  (CLAUDE.md prefers CLI). Minor; a `markery project review-year add <year>` could
  remove the hand-edit. Low priority.
- **`build-all` is whole-site.** Adding one year rebuilds every project + review.
  Fine at current scale; an incremental `--only <project>`/`--year` could help
  later. Low priority.

## 4. Design state + carry-forward

The pre-archival `SITE-REVIEW` (now `archive/SITE-REVIEW-2026-06-21.md`) items
#1–#15 were implemented (Ink Wash palette, card images, patent figures, vertical
timeline, entity-pill links, contrast, active nav, clickable cards, goods
tooltips, empty states, code labels, Guild Products footer). The **open** items
are the People ones — #6 company-formation essay, #8 "People" nav, #16 inventor
links — which are **D072 (deferred narrative half)**, dependent on per-person
narrative content.

So the structural/visual base is solid. Remaining design-pass work is
discretionary refinement (typography scale, review-page density, landing
hierarchy) — pending the user's priorities (§5).

## 5. Open — design-pass priorities (for the user)

The rebuild + search fix are done. What visual refresh, if any, to prioritize is a
taste call — see the proposed options.
