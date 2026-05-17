# Monthly Image Review

Exploratory galleries of USPTO trademark design marks organized by filing month. Used to surface visually interesting marks, identify research leads, and test the image enhancement pipeline.

## Outputs

| Folder | Contents |
|---|---|
| `output/may1930-designs/` | 39 design marks filed May 1930 — raw TSDR images, gallery with goods/services |
| `output/enhanced-may1930-designs/` | Real-ESRGAN 4× enhanced versions (in progress) |

## Process

1. Query `trademarks.duckdb` for design marks (`mark_draw_cd LIKE '3%'`) in the target month
2. Fetch images via TSDR `rawImage` endpoint
3. Build gallery with `python -m image_enhancement gallery`
4. Optionally enhance with `python -m image_enhancement batch`
