# Publisher Specialist

A Markery specialist agent for rendering confirmed pairs and historian essays into a static research site. The Publisher specialist transforms the project's content files and database records into publishable HTML.

---

## Role

The Publisher specialist is a **production agent**. It has no research or editorial function. Its job is to take what the historian has written and confirmed, resolve all data references (figures, images, Wikipedia summaries), and render a complete, self-contained static site.

The build is deterministic: the same content files and confirmed data always produce the same site. Running `markery site build` again after any content change produces an updated site.

---

## Owns

`projects/<project>/site/` — rendered static site. Gitignored and fully regenerable.

Reads: `data/patents.duckdb`, `data/trademarks.duckdb`, `data/entities.duckdb`, `projects/<project>/content/`, `projects/<project>/matches/confirmed.jsonl`.

---

## Key Commands

```bash
# Build the static site for a project
markery site build <project>

# Build to a specific output directory
markery site build <project> --out projects/<project>/site

# Enhance a specific mark image
markery enhance enhance <serial_no> --out-dir projects/<project>/output/<slug>

# Batch enhance marks matching a SQL condition
markery enhance batch "cf.serial_no IN ('71235764')" --out-dir projects/<project>/output/batch

# Create an image gallery from an enhanced output directory
markery enhance gallery projects/<project>/output/<slug> --title "<title>"

# Draft a Wikipedia article for an entity or confirmed pair
markery wikipedia draft <project> <slug>
```

---

## Content Pipeline

The site builder reads structured Markdown content files from `projects/<project>/content/` and renders them into HTML. The content files are written by the historian.

| Content file | Renders to |
|---|---|
| `content/index-narrative.md` | Project landing page |
| `content/trademarks-narrative.md` | Trademark gallery |
| `content/patents-narrative.md` | Patent gallery |
| `content/entity-<slug>.md` | Entity summary page |
| `content/<slug>.md` | Confirmed pair essay |

Figure references (`[[figure:patent_no]]`) in content files are resolved to stored BLOBs or on-disk PNGs at render time.

---

## How to Use

```
"Build the information-systems site."

"Enhance the mark image for serial number 71235764 and save it to
 projects/information-systems/output/vi-dex."

"Draft a Wikipedia article for the VI-DEX confirmed pair."
```

---

## Reference

| File | Contains |
|---|---|
| `identity.md` | Agent role, capabilities, explicit limits, and scope |
| `instructions/build-site.md` | When and how to build the site; `markery site build` vs `markery publisher build` aliasing |
| `instructions/enhance.md` | Mark image enhancement; single and batch; building image galleries |
| `instructions/wikipedia.md` | Wikipedia drafting workflow; draft → review → submit; content policy requirements |
| `reference/content-pipeline.md` | Content file types, rendering pipeline, figure fallback chain, mark image resolution |
