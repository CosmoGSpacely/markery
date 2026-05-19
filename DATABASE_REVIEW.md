# Database Review — All Three Databases

Design analysis of the trademarks, patents, and entities databases. Covers what is wrong with each, what the clean design should be, and what needs to change in code.

The organising principle for all three analyses is the same: **Markery is scope-neutral. Projects define scope.** Date windows, CPC class sets, entity rosters, seed records — all of these belong in project configuration. The database layer provides mechanisms; it does not bake in any project's choices.

---

## trademarks.duckdb

Design analysis of the current trademark database schema.

---

## Current State

### What exists

```
# Bulk tables — from USPTO CSV, serial_no BIGINT
case_file            25,473 rows   (filtering applied at build time)
owner                38,349 rows
statement            35,077 rows
classification       25,497 rows
intl_class           28,119 rows
us_class             26,188 rows
design_search        18,790 rows
owner_name_change     8,600 rows
prior_mark           11,329 rows

# Enrichment tables — from TSDR API, serial_no VARCHAR
mark_images            105 rows    (image blobs, fetched individually)
mark_case_status        18 rows    (TSDR status for bulk-dataset marks)
extended_marks           0 rows    (TSDR records for post-1939 marks)

# Ghost tables — empty, created speculatively
events                   0 rows
foreign_app              0 rows
```

---

## Problems

### 1. Project scope baked into the build

`build.py` has module-level constants:

```python
DATE_START = "1900-01-01"
DATE_END   = "1939-12-31"
```

These are defaults in the `build()` function and in the CLI. They are not Markery's values — they are one project's values. A different project (golf technology patents, pharmaceutical trademarks, 1970s consumer goods) would need a different window. The build defaults should not exist. The user specifies scope at build time; Markery provides the mechanism.

The same applies to any mark-type filtering (by `mark_draw_cd` or similar): that is project scope, not tool scope.

### 2. Two nearly-identical tables for TSDR-fetched data

`mark_case_status` and `extended_marks` have almost identical schemas:

| Column | mark_case_status | extended_marks |
|---|---|---|
| serial_no | ✓ | ✓ |
| mark_text | ✓ | ✓ |
| filing_dt | ✓ | ✓ |
| registration_no | ✓ | ✓ |
| registration_dt | ✓ | ✓ |
| status_cd | ✓ | ✓ |
| goods_desc | ✓ | ✓ |
| intl_class | ✓ | ✓ |
| **owner_name** | — | ✓ |
| first_use_dt | ✓ | ✓ |
| first_use_comm_dt | ✓ | ✓ |
| raw_json | ✓ | ✓ |
| fetched_dt | ✓ | ✓ |

The design intent was: `mark_case_status` enriches marks already in `case_file`; `extended_marks` is the primary record for marks outside the bulk dataset. But this distinction is invisible to a reviewer and adds a query fork everywhere goods descriptions are needed (`get_goods_desc` checks both tables). One table of TSDR-fetched records is correct.

### 3. Empty ghost tables created speculatively

`events` and `foreign_app` are in `_ENRICHMENT_DDL` and therefore created every time `open_db()` is called — even though neither has ever been loaded. Their triggers in DEFERRED.md had not fired when they were added. A reviewer inspecting the schema sees two empty tables with no data and no immediate purpose.

### 4. `serial_no` type inconsistency

Bulk tables use `BIGINT` (as delivered by the raw CSV). Enrichment tables use `VARCHAR` (as delivered by the TSDR API). Queries that join across the boundary must cast: `CAST(cf.serial_no AS VARCHAR)`. This is a known quirk of the USPTO source data — the serial number is numeric in the bulk dataset and string-formatted in the API. It is not a design error but it must be documented and handled consistently.

---

## Recommendation

### Core principle: Markery is scope-neutral

The database is a tool. The project defines scope. Date windows, mark type filters, CPC class sets, entity rosters — all of these belong to the project configuration, not to Markery's defaults. The build command accepts whatever scope the user provides; it does not assume any particular window.

### R1: Remove date defaults from `build.py`

```python
# Remove:
DATE_START = "1900-01-01"
DATE_END   = "1939-12-31"

# build() signature becomes:
def build(csv_dir=None, db_path=None, date_start=None, date_end=None) -> dict[str, int]:
    # Apply date filter only when arguments are supplied
    conditions = []
    if date_start:
        conditions.append(f"filing_dt >= '{date_start}'")
    if date_end:
        conditions.append(f"filing_dt <= '{date_end}'")
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
```

The CLI `--date-start` and `--date-end` flags remain but carry no default. A build with no date arguments loads the full dataset. The user chooses their scope.

**Practical note:** The full 2011 USPTO bulk dataset contains approximately five million case files. Projects that need a manageable development database supply their own window at build time. Markery does not prescribe what that window should be.

### R2: Merge `mark_case_status` into `extended_marks`

One table for all TSDR-fetched records. The rule is simple: any mark fetched from the TSDR API is stored in `extended_marks`, regardless of whether it already appears in `case_file`. For marks that are in the bulk dataset, `owner_name` is NULL (ownership comes from the `owner` table). For marks fetched as standalone records, `owner_name` is populated.

```sql
-- Final extended_marks schema (unchanged from current)
CREATE TABLE IF NOT EXISTS extended_marks (
    serial_no         VARCHAR PRIMARY KEY,
    mark_text         VARCHAR,
    filing_dt         DATE,
    registration_no   VARCHAR,
    registration_dt   DATE,
    status_cd         VARCHAR,
    goods_desc        VARCHAR,
    intl_class        VARCHAR,
    owner_name        VARCHAR,   -- NULL for bulk-enrichment rows; populated for standalone fetches
    first_use_dt      VARCHAR,
    first_use_comm_dt VARCHAR,
    raw_json          VARCHAR,
    fetched_dt        DATE
);
```

`mark_case_status` is removed from `_ENRICHMENT_DDL`. Existing rows (18) are migrated to `extended_marks` with `owner_name = NULL`. `enrich.py` writes to `extended_marks`. `get_goods_desc()` checks `extended_marks` instead of `mark_case_status`.

### R3: Remove `events` and `foreign_app` from `_ENRICHMENT_DDL`

These tables are not created until explicitly loaded via `load_events()` or `load_foreign_app()`. They do not belong in the baseline schema. The `_ENRICHMENT_DDL` constant defines what `open_db()` guarantees exists; it should not promise tables that have no data and no trigger.

The load functions remain intact — calling `load_events(csv_dir)` creates the table and populates it. But the table does not appear in the schema until that call is made.

### R4: Document the `serial_no` type split

Add a comment to `build.py` and `queries.py`:

```python
# serial_no is BIGINT in bulk tables (as delivered by the USPTO CSV source)
# and VARCHAR in extended_marks and mark_images (as returned by the TSDR API).
# Queries joining across the two must cast: CAST(cf.serial_no AS VARCHAR).
```

This is not fixable without a full rebuild of the bulk tables and has no practical cost beyond awareness.

---

## Resulting schema (after changes)

```
# Bulk tables — from USPTO CSV, no Markery-imposed scope
case_file            owner-defined rows   (full dataset or user-scoped window)
owner
statement
classification
intl_class
us_class
design_search
owner_name_change
prior_mark

# Enrichment tables — from TSDR API, created by open_db()
mark_images                              (image blobs)
extended_marks                           (all TSDR-fetched mark records, any date)

# On-demand tables — created only when explicitly loaded
events                                   (created by load_events())
foreign_app                              (created by load_foreign_app())
```

A reviewer sees: bulk source data, TSDR-enriched records, and images. The schema maps directly to the two data sources (USPTO CSV and TSDR API). No ghost tables, no project assumptions.

---

## Migration plan

| Step | Change | Files affected |
|---|---|---|
| M1 | Remove `DATE_START`, `DATE_END` constants and defaults | `trademark/build.py`, `trademark/cli.py` |
| M2 | Drop `mark_case_status` from `_ENRICHMENT_DDL`; migrate 18 rows to `extended_marks` | `trademark/build.py` |
| M3 | Update `enrich.py` to write to `extended_marks` instead of `mark_case_status` | `trademark/enrich.py` |
| M4 | Update `get_goods_desc()` to query `extended_marks` instead of `mark_case_status` | `trademark/queries.py` |
| M5 | Remove `events` and `foreign_app` from `_ENRICHMENT_DDL` | `trademark/build.py` |
| M6 | Add `serial_no` type-split comment to build and queries | `trademark/build.py`, `trademark/queries.py` |
| M7 | Update tests that reference `mark_case_status` | `tests/specialist/trademark/` |

M2–M4 are the most impactful: they eliminate the dual-table confusion and reduce the query surface. M1 eliminates the project-scope leak. M5 removes ghost tables. M6–M7 are documentation and cleanup.

---

## What does not change

The bulk table names (`case_file`, `owner`, `statement`) are retained. These are the USPTO's own terminology and are familiar to trademark practitioners and researchers. Renaming them would add friction without adding clarity.

The `mark_images` table is correct as-is: image blobs are a distinct concern from status/goods data and belong in their own table.

The `extended_marks` name is retained. It accurately describes its role: marks that extend the dataset beyond what the bulk CSV provides, whether temporally (post-1939) or in data richness (live TSDR status for bulk marks).

---

## patents.duckdb

### Current state

```
patents            11,284 rows   patent_no, title, app_dt, grant_dt, abstract,
                                 assignee_name, assignee_city, assignee_state
patent_classes     25,205 rows   patent_no, cpc_class, cpc_full
patent_inventors   11,442 rows   patent_no, inventor_name
patent_figures         31 rows   patent_no, figure_no, figure_data (BLOB), fetched_dt
fetch_log              17 rows   cpc_class, year_start, year_end, fetch_dt, patents_added
```

### Problems

**1. Project scope in module-level constants.**

`patent/build.py` opens with:

```python
START_YEAR = 1900
END_YEAR   = 1939

CPC_CLASSES: dict[str, str] = {
    "B42F": "Filing appliances, card-index systems, loose-leaf binders",
    "B42D": "Books, printed matter, forms, index cards, ledger sheets",
    "B41J": "Typewriters, selective printing mechanisms",
    "B41L": "Addressing and duplicating machines for office use",
    "G06C": "Mechanical calculators, tabulating machines",
    "G06K": "Punched cards, record carriers, recognition of data",
    "G09F": "Displaying, advertising, visible record systems, signs",
}
```

These are not Markery's values. They are one project's values — the information-systems project, which studies early twentieth-century office equipment. A golf technology project would need entirely different CPC classes (A63B, A63F) and a different year window. A pharmaceutical project would need yet another set. Neither the year range nor the class list belongs in the tool's source code.

**2. Seed patents are project data baked into the code.**

`build.py` contains `SEED_PATENTS`: two specific Remington Typewriter patents (US1261167A and US1435663A — the Soundex phonetic indexing patents) with manually-written abstracts. The `build()` function inserts these on every run. These are information-systems-project records. They have no meaning to any other project, and their hardcoded presence means the database is never truly empty — it always starts from one project's baseline.

**3. `fetch_log` is operational metadata in the research database.**

`fetch_log` records which CPC class / year-window combinations have been fetched from EPO, when, and how many patents were added. Its purpose is to enable `--resume` on interrupted builds. Two problems:

First, it encodes project scope: the rows in `fetch_log` record `cpc_class` and `year_start/year_end`, which means the log itself is a record of which project-specific CPC classes and date windows have been worked. If two projects share `patents.duckdb`, the first project's fetch log would cause `--resume` to skip windows the second project also needs.

Second, it is process state, not research data. A practitioner reviewing `patents.duckdb` does not need to know when the B42F 1905–1909 window was fetched. That information belongs in a build log, a `pipeline_state.json`, or a plain text file next to the database — not in the database schema itself.

### Recommendation

**R1: Remove `START_YEAR`, `END_YEAR`, and `CPC_CLASSES` from `build.py`.**

Year range and CPC class selection are required arguments supplied by the user at build time. No defaults. A project that needs B42F patents from 1900–1939 passes those arguments. A project that needs A63B patents from 1960–1990 passes those instead.

**R2: Move `SEED_PATENTS` out of `build.py`.**

Seed records are project data. They belong in a project-managed file (`projects/information-systems/seed_patents.json` or similar) loaded explicitly, not compiled into the tool. The `build()` command accepts an optional seed file path; if none is supplied, the database starts empty.

**R3: Remove `fetch_log` from the database schema.**

Resume state belongs in the build process, not the research database. Options:
- A plain JSON file written alongside the database (`patents_fetch_log.json`)
- An entry in `pipeline_state.json` at the project level
- Accept that a resumed build re-queries EPO for windows already done (EPO OPS rate limits are the practical constraint, not schema overhead)

The simplest clean design: write a `fetch_log.json` next to `patents.duckdb` during a build. The `--resume` flag reads that file. The research database contains only research data.

### Resulting schema (after changes)

```
patents          core bibliographic record
patent_classes   CPC classification (populated at fetch time)
patent_inventors inventor names
patent_figures   drawing images (BLOB, populated by fetch_abstract/figures)
```

Four tables. All research data, no process state. No project assumptions.

---

## entities.duckdb

### Current state

```
company_entity          5 rows    entity_id, canonical_name, entity_type, industry, notes
entity_name_variant    32 rows    variant_id, entity_id, variant_name, source
```

### Problems

**1. The entire database is one project's data baked into the tool's source code.**

`matchmaker/entities.py` contains `ENTITIES` and `VARIANTS` as Python literals: five companies (Remington Rand, Wilson Jones, Yawman & Erbe, Boorum & Pease, Library Bureau) with 32 name variants. The `build()` function inserts these as seed data on every run. Every one of these records is information-systems-project content. There is no Markery-neutral entity. The database always starts from one project's roster.

Adding entities for a second project (golf technology manufacturers, pharmaceutical companies, or any other subject) requires editing `matchmaker/entities.py` and re-running `markery matchmaker build`. This conflates the tool's build command with project data management. The source code becomes a versioned list of research notes.

**2. The `notes` field carries project narrative.**

The `notes` column on `company_entity` currently contains entries like:

> "Founded by Melvil Dewey in 1876 as a supply arm of the American Library Association; incorporated as Library Bureau in the 1880s. Holds the earliest B42F patent in the database (US664573A, 'File.', filed October 1896) — the progenitor filing-appliance entity."

This is historical research content about a specific entity in a specific project. It is not entity metadata in any general sense. It will be wrong, incomplete, or irrelevant for any other project and for Library Bureau itself in a different research context. Storing it in a database column rather than in project content files means it cannot be versioned, edited, or extended by the historian without touching the database.

**3. The schema itself is correct.**

`company_entity` and `entity_name_variant` are the right tables with the right structure. A canonical identity layer that maps variant names (as they appear in patent assignee fields and trademark owner fields) to unified entities is exactly what Markery needs. The `source` column (`patent_assignee` / `trademark_owner`) is the right way to distinguish which corpus a variant comes from. The design is sound; the data populating it is project-specific and should not live in the code.

### Recommendation

**R1: Move entity data out of `matchmaker/entities.py` into a per-project data file.**

Each project defines its own entities in a file it owns. The simplest format:

```
projects/information-systems/entities.csv
```

With columns: `entity_id, canonical_name, entity_type, industry` and a companion `variants.csv` with `entity_id, variant_name, source`. The `build` command reads from these files, not from Python literals. The `ENTITIES` and `VARIANTS` constants are removed from the source code.

This makes the entity registry a project artifact rather than a tool artifact. Adding entities for a new project means editing that project's CSV files, not the tool's source code.

**R2: Remove `notes` from `company_entity`, or make it a short identifier field.**

If a brief human-readable label is needed (entity type, founding year), that is appropriate in the schema. Long-form historical notes belong in the project's content directory — an `entity-remington-rand.md` file is the right place for the Melvil Dewey origin story, not a VARCHAR column. The historian already writes these files; they should be the canonical source.

**R3: The global singleton design is acceptable.**

One `entities.duckdb` shared across projects is the right design. Projects scope their queries via `entities.txt` (which selects entity_ids) at query time. This is already implemented correctly in `matchmaker/link.py` and `publisher/queries.py`. The issue is not the database architecture but the data populating it.

### Resulting schema (after changes)

```
company_entity          entity_id, canonical_name, entity_type
entity_name_variant     variant_id, entity_id, variant_name, source
```

Two tables, same as today. The difference is that every row comes from a project data file, not from the tool's source code. A fresh Markery installation has an empty entity registry. Projects populate it.

---

## Cross-cutting observations

**All three databases embed project scope at the wrong layer.** The pattern is consistent: date windows, CPC class sets, entity rosters, and seed records are compiled into tool source code or applied as build-time defaults. The consequence is that the databases are not reusable across projects without code changes.

**The fix is the same in all three cases.** Markery provides the schema and the build commands. Projects provide the parameters. Nothing that is specific to one project's research question should appear in `build.py`, in module-level constants, or in hardcoded seed data.

**The entity registry is the most acute case** because its current data is not just project-scoped but narrative — it contains research conclusions embedded in a database column. That content belongs in the content directory, managed by the historian, not in the schema.

**`fetch_log` is the most operationally damaging** because it actively interferes with multi-project use: two projects sharing `patents.duckdb` would corrupt each other's resume state.

## Consolidated migration table

| ID | Database | Change | Impact |
|---|---|---|---|
| M1 | trademarks | Remove `DATE_START`/`DATE_END` defaults from `build.py` | CLI args become required or date filter is omitted |
| M2 | trademarks | Merge `mark_case_status` → `extended_marks`; update `enrich.py` and `get_goods_desc` | Eliminates dual-table query fork |
| M3 | trademarks | Remove `events`/`foreign_app` from `_ENRICHMENT_DDL` | Created by load functions only |
| M4 | patents | Remove `START_YEAR`/`END_YEAR`/`CPC_CLASSES` constants | Year range and classes become caller-supplied |
| M5 | patents | Move `SEED_PATENTS` to project data file | `build()` accepts optional seed path |
| M6 | patents | Remove `fetch_log` from DDL; write build log as JSON alongside the DB | Research DB contains only research data |
| M7 | entities | Move `ENTITIES`/`VARIANTS` to per-project CSV files | `build()` reads from project data, not source code |
| M8 | entities | Remove or narrow `notes` column | Long-form content moves to project content directory |
