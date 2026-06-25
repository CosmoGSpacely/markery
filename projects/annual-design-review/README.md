# Annual Design-Mark Review

An **annual** review project (`type: annual-review`) of USPTO trademark **design marks**
(`mark_draw_cd LIKE '3%'`), organized by filing year. Each year listed in
`project.json`'s `review_years` is built into the Markery site as a **year landing page**
linking twelve **monthly galleries**, and surfaced as a card on the Markery root portal.

This supersedes the earlier *monthly* image-review project: the standalone monthly
`output/` galleries are gone; reviews are now generated into the site by the publisher
from this project's config.

## Config (`project.json`)

```json
{"type": "annual-review", "review_years": [1929, 1930]}
```

Add a year to `review_years` and rebuild to produce its annual review.

## Build

```
markery site build-all          # builds every project + the annual reviews + portal
```

Output: `site/annual-design-review/<year>/index.html` (year landing) +
`site/annual-design-review/<year>/NN.html` (monthly galleries), with design-mark images
under `site/annual-design-review/<year>/img/`. Each year is a card on `site/index.html`.

## What a gallery shows

Per design mark: the mark image (or word-mark placeholder), owner · state, filing date,
and goods/services. Source data is read from `data/trademarks.duckdb`; fetch missing
images with `markery trademark enrich <serial>` before building.
