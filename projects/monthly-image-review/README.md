# Monthly Image Review

Exploratory galleries of USPTO trademark design marks organized by filing month. Used to surface visually interesting marks, identify research leads, and test the image enhancement pipeline.

## Process

1. Query `data/trademarks.duckdb` for design marks (`mark_draw_cd LIKE '3%'`) in the target month
2. Fetch images for the result set via TSDR `rawImage` endpoint — stores into `mark_images` table
3. Build gallery directly from DB: `markery enhance gallery --where "..." --out output/<month>/gallery.html`
4. Browse the gallery; select marks of interest
5. Enhance selected marks: `markery enhance enhance <serial> --out-dir output/<month>-enhanced/`

Enhancement (step 5) is manual and selective — not run automatically on the full query result.

## Galleries

| Month | Marks | Gallery |
|---|---|---|
| June 1930 | 7 design marks | `output/june1930/gallery.html` |
