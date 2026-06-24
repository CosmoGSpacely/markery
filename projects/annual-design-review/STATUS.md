# Annual Design-Mark Review — Project Status

**Last updated:** 2026-06-23

---

## Status

Reconfigured from the former *monthly-image-review* project into an **annual** review
(`type: annual-review`). The publisher builds one review per year in `review_years`
(`project.json`) into `site/annual-design-review/<year>/` — a year landing linking twelve
monthly design-mark galleries — each surfaced as a card on the Markery root portal.

`review_years`: **1929, 1930** (design-mark images for both years are fully fetched).

The earlier standalone monthly `output/` galleries were removed; reviews now live in the
built site, generated from this project's config via `markery site build-all`.

## History

The earlier monthly cadence produced the Wikipedia edits recorded in
`wikipedia/submissions.jsonl` (Chicago Pneumatic, Library Bureau, Rolodex, Remington Rand,
Soundex) and the Chicago Pneumatic essay in `essays/` — retained here as project history.

## Next

- Add further years to `review_years` (fetch their design-mark images first with
  `markery trademark enrich`).
