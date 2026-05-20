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

The site builder resolves these references at build time using a `figure_index` built from `patent_figures` BLOBs in `patents.duckdb`. The fallback chain:

1. **`patents.duckdb` BLOB** (`patent_figures` table) — the build reads the BLOB, writes it to `site/images/patents/<patent_no>.png`, and adds the patent to the `figure_index`. The `[[figure:]]` reference renders as a `<figure class="patent-figure">` element with a caption.
2. **No figure available** — the patent is not in the `figure_index`. The `[[figure:]]` tag renders as nothing. The surrounding prose still renders; only the figure element is absent.

There is no silent fallback to an on-disk PNG for inline `[[figure:]]` references — if the BLOB is not in `patents.duckdb`, the figure does not appear.

**Check figure availability before building:**
```bash
markery historian prepare <project>
```
The `figures_available` field in `BRIEF.md` reports how many confirmed patents have stored figures.

**Fetch missing figures:**
```bash
markery patent fetch <project> --confirmed
```

**Diagnosing a missing figure in a rendered essay:**
1. Check `BRIEF.md` — is `figures_available` less than the confirmed patent count?
2. Query `patents.duckdb`: `SELECT patent_no FROM patent_figures WHERE patent_no = 'US1630977A'`
3. If absent, run `markery patent fetch <project> --confirmed` and rebuild the site.

**If a figure is permanently unavailable** (pre-1920 patents often lack EPO figure data), use language like "No figure is available from EPO records for this patent" in the essay body and omit the `[[figure:]]` tag.

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
