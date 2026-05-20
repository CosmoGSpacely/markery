# Commerce and Technology Historian

A Claude specialist for researching American commercial and industrial history through the combined USPTO trademark and patent record, 1870–1950. The specialist identifies and documents **confirmed patent-trademark pairs** — cases where a specific patent and a specific trademark, held by the same company, describe the same product — and builds **project research sites** that publish those findings as linked web content.

---

## What It Does

### Research mode

- Queries the trademark and patent databases for an entity's filings
- Identifies candidates for patent-trademark correspondence using date, entity, and goods evidence
- Confirms pairs with a defensible historical argument
- Answers historical questions about companies, product categories, mark types, and filing patterns

### Site curation mode

Writes structured Markdown content for five page types. The Markery site builder (`markery site`) renders these into a static HTML site at `projects/<project>/site/`.

| Page | Output file | What it contains |
|---|---|---|
| Trademark gallery | `content/trademarks-narrative.md` | Portfolio narrative + timeline + card grid |
| Patent gallery | `content/patents-narrative.md` | Patent strategy narrative + timeline + card grid |
| Entity summary | `content/entity-<slug>.md` | Company identity, filing record, research significance |
| Match essay | `content/<slug>.md` | Full research essay for one confirmed pair |
| Project landing | `content/index-narrative.md` | Scope, entities, method, confirmed findings |

See `content-schemas/` for the required structure of each page type.

---

## Databases

The specialist reads three DuckDB files via `ATTACH` cross-database queries:

| Database | Contents | Key tables |
|---|---|---|
| `data/trademarks.duckdb` | 25,473 USPTO trademark filings, 1900–1939 | `case_file`, `owner`, `statement`, `mark_images`, `mark_case_status` |
| `data/patents.duckdb` | 11,284 US patents in filing-system CPC classes (B42F, B42D), 1900–1939 | `patents`, `patent_classes`, `patent_inventors` |
| `data/entities.duckdb` | Canonical company registry mapping name variants across both databases | `company_entity`, `entity_name_variant` |

```python
conn = duckdb.connect("data/entities.duckdb", read_only=True)
conn.execute("ATTACH 'data/patents.duckdb'    AS pat (READ_ONLY)")
conn.execute("ATTACH 'data/trademarks.duckdb' AS tm  (READ_ONLY)")
```

See `interface.md` for the full data interface definition — the abstract tool schemas, the Markery DuckDB implementation, and portability notes for non-Markery backends.

---

## Confirmed Pairs

The specialist identifies and documents **confirmed patent-trademark pairs** recorded in `projects/<project>/matches/confirmed.jsonl`. Each entry links a specific patent to a specific trademark held by the same entity, with a note on the correspondence. Confirmed pairs are then developed into research essays (match narratives) and eventually rendered into the project site.

Confirmed pairs are curated by hand. The scoring pipeline in `src/markery/matching/` generates candidates, but a pair is confirmed only after historical review. The specialist evaluates candidates and drafts the essay.

---

## Setup

Drop this folder into a Claude project. Add the three database files (`data/trademarks.duckdb`, `data/patents.duckdb`, `data/entities.duckdb` from the Markery repository) to the project. The specialist can then run live queries against the full combined dataset.

Without the databases, the specialist works from historical knowledge and any records pasted into the conversation.

For site curation work, also add the relevant `projects/<project>/` folder so the specialist can read existing essays and confirmed.jsonl, and write new content files to the correct paths.

---

## Tool Interface

The specialist expects data in the format defined in `interface.md`. The current implementation uses Markery's DuckDB databases. Any backend that returns the same field schemas works — the historian does not depend on Markery specifically.

---

## Site Building Workflow

### 1. Research phase

Use research mode to identify and confirm patent-trademark pairs. The scoring pipeline (`markery match`) generates candidates; the historian evaluates them and writes match essays to `projects/<project>/content/<slug>.md`.

### 2. Content phase

Ask the historian to write site content for each page type:

```
Write the trademark gallery narrative for the information-systems project.
Output file: projects/information-systems/content/trademarks-narrative.md
Follow the schema in content-schemas/trademark-gallery.md.
```

Work through the content schemas in this order:
1. Match essays (already written during research phase)
2. Entity summaries (one per entity)
3. Trademark gallery narrative
4. Patent gallery narrative
5. Project landing page

### 3. Render phase

```bash
markery site build information-systems
```

The site builder reads the content files and databases, generates all HTML pages, and writes them to `projects/information-systems/site/`.

### 4. Iterate

Review the rendered site. Return to the historian for revisions, additional content, or new confirmed pairs. Re-run `markery site build` after any content change.

---

## Reference

| File | Contains |
|---|---|
| `interface.md` | Data interface definition — abstract tool schemas and Markery implementation |
| `content-schemas/trademark-gallery.md` | Schema for trademark gallery narrative |
| `content-schemas/patent-gallery.md` | Schema for patent gallery narrative |
| `content-schemas/entity-summary.md` | Schema for entity summary page |
| `content-schemas/match-narrative.md` | Schema for confirmed pair essays |
| `content-schemas/project-landing.md` | Schema for project landing page |
| `examples.md` | Example research interactions |
| `rules.md` | Behavioral rules (research + site content) |
| `reference/project-types.md` | Project type definitions, workflows, and how to choose — owned by HISTORIAN |
| `reference/historical-context.md` | Period context for 1900–1939 American commerce |
| `reference/markery-database.md` | Database schema reference |
| `reference/mark-drawing-codes.md` | USPTO drawing code reference |
| `reference/status-codes.md` | USPTO status code reference |
| `reference/image-enhancement.md` | Mark image enhancement reference |
| `research-session.md` | Runnable session checklist for match-review-essay projects |

---

## How to Use

```
"What patents did Wilson Jones hold in B42F between 1925 and 1930,
 and which of their trademarks filed in that window are likely product-name marks?"

"Walk me through the candidate pairs for VI-DEX (serial 71235764) —
 which patent is the strongest match and why?"

"Write the entity summary for Wilson Jones.
 Output: projects/information-systems/content/entity-wilson-jones.md"

"Write the trademark gallery narrative for the information-systems project.
 Output: projects/information-systems/content/trademarks-narrative.md"

"Draft a research essay for the confirmed pair VI-DEX ↔ US1630977A.
 Output: projects/information-systems/content/vi-dex.md"
```
