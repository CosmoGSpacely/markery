# Content Pipeline Reference

The Publisher specialist reads structured Markdown content files written by the historian and renders them into a static HTML site. This document describes the content file types, their expected locations, and how the rendering pipeline processes them.

---

## Content Files

All content files live in `projects/<project>/content/`. The site builder reads all `.md` files in this directory.

| File pattern | Page type | Written by historian |
|---|---|---|
| `index-narrative.md` | Project landing page | After all other content is complete |
| `trademarks-narrative.md` | Trademark gallery | After all mark essays are written |
| `patents-narrative.md` | Patent gallery | After all pair essays are written |
| `entity-<slug>.md` | Entity summary | One per entity in scope |
| `<slug>.md` | Confirmed pair essay | One per confirmed pair |

Content schemas (required structure for each file type) are defined in the Historian persona:
`src/markery/specialist/historian/persona/content-schemas/`

---

## Figure References

Content files may include figure references in the form:

```
[[figure:US1630977A]]
```

The site builder resolves these references at render time:
1. Check `patents.duckdb` for a stored BLOB (`patent_figures` table)
2. Fall back to `projects/<project>/output/<patent_no>.png` on disk
3. If neither exists, the reference renders as a placeholder

Fetch figures in advance: `markery patent fetch <project> --confirmed`

---

## Mark Images

Mark images stored in `trademarks.duckdb` (`mark_images` table) are written to `site/images/marks/<serial_no>.png` during the build and linked from gallery and essay pages.

Enhanced versions (from `markery enhance`) are preferred when available in `projects/<project>/output/`.

---

## Wikipedia Integration

For entities and confirmed pairs with Wikipedia articles, the builder can pull a summary paragraph and link. This is optional and requires a Wikipedia article to exist. Draft new articles: `markery wikipedia draft <project> <slug>`.

---

## Implementation

`src/markery/specialist/publisher/build.py` — `build_site()`
`src/markery/specialist/publisher/render.py` — Markdown rendering, figure resolution, image linking
`src/markery/specialist/publisher/queries.py` — database reads for confirmed pairs, entities, mark images
