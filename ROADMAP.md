# Markery Roadmap

Active and upcoming tool development. Items originate in `DEFERRED.md` and are promoted here when active. Completed phases are in `archive/`.

---

## Phase 8 — Specialist Completeness

**Goal:** All five specialists have accurate, complete personas. Key operations are covered by instruction cards. Reference material reflects the current schema. Deferred functional gap D007 (patent bulk CSV) has a clear implementation path.

The persona stubs created in this session (D009) are the starting point. The historian persona (D008) has stale content from the Phase 7 schema migration and must be fixed before the historian is used in a Claude project.

---

### P1 — Fix historian persona stale content *(D008)*

The historian persona was written before Phase 7 and contains three classes of stale content:

1. **Table names**: `README.md` and `reference/markery-database.md` reference `mark_case_status`, which was removed in Phase 7 and replaced by `extended_marks`.
2. **Hardcoded project row counts**: `README.md` lists `25,473 USPTO trademark filings, 1900–1939` and `11,284 US patents in filing-system CPC classes (B42F, B42D)` — information-systems-project values, not tool values.
3. **Old code path**: `README.md` references `src/markery/matching/` which no longer exists; the matchmaker lives at `src/markery/specialist/matchmaker/`.

**Deliverables:** Updated `historian/persona/README.md`, updated `historian/persona/reference/markery-database.md`. No other files should need changes.

**Closes:** D008

---

### P2 — Flesh out patent specialist persona *(D009 partial)*

Current stubs: `README.md`, `identity.md`, `instructions/build.md`, `reference/epo-ops.md`.

**New instruction cards:**
- `instructions/pull.md` — on-demand single patent fetch; when to use vs bulk build; citation chain as a discovery path
- `instructions/figures.md` — fetching and storing drawing figures; when the historian needs them; what to do when no figure is available
- `instructions/citations.md` — backward citation chain expansion; how it grows the corpus organically from confirmed pairs

**New reference docs:**
- `reference/cpc-classes.md` — CPC class system overview; how to identify the right classes for a research subject; how to read class codes; why pre-1940 assignments were retroactive

---

### P3 — Flesh out trademark specialist persona *(D009 partial)*

Current stubs: `README.md`, `identity.md`, `instructions/build.md`, `instructions/enrich.md`, `reference/bulk-tables.md`.

**New instruction cards:**
- `instructions/entity-forward.md` — surfacing post-1939 extended marks for a named entity; how to use `markery trademark entity-forward`; when this matters for research
- `instructions/load-supplemental.md` — loading the on-demand tables (`events`, `foreign_app`) from CSV; when prosecution history or Madrid Protocol data is needed

**Reference expansion:**
- Expand `reference/bulk-tables.md` to cover the `serial_no` type split (BIGINT vs VARCHAR) and the cross-layer cast pattern in more detail, with example queries

---

### P4 — Flesh out matchmaker specialist persona *(D009 partial)*

Current stubs: `README.md`, `identity.md`, `instructions/generate.md`, `reference/scoring.md`.

**New instruction cards:**
- `instructions/entities.md` — adding a new entity to the registry; editing `entities.csv` and `variants.csv`; how source values (`patent_assignee`, `trademark_owner`) affect matching; idempotent build

**New reference docs:**
- `reference/uncertainty-band.md` — what the 0.40–0.60 uncertainty band means; how signal enrichment narrows it; when to fetch abstracts vs goods descriptions; when to escalate to historian review
- `reference/entities-schema.md` — full CSV format for `entities.csv` and `variants.csv`; column definitions; how `source` values map to database fields; example rows

---

### P5 — Flesh out publisher specialist persona *(D009 partial)*

Current stubs: `README.md`, `identity.md`, `instructions/build-site.md`, `reference/content-pipeline.md`.

**New instruction cards:**
- `instructions/enhance.md` — mark image enhancement workflow; when to enhance vs use raw TSDR images; batch vs single-mark enhancement; where enhanced images are stored and how the site builder picks them up
- `instructions/wikipedia.md` — Wikipedia drafting workflow; what content qualifies; neutral point of view requirements; how to use `markery wikipedia draft`; review before submission

**Reference expansion:**
- Expand `reference/content-pipeline.md` to cover the figure resolution fallback chain (DB BLOB → on-disk PNG → placeholder) and how to diagnose missing figures

---

### P6 — Patent bulk CSV route: research and design *(D007)*

The SETUP.md stub documents the intended behavior but no implementation exists. This action produces a design, not working code.

**Deliverables:**
1. Identify the most practical bulk patent data source for Markery's use case: PatentsView (tab-separated, annual releases), Google Patents Public Data (BigQuery, requires export), USPTO bulk data (XML, complex parsing). Evaluate schema fit against `patents.duckdb` tables.
2. Write `src/markery/specialist/patent/BULK_CSV.md` documenting the chosen source, download process, schema mapping, and the planned `markery patent bulk-import` command signature.
3. Add a DEFERRED entry for the implementation once the design is settled.

**Closes:** D007 (design phase); implementation remains deferred until design is approved.

---

**Phase gate:** Historian persona is current with Phase 7 schema. Each of the four new specialist personas has at least three instruction cards and two reference documents. Patent bulk CSV route has a written design. D007, D008, and D009 closed.
