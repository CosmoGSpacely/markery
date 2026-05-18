# Markery Architecture Review

Design record for the specialist-pattern refactor of `src/markery/` and `tools/`. Captures decisions, analyses, and open questions. Implementation begins with the PATENT specialist once open questions are resolved.

---

## Design Goal

Reorganize `src/markery/` and `tools/` into a **specialist-pattern** architecture: Python module/package boundaries organized by data source ownership and functional responsibility. The pattern is chosen to be future-compatible with a model-agnostic AI agent layer, where each specialist eventually exposes a clean programmatic interface callable by a local or hosted model without going through the CLI.

Constraints:
- `data/*.duckdb` files stay in `data/`
- Root-level documents (ROADMAP, STATUS, DEFERRED, CONTEXT, RESEARCH, README) stay at root
- `projects/` stays as the work input/output tree
- No functionality removed — this is a structural refactor, not a rewrite

---

## Specialist Inventory

Five specialists. Each owns a data source and all functionality that reads from or writes to it. Documentation about each specialist lives inside its own folder.

### PATENT
**Owns:** `data/patents.duckdb`

**Absorbs from current codebase:**
- `src/markery/db/build_patents_db.py` — EPO OPS bulk fetch and DB population (543 lines; decomposed on migration — see below)
- `src/markery/db/test_epo_credentials.py` — credential verification
- `tools/patent_docs/fetch.py` — patent figure fetching via EPO OPS images endpoint
- `tools/patent_docs/signals.py` — text signal extraction from patent titles and abstracts
- `tools/patent_docs/migrate.py` — DB migration utilities
- `tools/patent_docs/cli.py`, `__main__.py` — entry points

---

### TRADEMARK
**Owns:** `data/trademarks.duckdb`

**Absorbs from current codebase:**
- `src/markery/db/build_trademarks_db.py` — USPTO bulk CSV import
- `src/markery/db/tsdr_client.py` — TSDR case status and mark image fetch
- `tools/image_enhancement/` — Real-ESRGAN 4× upscale and SVG vectorization (as optional utility module; see analysis)

---

### MATCHMAKER
**Owns:** `data/entities.duckdb`

**Absorbs from current codebase:**
- `src/markery/db/build_entities_db.py` — entity and name-variant population
- `src/markery/matchmaker/link.py` — cross-database candidate generation via ATTACH
- `src/markery/matchmaker/score.py` — patent-trademark scoring model
- `src/markery/matchmaker/cli.py`, `__main__.py` — entry points
- `src/markery/review.py` — interactive candidate review (logically owned by MATCHMAKER since it operates on candidates)

---

### HISTORIAN
**Owns:** no database — reads confirmed pairs and entity context from `projects/`

**Absorbs from current codebase:**
- `tools/historian/identity.md`, `rules.md`, `interface.md`, `examples.md`
- `tools/historian/content-schemas/`
- `tools/historian/reference/`

---

### PUBLISHER *(new)*
**Owns:** `projects/{name}/site/` — the rendered HTML output tree

**Absorbs from current codebase:**
- `tools/site_builder/queries.py` — cross-database queries for site data
- `tools/site_builder/render.py` — HTML page generators

**Rationale:** The site builder reads from all three databases and the historian's content output. Making it a fifth specialist gives it a clear owner, a clean CLI entry point (`markery site build <project>`), and a home for documentation about the site schema. It does not own a database but does own the output artifact, which is analogous.

---

## Proposed Directory Structure

```
src/markery/
├── __init__.py
├── cli.py                              # Unified CLI entry point
├── status.py                           # Cross-cutting DB health reporting
├── common/
│   ├── __init__.py
│   ├── config.py                       # DB paths, project root, directory layout contract
│   └── auth.py                         # .env loading, EPO OAuth2 token, USPTO key
└── specialist/
    ├── patent/
    │   ├── __init__.py                 # Standard interface exports only
    │   ├── README.md                   # What PATENT owns; CLI commands; credentials
    │   ├── schema.md                   # patents.duckdb tables, columns, BLOB layout
    │   ├── reference/
    │   │   ├── epo-ops-api.md          # CQL syntax, auth, rate limits, endpoints
    │   │   ├── cpc-classes.md          # CPC class descriptions for B42F, B42D, etc.
    │   │   └── patent-number-formats.md  # epodoc vs docdb, US number stripping rules
    │   ├── epo_client.py               # EPOClient class — OAuth2, search, image fetch
    │   ├── build.py                    # DB schema DDL and population loop
    │   ├── figures.py                  # TIFF→PNG conversion and BLOB storage
    │   ├── signals.py                  # Text signal extraction (title/abstract overlap)
    │   └── cli.py                      # markery patent {build,fetch,figures,verify-credentials}
    ├── trademark/
    │   ├── __init__.py
    │   ├── README.md
    │   ├── schema.md
    │   ├── reference/
    │   │   ├── tsdr-api.md             # TSDR endpoints, rate limits, response format
    │   │   ├── mark-drawing-codes.md   # ← tools/historian/reference/mark-drawing-codes.md
    │   │   ├── status-codes.md         # ← tools/historian/reference/status-codes.md
    │   │   └── us-trademark-classes.md # US class 037, intl class 016, etc.
    │   ├── build.py                    # USPTO bulk CSV import
    │   ├── tsdr_client.py              # TSDRClient class — case status, mark images
    │   ├── enhance.py                  # Image enhancement (optional [enhance] extra)
    │   └── cli.py                      # markery trademark {build,fetch,enhance}
    ├── matching/
    │   ├── __init__.py
    │   ├── README.md
    │   ├── schema.md
    │   ├── reference/
    │   │   └── entity-resolution.md    # Name-variant strategy, how to add entities
    │   ├── entities.py                 # Entity registry build and queries
    │   ├── link.py                     # Cross-DB candidate generation via ATTACH
    │   ├── score.py                    # Scoring model
    │   ├── review.py                   # Interactive candidate review
    │   └── cli.py                      # markery match, markery review, markery entities
    ├── historian/
    │   ├── __init__.py
    │   ├── README.md
    │   ├── identity.md
    │   ├── rules.md
    │   ├── interface.md
    │   ├── examples.md
    │   ├── content-schemas/
    │   └── reference/
    │       ├── historical-context.md   # Domain history (stays with historian)
    │       └── markery-database.md     # Updated to reference each specialist's schema.md
    └── publisher/
        ├── __init__.py
        ├── README.md
        ├── schema.md                   # Site page types and their data sources
        ├── queries.py                  # Cross-DB data assembly
        ├── render.py                   # HTML page generators
        └── cli.py                      # markery site build <project>
```

**Reference doc migration note:** `tools/historian/reference/mark-drawing-codes.md` and `status-codes.md` are technical USPTO API references, not historian domain knowledge. They move to `trademark/reference/`. The historian's `reference/` retains only `historical-context.md` (domain history) and `markery-database.md` (updated to reference each specialist's `schema.md` rather than duplicating schema). `image-enhancement.md` is absorbed into `trademark/README.md`.

---

## Resolved Decisions

### Q1 — Site Builder Destination
**Decision: PUBLISHER as a fifth specialist.** It owns `projects/{name}/site/` as its output artifact. Keeping it separate from HISTORIAN preserves the distinction between interpretation (historian's job) and rendering (publisher's job). This separation matters when the historian becomes model-agnostic — the rendering layer should not change when the model does.

### Q2 — Project Directory Contract
**Decision: `common/config.py` mediates all project path resolution.** Specialists never hardcode `projects/{name}/matches/candidates.jsonl`. All path construction goes through a function in `common/config.py`. This also means changing the directory layout in the future is a one-file change.

### Q3 — Specialist Interface Standard
**Decision: Yes, define a standard interface now.** Each specialist's `__init__.py` exports a consistent set of public functions. The naming convention for the data-owning specialists:

```python
# build — populate the database from its source
def build(...) -> None: ...

# fetch — retrieve a single record by primary identifier
def fetch(id: str) -> dict: ...

# search — query the database by criteria
def search(query: str, **kwargs) -> list[dict]: ...

# list — enumerate records, optionally filtered
def list(entity_id: int | None = None, **kwargs) -> list[dict]: ...
```

HISTORIAN and PUBLISHER have different interfaces (they transform rather than store), but still export their primary entry points from `__init__.py`.

### Q4 — `status.py` Placement
**Decision: `status.py` stays at `src/markery/status.py`**, adjacent to `cli.py`. It reads from all three databases and is a diagnostic tool rather than a specialist concern. It imports read-only query functions from each specialist to gather its data, keeping the specialist boundary intact.

### Q5 — Migration Sequence
**Decision: specialist-by-specialist**, in dependency order: PATENT → TRADEMARK → MATCHMAKER → HISTORIAN → PUBLISHER → common cleanup. Each phase must leave the unified CLI functional before the next begins.

### MATCHMAKER Split
**Decision: keep MATCHMAKER as one specialist**, with entities and matching algorithm as clearly separated modules internally (`entities.py` vs `link.py` vs `score.py`). Extract into a dedicated ENTITY specialist at a future phase gate when a second research project is added that requires independent entity lifecycle management.

---

## Documentation Standard

Each specialist folder contains:

| File | Contents |
|---|---|
| `README.md` | What the specialist owns; CLI commands with example invocations; credentials required; quick-start for a new developer |
| `schema.md` | Database tables, columns, types, and relationships (for data-owning specialists); or the content schema (for HISTORIAN, PUBLISHER) |
| `__init__.py` | Standard interface exports only — no implementation code |

The historian's richer documentation set (`identity.md`, `rules.md`, `interface.md`, `examples.md`, `reference/`, `content-schemas/`) continues unchanged. That depth exists because the historian guides an AI persona; the other specialists guide Python code and don't need a persona narrative.

---

## Common Module

`markery/common/` holds only what three or more specialists actually share. Keep it small.

| Module | Contents |
|---|---|
| `config.py` | DB paths, project root, project directory layout contract (all path construction goes here) |
| `auth.py` | `.env` loading, EPO OAuth2 token fetch and refresh, USPTO API key injection |

**Not in common:**
- `safe_date()` — belongs in `trademark/tsdr_client.py`
- DuckDB connection helpers — each specialist's ATTACH pattern differs; keep local
- Logging — use stdlib `logging` directly

---

## CLI: Hybrid Approach

**Decision: unified `markery` CLI for human-driven sessions; each specialist also exposes a clean programmatic API callable without the CLI.**

Unified entry point subcommands after refactor:

```
markery patent build [--classes B42F B42D …] [--resume]
markery patent fetch <patent-no>
markery patent figures <patent-no>
markery patent verify-credentials

markery trademark build
markery trademark fetch <serial>
markery trademark enhance <serial>

markery match <project>
markery review <project>
markery entities add
markery entities list

markery site build <project> [--out DIR]

markery status
```

Programmatic interface (example):

```python
from markery.specialist.patent import build, fetch, search, list_patents
from markery.specialist.trademark import fetch_case_status, get_mark_image
from markery.specialist.matchmaker import generate_candidates, get_entities
from markery.specialist.publisher import build_site
```

---

## Analysis: `src/` Layout

The `src/` wrapper is a Python packaging convention (src-layout). Without it, running Python from the project root makes the local `markery/` directory importable directly, which means tests can accidentally import the development tree rather than the installed package. With the src-layout, `import markery` only works after `pip install -e .`.

**Decision: keep `src/`.** Specialists live at `src/markery/specialist/`.

**Current problem exposed by this refactor:** `pyproject.toml` currently sets `where = ["src", "tools"]`, making `image_enhancement`, `patent_docs`, and `site_builder` importable as top-level packages. This is the coupling that requires cli.py to do `from image_enhancement.cli import main`. The refactor eliminates this by moving all `tools/` code into specialist packages.

---

## Analysis: Image Enhancement as Specialist

**Decision: utility module within TRADEMARK, not a standalone specialist.**

The specialist pattern is organized around data source ownership. Image enhancement owns no database — it is a transformation step. It belongs in `markery/specialist/trademark/enhance.py` because mark images are its only current input.

The heavy dependencies (torch, realesrgan, vtracer, opencv) move to an optional install extra:

```toml
[project.optional-dependencies]
enhance = ["torch", "realesrgan", "opencv-python-headless", "vtracer"]
```

`pip install markery` works without torch. `pip install markery[enhance]` enables enhancement. The CLI subcommand `markery trademark enhance <serial>` gives a clear error if the extra is not installed.

**Current problem:** `pyproject.toml` lists realesrgan, vtracer, and opencv-python-headless as hard dependencies in `[project]`. This means every environment — including CI, the GitHub Actions site builder, and any future agent runner — must install GPU-oriented packages. The refactor fixes this.

---

## Full Migration Sequence

| Phase | Specialist | Preconditions | Deletes |
|---|---|---|---|
| A | PATENT | none | `src/markery/db/build_patents_db.py`, `tools/patent_docs/` |
| B | TRADEMARK | Phase A complete (pyproject.toml already fixed) | `src/markery/db/build_trademarks_db.py`, `src/markery/db/tsdr_client.py`, `tools/image_enhancement/` |
| C | MATCHMAKER | Phase B complete | `src/markery/db/build_entities_db.py`, `src/markery/matchmaker/`, `src/markery/review.py`, `src/markery/db/` (empty) |
| D | HISTORIAN | Phase C complete | `tools/historian/` |
| E | PUBLISHER | Phase D complete | `tools/site_builder/` |
| F | Common cleanup | All phases complete | `tools/` (now empty) |

Each phase ends with a commit and a full `markery status` + site build smoke test.

---

## Resolved Decisions (Q6–Q10)

### Q6 — EPO and TSDR Client Architecture
**Decision: `EPOClient` class and `TSDRClient` class, symmetric design.**

`EPOClient` holds the consumer key/secret, manages the OAuth2 token lifecycle (lazy re-auth on 401), encapsulates rate limiting and retry logic (503 backoff), and exposes `search(cql)`, `fetch_biblio(patent_no)`, and `fetch_figure(patent_no, page)` as instance methods. Credential injection via constructor makes the class testable without environment variables.

`TSDRClient` is the symmetric equivalent: holds the API key, encapsulates rate limits (60 req/min), and exposes `get_case_status(serial)`, `get_mark_image(serial)`, and `get_multiple_cases(serials)`. Same design rationale: testable, self-contained, agent-callable.

### Q7 — Figure Storage Location
**Decision: figures stored as BLOBs in `patents.duckdb`.**

31 current figures = 2.8 MB total. DuckDB BLOB storage is appropriate at this scale. Storing figures in the DB means the PATENT specialist is fully self-contained — no external file dependencies — and PUBLISHER can retrieve figures with a single query rather than resolving file paths.

**Schema change required:**

Current `patent_figures` table:
```sql
patent_no VARCHAR, figure_no INTEGER, figure_path VARCHAR, is_representative BOOLEAN
```

Target `patent_figures` table:
```sql
patent_no VARCHAR, figure_no INTEGER, figure_data BLOB, figure_format VARCHAR,
fetched_at DATE, is_representative BOOLEAN
```

`figure_path` is dropped. `figure_data` holds the PNG bytes. `figure_format` is `'PNG'` (reserved for future formats). `fetched_at` replaces the orphaned `patent_documents.pdf_fetched_at`.

**`patent_documents` table fate:** This table was designed to track PDF downloads via Google Patents — a path that is now dropped. Its columns (`pdf_path`, `pdf_fetched_at`, `page_count`, `figure_count`) are vestigial. The table is dropped in the PATENT schema migration; figure fetch metadata is carried by `figure_data` presence and `fetched_at` in `patent_figures`.

**Migration step:** A one-time migration in `specialist/patent/build.py` reads the 31 existing PNG files from `projects/information-systems/output/patent-figures/`, inserts them as BLOBs into the new schema, and confirms count. The on-disk PNG files remain (gitignored) but are no longer the source of truth.

### Q8 — Google Patents PDF Code
**Decision: clean break.** The Google Patents PDF download path is dropped entirely. No stub, no dead code. The PATENT specialist's `README.md` documents the decision explicitly: EPO OPS is the authoritative source for pre-1940 patent drawings; Google Patents blocks automated access and returns no usable content for patents in this date range. PATENT specialist is the expert on how to get patent data — that expertise lives in `reference/epo-ops-api.md`.

### Q9 — Reference Documentation Depth
**Decision: data specialists have `reference/` folders with technical API and domain reference.**

Each data-owning specialist documents the external system it depends on, so the specialist folder is the definitive reference for interacting with that source. For PATENT: EPO OPS API, CQL syntax, patent number formats, known pre-1920 limitations. For TRADEMARK: TSDR API, USPTO bulk CSV format, mark drawing codes, status codes. For MATCHMAKER: entity resolution strategy and name-variant conventions.

### Q10 — `tools/patent_docs/migrate.py`
**Decision: drop.** Confirmed: `migrate.py` only creates the `patent_documents` and `patent_figures` tables. Both tables already exist in `patents.duckdb` (verified: 31 rows in each). `patent_documents` is being dropped in the schema migration (Q7). `patent_figures` is being restructured (Q7). `migrate.py` has no further role.

---

## Resolved Decisions (Q11--Q16)

### Q11 -- EPOClient Token Lifecycle
**Decision: lazy re-auth.** `EPOClient` stores the token string and expiry timestamp internally. Every public method calls `_ensure_token()` before issuing a request. `_ensure_token()` refreshes if the token is absent or expires within 60 seconds. Callers never manage token state. This is the correct default for agent use, where the caller should not need to reason about session lifecycle.

### Q12 -- TSDRClient Scope
**Decision: drop unused methods; document as deferred in `trademark/reference/tsdr-api.md`.**

`TSDRClient` v1 exposes only the two actively-used methods:
- `get_case_status(serial: str) -> dict | None`
- `get_mark_image(serial: str) -> tuple[bytes, str] | tuple[None, None]`

The following are dropped from the initial implementation and documented with their API endpoints in `tsdr-api.md` for future use:
- `get_last_update(serial)` -- last case update timestamp
- `get_multiple_cases_status(serials)` -- bulk status (deferred to Phase 3 trademark document retrieval)
- `download_document(serial, doc_id, format)` -- prosecution document download (deferred to Phase 3)

### Q13 -- `mark_case_status` Parsed Fields
**Decision: fix during TRADEMARK migration.** The bug (parsed columns empty, `raw_json` populated) is a response-parsing error in the current `tsdr_client.py`. `TSDRClient` rewrites the parsing layer, so the fix is included in that pass. No separate bugfix commit needed.

### Q14 -- `fetch_log` and `fetched_dt` Columns
**Reviewed and confirmed: keep both.**

`fetch_log` (`cpc_class, year_start, year_end, fetch_dt, patents_added`) is the resume mechanism for `markery patent build --resume`. It records which CPC class/year windows have been fetched from EPO OPS so that re-running build skips completed windows. Without it, a re-run would re-fetch all 11,284 patents -- a ~15-minute process over rate-limited API calls. 17 rows currently, one per fetch session. This is functional infrastructure, not an audit log. It stays in the PATENT schema and is documented in `schema.md`.

`fetched_dt DATE DEFAULT CURRENT_DATE` columns on `mark_images` and `mark_case_status` in `trademarks.duckdb` are lightweight staleness markers. They cost nothing to keep and answer "when was this data last refreshed?" without a separate query. They stay. Naming is unified as `fetched_dt` across all tables (the proposed `fetched_at` on the new `patent_figures` BLOB schema uses `fetched_dt` for consistency).

`pdf_fetched_at` on `patent_documents` disappears with that table (Q7 decision).

### Q15 -- `pyproject.toml` Dependency Split
**Decision: move image enhancement to `[enhance]` optional extra in Phase A; simplify CI in the same commit.**

The CI workflow (`pages.yml`) currently installs:
```
pip install duckdb Pillow
pip install --no-deps -e .
```
The `--no-deps` flag exists because `realesrgan` is a core dependency and would fail to install in CI (no GPU, large package). This is a smell that Phase A eliminates. After moving the heavy packages to optional, CI simplifies to:
```
pip install -e .
```
The site build path (`markery site build` -> `publisher/render.py`) uses only `duckdb` and `Pillow`. No enhance code is in that path. The split is clean. `pyproject.toml` after Phase A:

```toml
[project]
dependencies = [
    "duckdb>=0.9.0",
    "requests>=2.25.0",
    "python-dotenv>=1.0.0",
    "Pillow>=10.0.0",
]

[project.optional-dependencies]
enhance = ["torch", "realesrgan", "opencv-python-headless", "vtracer"]
dev     = ["pytest>=8.0.0"]
```

### Q16 -- Historian `markery-database.md`
**Decision: keep a query-relevant summary.** The historian's `reference/markery-database.md` is rewritten as a focused view of what data is available and what the historian uses to interpret pairs -- not a full column-level schema reference. Full schema lives in each specialist's `schema.md`. The summary covers: which entities exist in `entities.duckdb`; the fields on a patent record relevant to the historian; the fields on a trademark record relevant to the historian; how confirmed pairs are structured in `confirmed.jsonl`. This is what an AI context window needs without navigating to other folders.

---

## PATENT Migration Plan (Phase A) -- Detailed

PATENT is first because it has no Python-level dependents among the other specialists. MATCHMAKER reads `patents.duckdb` directly via DuckDB ATTACH at runtime, not through Python imports, so it continues to work unchanged during and after Phase A.

### What Phase A changes

| Before | After |
|---|---|
| `src/markery/db/build_patents_db.py` (543 lines, mixed concerns) | `specialist/patent/epo_client.py` + `build.py` + `figures.py` |
| `src/markery/db/test_epo_credentials.py` | `markery patent verify-credentials` CLI subcommand |
| `tools/patent_docs/fetch.py` (EPO + broken Google Patents paths) | `specialist/patent/figures.py` (EPO path only) |
| `tools/patent_docs/signals.py` | `specialist/patent/signals.py` (straight move) |
| `tools/patent_docs/migrate.py` | dropped (tables already exist; Q10) |
| `tools/patent_docs/cli.py`, `__main__.py` | `specialist/patent/cli.py` |
| `patent_figures.figure_path VARCHAR` | `patent_figures.figure_data BLOB, figure_format VARCHAR, fetched_dt DATE` |
| `patent_documents` table | dropped |
| `pyproject.toml`: realesrgan in core deps | realesrgan in `[enhance]` optional |
| `pyproject.toml`: `where = ["src", "tools"]` | `where = ["src"]` |
| CI: `pip install --no-deps -e .` | CI: `pip install -e .` |

### Module decomposition

**`epo_client.py` -- EPOClient class**

Extracted from `build_patents_db.py` lines covering OAuth2, search, and image fetch. No DuckDB imports.

```python
class EPOClient:
    AUTH_URL   = "https://ops.epo.org/3.2/auth/accesstoken"
    SEARCH_URL = "https://ops.epo.org/3.2/rest-services/published-data/search/biblio"
    IMAGE_URL  = "https://ops.epo.org/3.2/rest-services/published-data/images"

    def __init__(self, key: str, secret: str) -> None:
        # stores key/secret; token and expiry initialized to None/epoch

    def _ensure_token(self) -> None:
        # lazy re-auth: requests new token if absent or expiring within 60s
        # sets self._token and self._token_expiry

    def search(self, cql: str, range_start: int, range_end: int) -> list[dict]:
        # GET SEARCH_URL with Range header; returns list of parsed biblio dicts
        # each dict: {patent_no, title, app_dt, grant_dt, assignee_name,
        #              assignee_city, assignee_state, cpc_classes, inventors}
        # raises on non-200 after RETRY_DELAYS backoff

    def fetch_biblio(self, patent_no: str) -> dict | None:
        # single-patent biblio fetch; returns None if not found

    def fetch_figure(self, patent_no: str, page: int = 1) -> bytes | None:
        # GET IMAGE_URL/{stripped_no}/A/FullImage, Accept: application/tiff, Range: {page}
        # returns raw TIFF bytes or None on 404
        # stripped_no: numeric portion only (epodoc format, see reference/patent-number-formats.md)
```

Retry logic (`RETRY_DELAYS = [5, 15, 30]`) stays inside `_request()` -- a private method called by all public methods. Rate sleep (`RATE_SLEEP = 0.5s`) is applied after every request in `_request()`.

**`build.py` -- schema DDL and population**

Extracted from `build_patents_db.py`. Imports `EPOClient` from `epo_client.py` and `load_epo_credentials()` from `common/auth.py`.

Schema DDL reflects the updated `patent_figures` (BLOB) and dropped `patent_documents`. The `fetch_log` table is part of the schema -- documented, not vestigial.

Population loop logic is unchanged: iterate CPC classes and year windows, check `fetch_log` for resume, batch-insert via `executemany`, append `fetch_log` row on completion.

**`figures.py` -- figure fetch and BLOB migration**

Consolidates the EPO OPS image path from `tools/patent_docs/fetch.py`. Google Patents PDF path is removed entirely (Q8).

Two public functions:

```python
def fetch_and_store(patent_no: str, client: EPOClient, conn: duckdb.DuckDBPyConnection) -> bool:
    # fetches TIFF via client.fetch_figure(), converts to PNG via Pillow,
    # upserts into patent_figures as BLOB; returns True on success

def migrate_path_figures(project: str, conn: duckdb.DuckDBPyConnection) -> int:
    # one-time migration: reads rows WHERE figure_data IS NULL AND figure_path IS NOT NULL,
    # loads PNG from disk, inserts as BLOB, nulls figure_path; returns count migrated
    # idempotent: safe to re-run
```

**`signals.py`** -- straight move from `tools/patent_docs/signals.py`. One import change: remove `ROOT = Path(__file__).parent.parent`; use `common/config.py` for DB path.

**`cli.py`** -- registers the following under `markery patent`:

| Subcommand | Action |
|---|---|
| `build [--classes B42F ...] [--resume]` | Calls `build.build()` |
| `fetch <patent-no>` | Fetches and prints single patent biblio |
| `figures <patent-no>` | Fetches and stores figure BLOB for one patent |
| `figures --all-missing` | Fetches figures for all patents with no BLOB stored |
| `verify-credentials` | Calls `EPOClient._ensure_token()`; prints token prefix and expiry |
| `signals <project>` | Runs `signals.enrich_candidates()` on project candidates |
| `migrate-figures <project>` | Calls `figures.migrate_path_figures()` |

### Database schema changes (Phase A)

```sql
-- Run once on patents.duckdb before Phase A code goes live:

ALTER TABLE patent_figures ADD COLUMN figure_data   BLOB;
ALTER TABLE patent_figures ADD COLUMN figure_format VARCHAR DEFAULT 'PNG';
ALTER TABLE patent_figures ADD COLUMN fetched_dt    DATE;

-- After migrate-figures has run and BLOB count is verified:
ALTER TABLE patent_figures DROP COLUMN figure_path;
ALTER TABLE patent_figures DROP COLUMN is_representative;  -- was never set; see Q17

DROP TABLE IF EXISTS patent_documents;
```

`is_representative BOOLEAN` has never been populated (all NULL). It was intended to flag the primary figure for a patent that has multiple. Since we fetch only page 1 (always the representative drawing), the flag is redundant. Dropped.

### Step-by-step migration sequence

1. Create `src/markery/specialist/patent/` with empty `__init__.py`
2. Write `epo_client.py` -- `EPOClient` class as specified above
3. Write `build.py` -- schema DDL (updated) + population loop; imports `EPOClient`, `load_epo_credentials`
4. Write `figures.py` -- `fetch_and_store()` + `migrate_path_figures()`; imports `EPOClient`
5. Move `signals.py` from `tools/patent_docs/`; update imports
6. Write `cli.py` -- all subcommands
7. Write `README.md` -- ownership statement, CLI reference, credential requirements, known limitations
8. Write `schema.md` -- all five tables (`patents`, `patent_classes`, `patent_inventors`, `patent_figures`, `fetch_log`) with column types, constraints, and notes on BLOB layout; state that `patent_documents` was dropped and why
9. Write `reference/epo-ops-api.md`, `reference/cpc-classes.md`, `reference/patent-number-formats.md`
10. Update `__init__.py` -- export standard interface: `build`, `fetch`, `fetch_figure`, `search`, `list_patents`
11. Update `src/markery/cli.py` -- replace `cmd_fetch_patents`, `cmd_score_signals` with routing to `specialist/patent/cli.py`; remove `from patent_docs.cli import main`
12. Run database schema migration SQL (step in `build.py` or as standalone `markery patent migrate-figures`)
13. Run `markery patent migrate-figures information-systems` -- confirm 31 BLOBs inserted
14. Update `pyproject.toml` -- `where = ["src"]`; move enhance deps to `[enhance]`; core deps clean
15. Update `pages.yml` -- replace `pip install duckdb Pillow && pip install --no-deps -e .` with `pip install -e .`
16. Delete `src/markery/db/build_patents_db.py`, `src/markery/db/test_epo_credentials.py`, `tools/patent_docs/`
17. Smoke tests:
    - `markery patent verify-credentials` -- prints token, no error
    - `markery patent build --seed-only` -- DB row count unchanged from pre-migration value
    - `markery status` -- all three DB row counts correct
    - `markery site build information-systems` -- 14 pages rendered; figures display (BLOB path); no broken images

---

## Resolved Decisions (Q17--Q21)

### Q17 -- `is_representative` Column
**Decision: drop; document as deferred in `patent/schema.md`.**

The column has never been populated (all NULL). Page-1 fetch is always the representative drawing for pre-1940 patents, so the flag adds no information in the current corpus. It is dropped in the Phase A schema migration. `schema.md` documents the intent and the deferred path: if multi-page figure fetch is added in a future phase, re-add `is_representative BOOLEAN DEFAULT FALSE` with a `markery patent figures --all-pages` flag that sets it on the first page of each patent.

### Q18 -- Testing Strategy
**Decision: add unit tests in Phase A; each specialist migration adds tests for that specialist.**

Tests live at `tests/specialist/{name}/`. Phase A deliverables include `tests/specialist/patent/test_epo_client.py` and `tests/specialist/patent/test_figures.py`. Tests mock HTTP calls (using `unittest.mock.patch`) so they run offline and in CI without credentials. The smoke-test sequence (`verify-credentials`, `build --seed-only`, `site build`) remains the integration gate; unit tests guard logic that smoke tests cannot reach (token expiry edge cases, BLOB migration idempotency, schema DDL on fresh DB).

### Q19 -- PUBLISHER Queries Coupling
**Decision: call specialist programmatic APIs; enforce the boundary whenever feasible.**

PUBLISHER's `queries.py` imports from `markery.specialist.patent`, `markery.specialist.trademark`, and `markery.specialist.matchmaker` rather than opening DuckDB files directly. This means any schema change inside a specialist must be reflected in that specialist's public API before PUBLISHER can see it -- which is the correct forcing function for keeping APIs honest. PUBLISHER becomes the integration test for all three public APIs working together.

Where a query genuinely requires a cross-specialist JOIN that cannot be expressed through individual specialist APIs without multiple round trips, PUBLISHER is permitted to attach the relevant DB files directly -- but this must be documented in a comment citing the specific query and why the API path is insufficient.

### Q20 -- CI Workflow Update Timing
**Decision: same commit as Phase A.**

Phase A already modifies `pyproject.toml` (removes `"tools"` from `where`, cleans core deps). At that point the `pip install --no-deps -e .` workaround is both unnecessary and misleading -- it implies the declared deps are untrustworthy when they are now correct. Leaving the workaround in place through Phases B--E creates a false impression that something is still broken. Same-commit is the clean call.

### Q21 -- `build_trademarks_db.py` Pre-Assessment
**Decision: read at Phase B planning time, not before Phase A.**

`build_trademarks_db.py` does not affect Phase A. A detailed Phase B plan is written after Phase A is complete, using the same decomposition analysis applied to `build_patents_db.py`. Noted.

---

## Resolved Decisions (Q22--Q27)

### Q22 -- Unit Test HTTP Mocking Library
**Decision: `responses` library; add to `[dev]` optional extra.**
`responses` registers declarative mock URLs and is cleaner than `patch` chains for multi-call HTTP sequences. Added to `pyproject.toml` as `responses>=0.25` under `[dev]`.

### Q23 -- `common/auth.py` Credential Validation
**Decision: specific loaders backed by a private `_require_env()` primitive.**
```python
def _require_env(key: str, hint: str) -> str:
    val = os.getenv(key, "").strip()
    if not val:
        raise EnvironmentError(f"{key} not set in .env -- {hint}")
    return val

def load_epo_credentials() -> tuple[str, str]:
    key    = _require_env("EPO_CONSUMER_KEY",    "register at https://developers.epo.org")
    secret = _require_env("EPO_CONSUMER_SECRET", "register at https://developers.epo.org")
    return key, secret

def load_tsdr_key() -> str:
    return _require_env("USPTO_API_KEY", "register at https://account.uspto.gov/api-manager/")
```

### Q24 -- `common/config.py` Project Path API
**Decision: `Project` dataclass.**
```python
@dataclass
class Project:
    name: str
    @property def root(self)       -> Path: ...  # projects/{name}/
    @property def candidates(self) -> Path: ...  # matches/candidates.jsonl
    @property def confirmed(self)  -> Path: ...  # matches/confirmed.jsonl
    @property def content(self)    -> Path: ...  # content/
    @property def site(self)       -> Path: ...  # site/
    @property def entities_file(self) -> Path: ...  # entities.txt
```

### Q25 -- MATCHMAKER CLI Subcommand Names
**Decision: keep `markery match` and `markery review` as human-facing subcommands.** Python package is `markery.specialist.matchmaker`; CLI names are research verbs, not package names.

### Q26 -- Phase A Commit Granularity
**Decision: multi-commit within one PR.**
Commit order: (1) schema migration SQL, (2) `common/` + `specialist/patent/` modules, (3) CLI routing + `pyproject.toml` + CI, (4) unit tests, (5) delete old files.

### Q27 -- MATCHMAKER Package Name
**Decision: `matchmaker`.** Consistent with the specialist-as-persona pattern: `historian`, `publisher`, `matchmaker`. Import path: `from markery.specialist.matchmaker import generate_candidates`.

---

## Phase B -- TRADEMARK Specialist Migration Plan

Phase A is complete as of 2026-05-18 (commits aa61059–4557811). Phase B migrates
`src/markery/db/build_trademarks_db.py` and `src/markery/db/tsdr_client.py` into
`src/markery/specialist/trademark/`, following the same specialist pattern.

### Source code analysis

**`build_trademarks_db.py`** (95 lines):
- Drops and recreates `trademarks.duckdb` from scratch — not idempotent by design.
  The CSV source does not change; a full rebuild is the correct operation.
- Loads eight tables from the 2011 USPTO Trademark Case Files Dataset CSV files
  in `csv/`: `case_file`, `owner`, `owner_name_change`, `classification`,
  `intl_class`, `us_class`, `design_search`, `prior_mark`.
- Filters to `filing_dt BETWEEN 1900-01-01 AND 1939-12-31`.
- Builds a temp `target_serials` table to JOIN companion tables against
  `case_file`'s filtered serial numbers -- efficient bulk load pattern to keep.
- No resume capability needed -- it's all-or-nothing by definition.
- Issues to fix: hardcoded `CSV_DIR` and `DB_PATH` strings; bare `print()`/`log()`
  instead of returned counts; `os.remove()` before connect instead of `IF EXISTS` +
  separate drop logic.

**`tsdr_client.py`** (168 lines):
- A module-level prototype, not a class. `API_KEY` is loaded at import time with
  a hard `sys.exit(1)` if missing -- incompatible with testing.
- No rate limiting. USPTO TSDR allows 60 req/min (1 per second).
- No retry logic for transient failures.
- `get_trademark_image()` is the only function used in the current workflow.
  `get_case_status()`, `get_last_update()`, and `get_multiple_cases_status()` are
  exploratory stubs. `download_document()` is unused.
- Needs a full rewrite as a `TSDRClient` class symmetric to `EPOClient`.

### Current `trademarks.duckdb` schema (no changes needed)

The database already has the correct shape from prior work. No schema migration
is required for Phase B.

```
Tables (current state, 2026-05-18):
  case_file          25,473 rows   -- CSV bulk load
  classification     25,497 rows   -- CSV bulk load
  design_search      18,790 rows   -- CSV bulk load
  intl_class         28,119 rows   -- CSV bulk load
  mark_case_status       13 rows   -- TSDR API enrichment
  mark_images           105 rows   -- TSDR API enrichment (BLOB)
  owner              38,349 rows   -- CSV bulk load
  owner_name_change   8,600 rows   -- CSV bulk load
  prior_mark         11,329 rows   -- CSV bulk load
  statement          35,077 rows   -- CSV bulk load
  us_class           26,188 rows   -- CSV bulk load
```

`mark_images` schema: `serial_no VARCHAR, image_data BLOB, image_format VARCHAR,
image_size INTEGER, fetched_dt DATE`

`mark_case_status` schema: `serial_no VARCHAR, mark_text VARCHAR, filing_dt DATE,
registration_no VARCHAR, registration_dt DATE, status_cd VARCHAR, goods_desc VARCHAR,
intl_class VARCHAR, first_use_dt VARCHAR, first_use_comm_dt VARCHAR, raw_json VARCHAR,
fetched_dt DATE`

Both tables use `serial_no` as `VARCHAR` (not `BIGINT` like the CSV tables).
Keep as-is — TSDR API returns serial numbers as strings.

### Two data sources, one specialist

Unlike PATENT (EPO OPS is the only source), TRADEMARK has two distinct sources:

| Source | Tables | Entry point |
|---|---|---|
| 2011 USPTO CSV dataset | case_file, owner, owner_name_change, classification, intl_class, us_class, design_search, prior_mark, statement | `build.py` |
| USPTO TSDR API | mark_images, mark_case_status | `enrich.py` via `TSDRClient` |

Both are owned by the TRADEMARK specialist. `build.py` is a one-shot bulk loader;
`enrich.py` is the ongoing enrichment path for individual marks.

### `TSDRClient` class interface

Symmetric to `EPOClient` but simpler: USPTO uses a static API key header (no
OAuth2 token lifecycle). Rate limit: 60 req/min (sleep 1.0 s after each request).

```python
class TSDRClient:
    _BASE_URL    = "https://tsdrapi.uspto.gov"
    RATE_SLEEP   = 1.0          # 60 req/min
    RETRY_DELAYS = [5, 15, 30]  # 429/503 backoff

    def __init__(self, api_key: str) -> None:
        # stores api_key; creates requests.Session with USPTO-API-KEY header

    def _get(self, url: str, **kwargs) -> requests.Response:
        # rate-limited GET with 429/503 retry; no token state

    def fetch_case_status(self, serial_no: str) -> dict | None:
        # GET /ts/cd/casestatus/sn{serial_no}/info
        # returns parsed flat dict or None on 404
        # parsed fields: mark_text, filing_dt, registration_no, registration_dt,
        #                status_cd, goods_desc, intl_class, first_use_dt,
        #                first_use_comm_dt (from JSON path)

    def fetch_mark_image(self, serial_no: str) -> bytes | None:
        # GET /ts/cd/rawImage/{serial_no}, Accept: image/png
        # returns PNG bytes or None on 404

    def token_info(self) -> dict:
        # returns {"api_key_prefix": "...", "base_url": "..."} for verify-credentials
        # no live check -- key validity only confirmed by actual requests
```

No equivalent to `_ensure_token()` -- the API key is static. Add a
`verify_credentials()` method that makes a single cheap request (e.g., known
serial number) to confirm the key is accepted.

### Target directory layout

```
src/markery/specialist/trademark/
    __init__.py          public interface exports
    tsdr_client.py       TSDRClient class
    build.py             CSV bulk loader (create/recreate trademarks.duckdb)
    enrich.py            TSDR API enrichment (mark images, case status)
    cli.py               markery trademark subcommand router
```

No `signals.py` equivalent -- signal enrichment reads trademark data but lives
in `specialist/patent/signals.py` (it reads both DBs). No change needed there.

### `build.py` public interface

```python
def build(
    csv_dir: str | Path | None = None,
    db_path: str | Path | None = None,
    date_start: str = "1900-01-01",
    date_end:   str = "1939-12-31",
) -> None:
    """Drop and recreate trademarks.duckdb from CSV source files.

    csv_dir defaults to ROOT / "csv".
    db_path defaults to DB["trademarks"].
    Prints row counts per table on completion.
    """
```

Key implementation changes from `build_trademarks_db.py`:
- Accept `csv_dir` and `db_path` as parameters (testable, not hardcoded).
- Return table row counts as a dict instead of printing inline.
- Use `conn.execute("DROP TABLE IF EXISTS ...")` before `CREATE TABLE AS SELECT`
  rather than `os.remove()` before `connect()`. This makes partial re-runs safer.
- Keep the `target_serials` temp table JOIN pattern (correct and efficient).
- Keep `PRAGMA threads=4`.

### `enrich.py` public interface

```python
def store_mark_image(
    serial_no: str,
    client: TSDRClient,
    conn: duckdb.DuckDBPyConnection,
) -> bool:
    """Fetch PNG from TSDR and upsert into mark_images. Returns True if stored."""

def store_case_status(
    serial_no: str,
    client: TSDRClient,
    conn: duckdb.DuckDBPyConnection,
) -> bool:
    """Fetch case status from TSDR and upsert into mark_case_status. Returns True if stored."""

def enrich_project(
    project: str,
    client: TSDRClient,
    conn: duckdb.DuckDBPyConnection,
    source: str = "confirmed",   # "confirmed" | "candidates"
    min_score: float = 0.0,
    force: bool = False,
) -> dict[str, int]:
    """Fetch images and status for all marks in a project. Returns {"images": n, "status": n}."""
```

Both `store_*` functions are idempotent: skip if the row already has data and
`force=False`. Both UPDATE existing rows or INSERT new ones (same pattern as
`patent/figures.py:fetch_and_store`).

### `markery trademark` CLI subcommands

| Subcommand | Action |
|---|---|
| `build` | Run CSV bulk load; requires `csv/` directory |
| `enrich <serial_no>` | Fetch image + status for one mark |
| `enrich-project [project]` | Enrich all marks in confirmed.jsonl (or candidates above min-score) |
| `verify-credentials` | Make a known-good TSDR request; confirm key is accepted |
| `status` | Print row counts for all trademark tables |

### `__init__.py` public interface

```python
from markery.specialist.trademark.build import build, open_db
from markery.specialist.trademark.tsdr_client import TSDRClient
from markery.specialist.trademark.enrich import store_mark_image, store_case_status

__all__ = ["build", "open_db", "TSDRClient", "store_mark_image", "store_case_status"]
```

### Unit tests

`tests/specialist/trademark/test_tsdr_client.py`:
- `test_fetch_mark_image_returns_bytes` — mock `GET /ts/cd/rawImage/{sn}` → PNG bytes
- `test_fetch_mark_image_returns_none_on_404`
- `test_fetch_case_status_parses_response` — mock status JSON → check parsed fields
- `test_fetch_case_status_returns_none_on_404`
- `test_rate_sleep_applied` — monkeypatch `time.sleep`; confirm called after each request

`tests/specialist/trademark/test_enrich.py`:
- `test_store_mark_image_inserts_new` — in-memory DB; confirm BLOB stored
- `test_store_mark_image_skips_if_already_stored`
- `test_store_mark_image_updates_existing_row_without_data`
- `test_store_case_status_inserts_new`
- `test_store_case_status_is_idempotent`

No `test_build.py` — the CSV bulk loader depends on 2 GB CSV files not in the
repo. Test coverage for build logic is provided by smoke-test only.

### Image enhancement (deferred)

`tools/image_enhancement/` is still wired to `markery enhance`. It is not moved
in Phase B. The `[enhance]` optional extra in `pyproject.toml` already declares
the correct deps (opencv, realesrgan, vtracer). Migration to `specialist/` or a
standalone `enhance` specialist is deferred until PUBLISHER is planned.

### `markery enhance` CLI dependency on `tools/`

The `markery enhance` subcommand still imports `from image_enhancement.cli import main`.
The `tools/` directory is still needed for this path. It cannot be removed until
`image_enhancement/` is migrated. This is the one remaining `tools/` dependency
after Phase B completes.

### Files to delete after Phase B

```
src/markery/db/build_trademarks_db.py
src/markery/db/tsdr_client.py
```

`src/markery/db/` becomes empty after Phase B. The directory itself is removed
when Phase C (MATCHMAKER) migrates `src/markery/matching/` and
`src/markery/db/build_entities_db.py`.

### Step-by-step migration sequence

1. Create `src/markery/specialist/trademark/` with empty `__init__.py`
2. Write `tsdr_client.py` -- `TSDRClient` class as specified above
3. Write `build.py` -- CSV bulk loader; imports `load_tsdr_key` (unused in build
   but needed to confirm auth is not accidentally required for bulk load)
4. Write `enrich.py` -- `store_mark_image()`, `store_case_status()`,
   `enrich_project()`; imports `TSDRClient`
5. Write `cli.py` -- all `markery trademark` subcommands
6. Write `__init__.py` -- public interface exports
7. Update `src/markery/cli.py` -- add `"trademark": lambda: cmd_trademark(rest)`
8. Write unit tests in `tests/specialist/trademark/`
9. Smoke tests:
   - `markery trademark verify-credentials` -- key accepted, no error
   - `markery trademark status` -- row counts match current `markery status` output
   - `markery trademark enrich-project information-systems` -- skips all (already enriched)
   - `markery status` -- all three DB row counts unchanged
10. Delete `src/markery/db/build_trademarks_db.py` and `src/markery/db/tsdr_client.py`
11. Multi-commit: (1) new `specialist/trademark/` code, (2) CLI routing,
    (3) unit tests, (4) delete old files

### Deferred items (documented here for Phase B reference)

These were identified during Phase A planning and remain deferred:

- **`fetched_dt` staleness refresh**: `mark_images` and `mark_case_status` rows
  older than a configurable threshold could be refreshed with a
  `markery trademark refresh-stale [--days N]` subcommand. Not needed until the
  corpus grows significantly or marks change status.
- **TSDR bulk status endpoint**: `get_multiple_cases_status()` (up to N serial
  numbers in one call) was explored in `tsdr_client.py` but not used. Deferred
  until `enrich-project` proves too slow for larger corpora.
- **Mark image enhancement**: `tools/image_enhancement/` pipeline (upscale,
  binarize, vectorize) could be wired to `markery trademark enrich` as an
  optional post-process step. Deferred to PUBLISHER or a dedicated enhance phase.

---

## Phase C -- MATCHMAKER Specialist Migration Plan

Phase B is complete as of 2026-05-18 (commits 2377c22–a48a6a5). Phase C migrates
`src/markery/matching/` and the remaining `src/markery/db/` files into
`src/markery/specialist/matchmaker/`, following the specialist pattern.
After Phase C, `src/markery/db/` and `src/markery/matching/` are fully deleted.

### Source code analysis

**`matching/score.py`** (49 lines):
- Pure scoring functions: `date_score`, `class_score`, `total_score`. No I/O.
- No imports to update. Straight move to `specialist/matchmaker/score.py`.
- Currently tested by `tests/test_score.py` (6 tests, all passing).
  That file imports `from markery.matching.score import ...` — must be updated.

**`matching/link.py`** (168 lines):
- Core candidate generation: `generate_candidates`, `patents_for_entity`,
  `trademarks_for_entity`, `cpc_for_patents`, `write_candidates`, `read_confirmed`,
  `entity_ids_for_project`.
- Hardcoded module-level path strings (`ENTITIES_DB = "data/entities.duckdb"`,
  `PATENTS_DB`, `TRADEMARKS_DB`). Replace with `common/config.py` DB dict.
- Uses DuckDB ATTACH to join entities, patents, and trademarks in one connection
  (documented approach per Q19). The comment on `_connect()` should explicitly
  note the cross-specialist ATTACH as the intended pattern.
- `entity_ids_for_project()` reads a plain-text file — no DB dependency. Testable
  without a database fixture.

**`matching/cli.py`** (112 lines):
- Entry point for `markery match`. Handles project/all/entity/list-entities modes.
- Hardcoded `ENTITIES_DB = "data/entities.duckdb"` for `list_entities()`.
- Imports from `.link` (relative) — update to `markery.specialist.matchmaker.link`.
- The argument structure is clean and does not need to change.

**`matching/__init__.py`** (8 lines) and `__main__.py` (2 lines):
- Both are vestigial stubs. Not worth preserving; `__main__.py` support for
  `python -m markery.matching` is dropped (use `markery match` instead).

**`db/build_entities_db.py`** (190 lines):
- Creates and seeds `entities.duckdb`: `company_entity` (5 rows) and
  `entity_name_variant` (32 rows). Pure seed data — no external API calls.
- Idempotent by design: skips entities and variants that already exist.
- The seed data and `build()` function move to `specialist/matchmaker/entities.py`.
- `open_db()` in entities.py ensures the schema exists before any operation.

**`db/build_patents_db.py`** (544 lines):
- A full reimplementation of what is now `specialist/patent/`. Every function
  in this file has a direct equivalent already in production. Pure deletion.

**`db/test_epo_credentials.py`** (119 lines):
- A standalone smoke-test script superseded by `markery patent verify-credentials`.
  Pure deletion.

**`review.py`** (imports `from markery.matching.score import date_score, class_score`):
- This import must be updated to `from markery.specialist.matchmaker.score import ...`
  during Phase C. `review.py` itself moves in Phase D (HISTORIAN); only the
  import changes now.

### No schema changes

`entities.duckdb` schema is already correct:

```
company_entity       INTEGER PK, canonical_name NOT NULL, entity_type, industry, notes
entity_name_variant  INTEGER PK, entity_id FK, variant_name NOT NULL, source NOT NULL
```

No ALTER TABLE or DROP TABLE operations are needed for Phase C.

### Two CLI surfaces

Per Q25, `markery match` and `markery review` remain as human-facing verbs.
Phase C adds `markery matchmaker` for entity registry management:

| CLI surface | Routes to | Purpose |
|---|---|---|
| `markery match` | `specialist/matchmaker/cli.py` | Candidate generation (existing behavior) |
| `markery matchmaker` | `specialist/matchmaker/cli.py` | Entity registry management |
| `markery review` | `src/markery/review.py` | Unchanged until Phase D |

### Target directory layout

```
src/markery/specialist/matchmaker/
    __init__.py     public interface exports
    entities.py     entity registry: open_db, build, list_entities
    score.py        scoring functions (straight move from matching/score.py)
    link.py         cross-DB candidate generation (from matching/link.py)
    cli.py          markery match + markery matchmaker subcommand router
```

### `entities.py` public interface

```python
DDL = """
CREATE TABLE IF NOT EXISTS company_entity ( ... );
CREATE TABLE IF NOT EXISTS entity_name_variant ( ... );
"""

ENTITIES: list[tuple] = [...]   # seed data: 5 rows
VARIANTS:  list[tuple] = [...]  # seed data: 32 rows

def open_db(db_path: str | Path | None = None) -> duckdb.DuckDBPyConnection:
    # Connect to entities.duckdb (DB["entities"]), ensure schema, return conn

def build(db_path: str | Path | None = None) -> dict[str, int]:
    # Idempotent: insert seed entities and variants, skip existing.
    # Returns {"entities": n_added, "variants": n_added}.

def list_entities(conn: duckdb.DuckDBPyConnection) -> list[dict]:
    # Return [{entity_id, canonical_name, entity_type, industry, notes}]
    # ordered by entity_id.
```

The seed data (`ENTITIES`, `VARIANTS`) is the source of truth for the entity
registry. Adding a new entity means adding a tuple here and running
`markery matchmaker build`.

### `link.py` changes from `matching/link.py`

- Remove `ENTITIES_DB`, `PATENTS_DB`, `TRADEMARKS_DB` module-level constants.
- Import `DB` from `markery.common.config`.
- `_connect()` uses `DB["entities"]`, `DB["patents"]`, `DB["trademarks"]` and
  adds a comment: `# Cross-specialist ATTACH — permitted per Q19 for queries
  that cannot be expressed through individual specialist APIs without multiple
  round trips.`
- All other logic is unchanged.

### `markery match` subcommand (unchanged behavior)

The existing argument structure is kept exactly:

```
markery match <project>          generate candidates for a project
markery match --all              generate for all entities
markery match --entity NAME      single entity
markery match --list-entities    list entity registry
markery match --min-score 0.1    score threshold
```

`--list-entities` prints from `entities.list_entities()` via a read-only
connection (no separate `matchmaker list` needed for this quick lookup).

### `markery matchmaker` subcommand (new)

```
markery matchmaker build         Idempotent seed insert; prints counts
markery matchmaker list          List all entities with IDs and names
markery matchmaker status        Row counts for company_entity and entity_name_variant
```

### `__init__.py` public interface

```python
from markery.specialist.matchmaker.entities import build as build_entities, open_db
from markery.specialist.matchmaker.link import generate_candidates, write_candidates, read_confirmed
from markery.specialist.matchmaker.score import total_score

__all__ = [
    "build_entities", "open_db",
    "generate_candidates", "write_candidates", "read_confirmed",
    "total_score",
]
```

### Unit tests

**`tests/specialist/matchmaker/test_score.py`**:
- Move from `tests/test_score.py`. Update import to
  `from markery.specialist.matchmaker.score import ...`.
- All 6 existing tests kept unchanged. The old file is deleted.

**`tests/specialist/matchmaker/test_entities.py`**:
- `test_build_inserts_seed_data` — in-memory DB; assert 5 entities, 32 variants
- `test_build_is_idempotent` — call build() twice; counts unchanged
- `test_list_entities_returns_all` — assert 5 items, ordered by entity_id
- `test_open_db_creates_schema` — confirm both tables exist after open_db(":memory:")

**`tests/specialist/matchmaker/test_link.py`**:
- `test_entity_ids_for_project` — writes an `entities.txt` to `tmp_path`,
  calls `entity_ids_for_project`; no DB needed.
- `test_entity_ids_for_project_ignores_comments` — lines starting with `#`
  and inline `#` suffixes are ignored.
- `test_read_confirmed_returns_empty_when_missing` — path that doesn't exist → `[]`.
- `test_write_and_read_candidates_roundtrip` — write then read via `read_confirmed`.

  Full `generate_candidates` integration (three DBs via ATTACH) is covered by the
  existing smoke test (`markery match information-systems`) rather than unit tests,
  since ATTACH across temp files in pytest is brittle and adds little value given
  the smoke test exercises the real data.

### Files to delete after Phase C

```
src/markery/matching/cli.py
src/markery/matching/link.py
src/markery/matching/score.py
src/markery/matching/__init__.py
src/markery/matching/__main__.py
src/markery/db/build_entities_db.py
src/markery/db/build_patents_db.py
src/markery/db/test_epo_credentials.py
src/markery/db/__init__.py
tests/test_score.py
```

After deletion `src/markery/db/` and `src/markery/matching/` directories are gone.
`src/markery/` then contains only: `__init__.py`, `cli.py`, `review.py`, `status.py`,
`common/`, `specialist/`.

### Step-by-step migration sequence

1. Create `src/markery/specialist/matchmaker/` with empty `__init__.py`
2. Write `entities.py` — DDL, seed data, `open_db`, `build`, `list_entities`
3. Write `score.py` — straight move from `matching/score.py` (no changes)
4. Write `link.py` — from `matching/link.py`; replace hardcoded paths with `DB` dict;
   add cross-specialist ATTACH comment
5. Write `cli.py` — `cmd_match` (existing behavior) + `cmd_matchmaker` (entity management)
6. Write `__init__.py` — public interface exports
7. Update `src/markery/review.py` import:
   `from markery.matching.score` → `from markery.specialist.matchmaker.score`
8. Update `src/markery/cli.py`:
   - `cmd_match` routes to `specialist/matchmaker/cli.py`
   - add `"matchmaker": lambda: cmd_matchmaker(rest)` dispatch
9. Write unit tests:
   - `tests/specialist/matchmaker/test_score.py` (moved + import updated)
   - `tests/specialist/matchmaker/test_entities.py` (new)
   - `tests/specialist/matchmaker/test_link.py` (new)
10. Smoke tests:
    - `markery match information-systems` — 2,412 candidates, output unchanged
    - `markery match --list-entities` — 5 entities printed
    - `markery matchmaker build` — 0 entities added (all already present)
    - `markery matchmaker status` — 5 entities, 32 variants
    - `markery status` — all row counts unchanged
    - `markery site build information-systems` — 14 pages rendered
11. Delete old files
12. Multi-commit: (1) `specialist/matchmaker/` code + `review.py` import fix,
    (2) CLI routing, (3) tests, (4) delete old files

---

## Phase D — HISTORIAN specialist

**Goal:** Move `src/markery/review.py` and `src/markery/status.py` into
`src/markery/specialist/historian/`. Fix the broken figure display (which queries
the dropped `figure_path` column). Replace all hardcoded DB paths with `DB` from
`common.config`. Use the `Project` dataclass for project file paths.

HISTORIAN owns no database. It reads all three DBs in read-only mode and writes
only to per-project `confirmed.jsonl` files.

### Decision log

**Q1 — Does `status.py` move to historian or stay in `markery/`?**
Move to historian. After Phase D, `src/markery/` will contain only `__init__.py`,
`cli.py`, `common/`, and `specialist/`. Keeping `status.py` at the top level would
leave an orphan. Both `review.py` and `status.py` are "session management" tools
that observe the full system state without owning any of it — a natural unit.

**Q2 — How does the broken `figure_path` query get fixed?**
`fetch_patent()` currently runs `SELECT figure_path FROM patent_figures WHERE ...`.
`figure_path` was dropped in Phase A. Fix: query `SELECT figure_data FROM
patent_figures WHERE patent_no = ? AND figure_no = 1`. If the BLOB is present,
write it to a `tempfile.NamedTemporaryFile(suffix=".png", delete=False)` and
return the temp path. The caller (`display()`) xdg-opens that path unchanged.
Temp files are collected in a session list and unlinked in the `finally` block at
the end of `main()`.

**Q3 — Does historian add new CLI subcommands?**
No new subcommands in Phase D. `markery review` preserves its existing interface
exactly. A `markery historian` top-level subcommand could be added later (e.g.
`markery historian export`, `markery historian stats`) but that scope is deferred.

**Q4 — What gets unit tested?**
Pure functions: `wordwrap`, `load_confirmed`, `write_confirmed`. The DB-dependent
functions (`fetch_tm`, `fetch_patent`, `display`) require live schemas and terminal
I/O — they are covered by smoke tests only. The `status.py` functions `count_jsonl`
and `human_size` are also straightforward to test.

**Q5 — What's the temp-file lifetime strategy for figures?**
`fetch_patent()` returns the temp path but does not unlink it. `main()` collects
all returned figure paths in a `_tmp_figures: list[Path]` list and calls
`path.unlink(missing_ok=True)` for each in the `finally` block. This keeps the
file alive for the duration of the review session (xdg-open may hand off to an
async image viewer) but cleans up on normal exit or `KeyboardInterrupt`.

**Q6 — Where does `PROJECTS_DIR = Path("projects")` go?**
Deleted entirely. `review.py` constructs a `Project(args.project)` instance and
uses `proj.candidates` / `proj.confirmed`. `status.py` reads `ROOT / "projects"`
directly (it iterates all subdirectories, so the `Project` dataclass does not fit).

### Module layout

```
src/markery/specialist/historian/
    __init__.py
    review.py          ← moved from src/markery/review.py; figure + path fixes
    status.py          ← moved from src/markery/status.py; path fixes
    cli.py             ← historian_main() (no-op stub for future use)
```

`src/markery/cli.py` routes:
- `"review"` → `specialist/historian/review.py:main()`
- `"status"` → `specialist/historian/status.py:main()`

### Changes to `review.py`

**Imports to add/change:**

```python
# add
import tempfile
from markery.common.config import DB, Project

# remove
PROJECTS_DIR = Path("projects")
```

**`fetch_patent()` — fix figure query:**

```python
def fetch_patent(conn, patent_no: str) -> dict:
    ...
    fig = conn.execute(
        "SELECT figure_data FROM patent_figures WHERE patent_no = ? AND figure_no = 1",
        [patent_no],
    ).fetchone()
    figure_path = None
    if fig and fig[0]:
        tf = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        tf.write(bytes(fig[0]))
        tf.close()
        figure_path = tf.name
    return {
        "app_dt":    str(p[0]) if p and p[0] else "—",
        "inventors": "  ".join(r[0].title() for r in inv) if inv else "—",
        "cpc_full":  "  ".join(r[0] for r in cls) if cls else "—",
        "figure":    figure_path,
    }
```

**`main()` — replace hardcoded paths:**

```python
# before
project_dir     = PROJECTS_DIR / args.project
candidates_path = project_dir / "matches" / "candidates.jsonl"
confirmed_path  = project_dir / "matches" / "confirmed.jsonl"
conn_tm  = duckdb.connect("data/trademarks.duckdb", read_only=True)
conn_pat = duckdb.connect("data/patents.duckdb",    read_only=True)
conn_ent = duckdb.connect("data/entities.duckdb",   read_only=True)

# after
proj            = Project(args.project)
candidates_path = proj.candidates
confirmed_path  = proj.confirmed
conn_tm  = duckdb.connect(str(DB["trademarks"]), read_only=True)
conn_pat = duckdb.connect(str(DB["patents"]),    read_only=True)
conn_ent = duckdb.connect(str(DB["entities"]),   read_only=True)
```

**`main()` — temp file cleanup:**

```python
_tmp_figures: list[str] = []

try:
    for idx, cand in enumerate(queue, 1):
        pat = fetch_patent(conn_pat, cand["patent_no"])
        if pat["figure"]:
            _tmp_figures.append(pat["figure"])
        ...
except KeyboardInterrupt:
    print("\n  (interrupted)")
finally:
    for p in _tmp_figures:
        Path(p).unlink(missing_ok=True)
    conn_tm.close()
    conn_pat.close()
    conn_ent.close()
```

Note: the existing code closes connections outside the `try` block, so they are
not closed on `KeyboardInterrupt`. Fix this by moving closes into `finally`.

### Changes to `status.py`

Only path changes; no logic changes.

```python
# add import
from markery.common.config import ROOT, DB

# replace hardcoded DB paths
dbs = [
    (str(DB["trademarks"]), ["case_file", "mark_images", "mark_case_status"]),
    (str(DB["patents"]),    ["patents", "patent_classes", "patent_inventors"]),
    (str(DB["entities"]),  ["company_entity", "entity_name_variant"]),
]

# replace projects dir
for project_dir in sorted((ROOT / "projects").iterdir()):
    ...
```

The `db_stats()` function receives a `Path` already, so no change needed there.
The `read_deferred` and `read_next_action` functions reference `root / "DEFERRED.md"`
and `root / "CONTEXT.md"` — change `root = Path(".")` to `root = ROOT`.

### `cli.py` (new, minimal)

```python
"""Historian specialist CLI — human review workflow."""

from __future__ import annotations


def historian_main() -> None:
    """Entry point for future `markery historian` subcommands."""
    print("markery historian: no subcommands defined yet.")
    print("Use 'markery review' to review candidate pairs.")
```

Not wired into `cli.py` dispatch yet — no `markery historian` subcommand in Phase D.
The stub is there so the module exists and can grow in Phase E or later.

### `__init__.py`

```python
from markery.specialist.historian.review import main as review_main
from markery.specialist.historian.status import main as status_main

__all__ = ["review_main", "status_main"]
```

### Updates to `src/markery/cli.py`

```python
def cmd_review(rest: list[str]) -> None:
    from markery.specialist.historian.review import main   # was: markery.review
    sys.argv = ["markery review"] + rest
    main()

def cmd_status() -> None:
    from markery.specialist.historian.status import main   # was: markery.status
    main()
```

No change to routing table or subcommand descriptions.

### Unit tests

**`tests/specialist/historian/__init__.py`** — empty

**`tests/specialist/historian/test_review.py`**:

- `test_wordwrap_short_text` — text shorter than width → single-element list
- `test_wordwrap_long_text` — text longer than width → wraps at word boundary
- `test_wordwrap_empty_text` — empty string → `["—"]`
- `test_load_confirmed_empty_when_missing` — path that doesn't exist → empty set
- `test_load_confirmed_parses_jsonl` — write two JSONL lines; assert two tuples
- `test_write_confirmed_appends` — call twice; file has two lines
- `test_write_confirmed_creates_parent_dir` — deep nested path; file created

**`tests/specialist/historian/test_status.py`**:

- `test_human_size_bytes` — `human_size` on a file with known size
- `test_count_jsonl_empty_when_missing` — path doesn't exist → 0
- `test_count_jsonl_counts_nonempty_lines` — write 3 lines + 1 blank → 3

The DB-dependent `db_stats()` and the full `main()` output are covered by
the existing `markery status` smoke test.

### Files to delete after Phase D

```
src/markery/review.py
src/markery/status.py
```

After deletion `src/markery/` contains only: `__init__.py`, `cli.py`, `common/`,
`specialist/`. The only remaining Phase E target in `src/markery/` is `cli.py`
itself (which is the unified entry point, not specialist code).

### Step-by-step migration sequence

1. Create `src/markery/specialist/historian/` with empty `__init__.py`
2. Copy `review.py` → `specialist/historian/review.py`; apply all changes:
   - Add `import tempfile` and `from markery.common.config import DB, Project`
   - Remove `PROJECTS_DIR`
   - Fix `fetch_patent()`: `figure_data` BLOB + tempfile write
   - Fix `main()`: use `Project`, use `DB`, move conn closes to `finally`,
     collect and unlink temp figure files
3. Copy `status.py` → `specialist/historian/status.py`; apply all changes:
   - Add `from markery.common.config import ROOT, DB`
   - Replace `root = Path(".")` with `root = ROOT`
   - Replace hardcoded DB path strings with `DB` dict entries
4. Write `specialist/historian/cli.py` (stub only)
5. Write `specialist/historian/__init__.py`
6. Update `src/markery/cli.py`:
   - `cmd_review` imports from `specialist.historian.review`
   - `cmd_status` imports from `specialist.historian.status`
7. Write unit tests:
   - `tests/specialist/historian/__init__.py`
   - `tests/specialist/historian/test_review.py` (7 tests)
   - `tests/specialist/historian/test_status.py` (3 tests)
8. Run `pytest -q` — all tests pass
9. Smoke tests:
   - `markery status` — output unchanged from pre-Phase D
   - `markery review information-systems --min-score 0.9` — first few candidates
     display correctly; figure temp file is created and opened; session exits clean
10. Delete `src/markery/review.py` and `src/markery/status.py`
11. Run `pytest -q` again to confirm nothing imported from the old paths
12. Multi-commit: (1) `specialist/historian/` code, (2) CLI routing updates,
    (3) tests, (4) delete old files

---

## Phase E — PUBLISHER specialist

**Goal:** Move `tools/site_builder/` and `tools/image_enhancement/` into
`src/markery/specialist/publisher/`. Delete `tools/patent_docs/` (superseded by
Phase A). Fix all hardcoded DB path strings and project path strings. Extract the
`_site_build()` orchestration from `cli.py` into a proper `build_site()` function.
Wire `markery publisher` as a CLI stub for future use.

**Background:** The editable install's `MAPPING` currently lists `site_builder`,
`image_enhancement`, and `patent_docs` as top-level importable packages pointing
into `tools/`. This is stale state from before Phase A changed `pyproject.toml`
to `where = ["src"]`. It works now only because `pip install -e .` has not been
re-run since that change. Phase E fixes the underlying import paths and removes
the reliance on this stale mapping. After Phase E, running `pip install -e .`
will regenerate the MAPPING with only `markery` present.

### Decision log

**Q1 — Does `db_paths: dict[str, str]` stay as a function parameter?**
No. The `db_paths` dict is constructed in `cli.py` with hardcoded strings and
threaded through every query and render function purely as a vehicle for DB paths.
Phase E removes it from all function signatures. Functions use `DB` from
`common.config` directly. `get_entity_stats` already needs no DB at all (pure
aggregation). Call sites in `build_site()` become simpler: no dict to construct
or pass around.

**Q2 — How are narrative content paths fixed in `render.py`?**
Replace `Path(f"projects/{project}/content/...")` with
`Project(project).content / "..."` in each render function. The `project: str`
parameter stays so render functions remain callable with just a project name. No
signature-breaking change for callers.

**Q3 — Does `_site_build()` stay in `cli.py` or move to publisher?**
Move into `specialist/publisher/build.py` as `build_site(project, out_dir=None)`.
This separates orchestration from argument parsing, makes `build_site` directly
importable by agents or tests, and leaves `cli.py` with a one-liner
`cmd_site()`. The print statements (`→ entities/...`) move into `build_site` so
the smoke-test output is preserved.

**Q4 — Does `image_enhancement` move into publisher?**
Yes, as a sub-package at `specialist/publisher/image_enhancement/`. The internal
relative imports (`from .pipeline import`, `from .gallery import`) are
package-relative and continue to work unchanged after the move. The only code
change inside `image_enhancement` is the `--db` default in `cli.py`:
`"data/trademarks.duckdb"` → `str(DB["trademarks"])`. No other logic changes to
the image pipeline.

**Q5 — Does `tools/patent_docs/` get deleted?**
Yes. Phase A moved all its logic into `specialist/patent/`. `cli.py` no longer
references it. It is unreferenced dead code in `tools/`.

**Q6 — Does `tools/historian/` get deleted?**
No. `tools/historian/` contains only Markdown documentation (content schemas,
examples, reference materials for the Claude historian agent). It has no Python
files and is not imported by anything. It stays in place as prose docs.

**Q7 — What gets unit tested?**
Pure functions: `_esc`, `_render_markdown` (from `render.py`) and
`get_entity_stats` (from `queries.py`). These are straightforward to test
without any DB or filesystem. The DB-dependent query functions and the full page
render pipeline (which writes HTML files to disk) are covered by the
`markery site build information-systems` smoke test.

**Q8 — Does `markery publisher` get wired into the CLI?**
Yes, as a stub (like `markery historian`). The `build` subcommand routes to
`build_site` so `markery publisher build <project>` is equivalent to
`markery site build <project>`. `markery site` remains the canonical form for
humans; `markery publisher` gives agents a well-namespaced entry point.

### Module layout

```
src/markery/specialist/publisher/
    __init__.py
    queries.py            ← from tools/site_builder/queries.py; db_paths removed
    render.py             ← from tools/site_builder/render.py; db_paths removed
    build.py              ← new; extracts _site_build() from cli.py
    cli.py                ← publisher_main() stub + build subcommand
    image_enhancement/
        __init__.py       ← unchanged
        binarize.py       ← unchanged
        cli.py            ← --db default only
        gallery.py        ← unchanged
        pipeline.py       ← unchanged
        upscale.py        ← unchanged
        ENHANCE.md        ← unchanged
```

After Phase E, `tools/` contains only:
```
tools/historian/          ← documentation only; not deleted
```

### Changes to `queries.py`

**`_connect()` — use `DB` directly:**

```python
# before
def _connect(db_paths: dict[str, str]) -> duckdb.DuckDBPyConnection:
    conn = duckdb.connect(db_paths["entities"], read_only=True)
    conn.execute(f"ATTACH '{db_paths['patents']}'    AS pat (READ_ONLY)")
    conn.execute(f"ATTACH '{db_paths['trademarks']}' AS tm  (READ_ONLY)")
    return conn

# after
from markery.common.config import DB, Project

def _connect() -> duckdb.DuckDBPyConnection:
    conn = duckdb.connect(str(DB["entities"]), read_only=True)
    conn.execute(f"ATTACH '{DB['patents']}'    AS pat (READ_ONLY)")
    conn.execute(f"ATTACH '{DB['trademarks']}' AS tm  (READ_ONLY)")
    return conn
```

**Function signature changes (all callers in `build.py` updated accordingly):**

```python
# before → after
get_entities(db_paths, entity_ids)               → get_entities(entity_ids)
get_trademarks_for_project(db_paths, entity_ids) → get_trademarks_for_project(entity_ids)
get_patents_for_project(db_paths, entity_ids)    → get_patents_for_project(entity_ids)
get_confirmed_matches(project, db_paths)         → get_confirmed_matches(project)
get_mark_image_b64(db_paths, serial_no)          → get_mark_image_b64(serial_no)
get_patent_figure_b64(db_paths, patent_no)       → get_patent_figure_b64(patent_no)
get_entity_stats(db_paths, entity_ids, ...)      → get_entity_stats(entity_ids, ...)
```

**Project path fixes:**

```python
# get_project_entity_ids
path = Path(f"projects/{project}/entities.txt")          # before
path = Project(project).entities_file                    # after

# get_confirmed_matches — confirmed path
path = Path(f"projects/{project}/matches/confirmed.jsonl")   # before
path = Project(project).confirmed                            # after

# get_confirmed_matches — essay path per match
essay = Path(f"projects/{project}/content/{slug}.md")    # before
essay = Project(project).content / f"{slug}.md"          # after
```

**`get_mark_image_b64` and `get_patent_figure_b64`:**

```python
def get_mark_image_b64(serial_no: str) -> str | None:
    conn = duckdb.connect(str(DB["trademarks"]), read_only=True)
    ...

def get_patent_figure_b64(patent_no: str) -> str | None:
    conn = duckdb.connect(str(DB["patents"]), read_only=True)
    ...
```

### Changes to `render.py`

**Relative imports → absolute:**

```python
# before (in render_landing, render_trademark_gallery, etc.)
from .queries import get_mark_image_b64
from .queries import get_patent_figure_b64

# after
from markery.specialist.publisher.queries import get_mark_image_b64, get_patent_figure_b64
```

**`db_paths` removed from all render function signatures:**

```python
# before
def render_landing(project, entities, trademarks, patents, matches,
                   entity_stats, db_paths, out_dir): ...
def render_trademark_gallery(project, entities, trademarks, matches,
                              entity_colors, db_paths, out_dir): ...
def render_patent_gallery(project, entities, patents, matches,
                           entity_colors, db_paths, out_dir): ...
def render_match_essay(project, match, entities, db_paths, out_dir): ...

# after (db_paths removed; functions call queries directly via no-arg versions)
def render_landing(project, entities, trademarks, patents, matches,
                   entity_stats, out_dir): ...
def render_trademark_gallery(project, entities, trademarks, matches,
                              entity_colors, out_dir): ...
def render_patent_gallery(project, entities, patents, matches,
                           entity_colors, out_dir): ...
def render_match_essay(project, match, entities, out_dir): ...
```

**Narrative path fixes in each render function:**

```python
# before
_read_narrative(Path(f"projects/{project}/content/index-narrative.md"))

# after
_read_narrative(Project(project).content / "index-narrative.md")
```

Same pattern for `trademarks-narrative.md`, `patents-narrative.md`, and
`entity-{slug}.md`.

### New `build.py`

Extracts all orchestration from `cli.py::_site_build()`. Print statements are
preserved so smoke-test output is unchanged.

```python
from __future__ import annotations

from pathlib import Path

from markery.common.config import Project
from markery.specialist.publisher import queries as q
from markery.specialist.publisher import render as r


def build_site(project: str, out_dir: Path | None = None) -> list[Path]:
    """Render all pages for a project; return list of written paths."""
    proj = Project(project)
    out  = out_dir if out_dir is not None else proj.site
    out.mkdir(parents=True, exist_ok=True)
    (out / "entities").mkdir(exist_ok=True)
    (out / "matches").mkdir(exist_ok=True)

    print(f"Building site for '{project}' → {out}/")

    entity_ids = q.get_project_entity_ids(project)
    entities   = q.get_entities(entity_ids)
    trademarks = q.get_trademarks_for_project(entity_ids)
    patents    = q.get_patents_for_project(entity_ids)
    matches    = q.get_confirmed_matches(project)
    stats      = q.get_entity_stats(entity_ids, trademarks, patents, matches)
    colors     = r._entity_color_map(entity_ids)

    pages: list[Path] = []

    pages.append(r.render_landing(project, entities, trademarks, patents, matches, stats, out))
    print(f"  landing          → {pages[-1].name}")

    pages.append(r.render_trademark_gallery(project, entities, trademarks, matches, colors, out))
    print(f"  trademark gallery → {pages[-1].name}")

    pages.append(r.render_patent_gallery(project, entities, patents, matches, colors, out))
    print(f"  patent gallery   → {pages[-1].name}")

    for entity in entities:
        ent_tms   = [t for t in trademarks if t["entity_id"] == entity["entity_id"]]
        ent_pats  = [p for p in patents    if p["entity_id"] == entity["entity_id"]]
        ent_mats  = [m for m in matches    if m["entity_id"] == entity["entity_id"]]
        ent_stats = stats.get(entity["entity_id"], {})
        p = r.render_entity_page(project, entity, entities, ent_tms, ent_pats, ent_mats, ent_stats, out)
        pages.append(p)
        print(f"  entity           → entities/{p.name}")

    seen: set[str] = set()
    for match in matches:
        slug = match.get("slug", "")
        if slug in seen:
            continue
        seen.add(slug)
        p = r.render_match_essay(project, match, entities, out)
        pages.append(p)
        print(f"  match essay      → matches/{p.name}")

    print(f"\n{len(pages)} pages written to {out}/")
    return pages
```

### `cli.py` (publisher specialist)

```python
"""Publisher specialist CLI — static site generation."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def publisher_main() -> None:
    ap = argparse.ArgumentParser(prog="markery publisher")
    sub = ap.add_subparsers(dest="action", required=True)

    bp = sub.add_parser("build", help="Build static site for a project")
    bp.add_argument("project", help="Project name")
    bp.add_argument("--out", metavar="DIR",
                    help="Output directory (default: projects/<project>/site)")

    args = ap.parse_args()
    if args.action == "build":
        from markery.specialist.publisher.build import build_site
        build_site(args.project, Path(args.out) if args.out else None)
```

### `__init__.py`

```python
from markery.specialist.publisher.build import build_site
from markery.specialist.publisher import queries, render

__all__ = ["build_site", "queries", "render"]
```

### Changes to `image_enhancement/cli.py`

Only the `--db` argument default changes:

```python
# before
parser.add_argument("--db", default="data/trademarks.duckdb", ...)

# after
from markery.common.config import DB
parser.add_argument("--db", default=str(DB["trademarks"]), ...)
```

No other changes to the image enhancement pipeline.

### Updates to `src/markery/cli.py`

**`cmd_site()` — delegate to `build_site`:**

```python
def cmd_site(rest: list[str]) -> None:
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(prog="markery site")
    sub = parser.add_subparsers(dest="action", required=True)
    build = sub.add_parser("build", help="Render project to HTML")
    build.add_argument("project")
    build.add_argument("--out", metavar="DIR")

    args = parser.parse_args(rest)
    if args.action == "build":
        from markery.specialist.publisher.build import build_site
        build_site(args.project, Path(args.out) if args.out else None)
```

`_site_build()` is deleted from `cli.py`.

**`cmd_enhance()` — new import path:**

```python
def cmd_enhance(rest: list[str]) -> None:
    from markery.specialist.publisher.image_enhancement.cli import main
    sys.argv = ["markery enhance"] + rest
    main()
```

**`cmd_publisher()` — new:**

```python
def cmd_publisher(rest: list[str]) -> None:
    from markery.specialist.publisher.cli import publisher_main
    sys.argv = ["markery publisher"] + rest
    publisher_main()
```

**`_SUBCOMMANDS` update:**

```python
_SUBCOMMANDS = {
    ...
    "publisher":  "Static site generation  (build <project>)",
    ...
}
```

**Dispatch table update:**

```python
"publisher": lambda: cmd_publisher(rest),
```

### Unit tests

**`tests/specialist/publisher/__init__.py`** — empty

**`tests/specialist/publisher/test_render.py`**:

- `test_esc_empty_string` — `_esc("")` → `""`
- `test_esc_none` — `_esc(None)` → `""`
- `test_esc_html_chars` — `<`, `>`, `&`, `"` all escaped
- `test_render_markdown_heading` — `## Heading` → contains `<h2>Heading</h2>`
- `test_render_markdown_paragraph` — bare text → wrapped in `<p>` tags
- `test_render_markdown_bold` — `**bold**` → `<strong>bold</strong>`
- `test_render_markdown_code_inline` — `` `code` `` → `<code>code</code>`
- `test_render_markdown_fenced_block` — triple-backtick block → `<pre><code>...</code></pre>`

**`tests/specialist/publisher/test_queries.py`**:

- `test_get_entity_stats_counts` — pass 2 entities, trademarks/patents/matches
  split between them; verify per-entity counts are correct
- `test_get_entity_stats_year_range` — trademarks with known `filing_dt` →
  verify `active_from`, `active_to` correct
- `test_get_entity_stats_empty_lists` — empty trademarks/patents/matches →
  all counts 0, `active_from` / `active_to` both `None`

Note: `_esc` and `_render_markdown` are private functions (`_` prefix). Import
them directly in the test via:
```python
from markery.specialist.publisher.render import _esc, _render_markdown
```

### Files to delete after Phase E

```
tools/site_builder/__init__.py
tools/site_builder/queries.py
tools/site_builder/render.py
tools/patent_docs/cli.py
tools/patent_docs/fetch.py
tools/patent_docs/__init__.py
tools/patent_docs/__main__.py
tools/patent_docs/migrate.py
tools/patent_docs/signals.py
tools/image_enhancement/__init__.py
tools/image_enhancement/binarize.py
tools/image_enhancement/cli.py
tools/image_enhancement/gallery.py
tools/image_enhancement/pipeline.py
tools/image_enhancement/upscale.py
tools/image_enhancement/ENHANCE.md
```

After deletion, `tools/` contains only `tools/historian/` (documentation).

### Post-deletion reinstall

After deleting `tools/site_builder/`, `tools/image_enhancement/`, and
`tools/patent_docs/`, run:

```
pip install -e .
```

This regenerates the editable install `MAPPING` in `.venv/`, removing the stale
entries for `site_builder`, `image_enhancement`, `patent_docs`, and `historian`.
The MAPPING will then contain only `{'markery': '.../src/markery'}`.

### Step-by-step migration sequence

1. Create `src/markery/specialist/publisher/` with empty `__init__.py`
2. Write `queries.py`:
   - Add `from markery.common.config import DB, Project`
   - Remove `db_paths` from `_connect()` and all function signatures
   - Replace `duckdb.connect(db_paths[...])` with `duckdb.connect(str(DB[...]))`
   - Replace `Path(f"projects/{project}/...")` with `Project(project).*`
3. Write `render.py`:
   - Change `from .queries import ...` → `from markery.specialist.publisher.queries import ...`
   - Add `from markery.common.config import Project` at top
   - Remove `db_paths` from all `render_*` function signatures
   - Replace `Path(f"projects/{project}/content/...")` with `Project(project).content / "..."`
4. Write `build.py` — `build_site(project, out_dir=None)` orchestration
5. Write `publisher/cli.py` — `publisher_main()` with `build` subcommand
6. Write `publisher/__init__.py`
7. Copy `tools/image_enhancement/` → `src/markery/specialist/publisher/image_enhancement/`;
   update `--db` default in `image_enhancement/cli.py`
8. Update `src/markery/cli.py`:
   - `cmd_site()` → call `build_site`; delete `_site_build()`
   - `cmd_enhance()` → import from `markery.specialist.publisher.image_enhancement.cli`
   - Add `cmd_publisher()` and wire into `_SUBCOMMANDS` + dispatch
9. Write unit tests:
   - `tests/specialist/publisher/__init__.py`
   - `tests/specialist/publisher/test_render.py` (8 tests)
   - `tests/specialist/publisher/test_queries.py` (3 tests)
10. Run `pytest -q` — all tests pass
11. Smoke tests:
    - `markery site build information-systems` — same page count and structure
    - `markery publisher build information-systems` — identical output
    - `markery status` — unchanged
12. Delete `tools/site_builder/`, `tools/image_enhancement/`, `tools/patent_docs/`
13. Run `pip install -e .` to regenerate editable install MAPPING
14. Run `pytest -q` again — all tests still pass
15. Smoke test `markery site build information-systems` again to confirm clean import
16. Multi-commit: (1) `specialist/publisher/` code + `image_enhancement` sub-package,
    (2) `src/markery/cli.py` updates, (3) tests, (4) delete old files + reinstall note

---

## Phase F — Scoring refinement, Open Graph, and documentation update

Three independent components, no ordering dependency between them.

### Component 1 — D006: Company-name mark filter

**Problem**

`generate_candidates()` in `link.py` pairs every trademark owned by an entity against
every patent assigned to that entity. For entities like REMINGTON, RAND, and WILSON
JONES COMPANY, some trademarks carry the company name itself as the `mark_id_char`
value (e.g. `"REMINGTON"`, `"RAND"`, `"WILSON JONES COMPANY"`). These score ~0.80
against all patents in the date window because the date and class components apply
unconditionally — there is no penalty for a mark that is simply the company's own name.

The false positives clutter the candidate list and create noise during review.

**Root cause in scoring**

`total_score()` in `score.py` calls `date_score()` + `class_score()`. Neither
function has any awareness of whether the mark name is substantively different from
the entity name.

**Fix strategy**

Add a boolean predicate `is_company_name_mark(canonical_name, mark_name)` to
`score.py`, applied as a hard exclusion in `generate_candidates()` before scoring.

A mark is classified as a company-name mark if the normalised mark text appears
entirely within the normalised canonical name, or the normalised canonical name
appears entirely within the normalised mark text. Normalisation strips common legal
suffixes (`COMPANY`, `CO`, `INC`, `CORP`, `LTD` and their punctuated variants)
and collapses whitespace.

```python
_LEGAL_SUFFIXES = re.compile(
    r'\b(COMPANY|CO\.?|INC\.?|CORP\.?|CORPORATION|LTD\.?|LLC)\b',
    re.IGNORECASE,
)

def _normalise(s: str) -> str:
    """Strip legal suffixes, upper-case, collapse whitespace."""
    s = _LEGAL_SUFFIXES.sub("", s or "").upper()
    return " ".join(s.split())

def is_company_name_mark(canonical_name: str, mark_name: str | None) -> bool:
    """True when the mark text is essentially the company's own name.

    Filters marks like "REMINGTON" for entity "Remington Arms Company" —
    pairing those against every patent produces systematic false positives
    (D006).
    """
    cn = _normalise(canonical_name)
    mn = _normalise(mark_name or "")
    if not mn:
        return False
    return cn in mn or mn in cn
```

**Application in link.py**

Inside the `for tm in trademarks:` loop in `generate_candidates()`, skip the mark
before entering the inner patent loop:

```python
from markery.specialist.matchmaker.score import is_company_name_mark, total_score

for tm in trademarks:
    if is_company_name_mark(entity_names[eid], tm["mark"]):
        continue
    tm_filing = tm["filing_dt"]
    for pat in patents:
        ...
```

This avoids scoring the pair at all — no candidates are written for company-name
marks, not even low-scoring ones. Because the filter is in `generate_candidates()`
rather than in the scoring function, confirmed matches already in `confirmed.jsonl`
are unaffected (they were already reviewed and accepted by the researcher).

**Files changed**

| File | Change |
|---|---|
| `src/markery/specialist/matchmaker/score.py` | Add `_LEGAL_SUFFIXES`, `_normalise()`, `is_company_name_mark()` |
| `src/markery/specialist/matchmaker/link.py` | Import `is_company_name_mark`; add one `if is_company_name_mark(...): continue` before inner loop |

**Tests**

New file `tests/specialist/matchmaker/test_score.py`:

```python
from markery.specialist.matchmaker.score import is_company_name_mark

def test_company_name_exact():
    assert is_company_name_mark("Remington Arms Company", "REMINGTON") is True

def test_company_name_with_suffix():
    assert is_company_name_mark("Wilson Jones Company", "WILSON JONES") is True

def test_company_name_substring_both_ways():
    assert is_company_name_mark("Rand Corporation", "RAND") is True
    assert is_company_name_mark("RAND", "Rand Corporation") is True

def test_company_name_not_matching():
    # "VISIBLE" does not appear in or contain "Remington Arms Company"
    assert is_company_name_mark("Remington Arms Company", "VISIBLE INDEX") is False

def test_company_name_none_mark():
    assert is_company_name_mark("Rand Corporation", None) is False

def test_company_name_empty_mark():
    assert is_company_name_mark("Rand Corporation", "") is False

def test_company_name_suffix_stripping():
    # "REMINGTON" in "REMINGTON ARMS" after stripping "COMPANY", "CO", etc.
    assert is_company_name_mark("Remington Arms Co.", "REMINGTON ARMS") is True
```

Existing `test_score.py` for `date_score` and `class_score` is not present yet —
these can be added in the same commit:

```python
from datetime import date
from markery.specialist.matchmaker.score import date_score, class_score, total_score

def test_date_score_patent_before_tm():
    # grant 1920, filing 1925 — positive delta, ~0.375
    s = date_score(date(1920, 1, 1), date(1925, 6, 1))
    assert 0.2 < s <= 0.5

def test_date_score_tm_before_patent():
    # filing before grant — slight negative
    s = date_score(date(1925, 1, 1), date(1920, 6, 1))
    assert -0.4 <= s < 0.0

def test_date_score_none_inputs():
    assert date_score(None, date(1925, 1, 1)) == 0.0
    assert date_score(date(1920, 1, 1), None) == 0.0

def test_class_score_hit():
    assert class_score(["B42F", "A63F"]) == 0.3

def test_class_score_miss():
    assert class_score(["A63F", "H04N"]) == 0.0

def test_total_score_bounds():
    s = total_score(date(1920, 1, 1), date(1925, 1, 1), ["B42F"])
    assert 0.0 <= s <= 0.81  # date(0.375) + class(0.3) < 0.8
```

**Smoke test**

```
markery match information-systems --list-entities  # unchanged
markery match information-systems                  # should have fewer candidates
```

Compare candidate count to the baseline stored in `projects/information-systems/candidates.jsonl`.

---

### Component 2 — P3: Open Graph metadata

**Problem**

When a link to a Markery entity page or match essay is shared in Slack, Discord, or
similar chat platforms, the platform's link-unfurler fetches the page and looks for
`og:title`, `og:description`, and `og:url` `<meta>` tags. Without these tags the
unfurler falls back to the raw `<title>` and produces a generic or empty card.

Open Graph tags require an absolute URL for `og:url`. The site is hosted at
`https://cosmogspacely.github.io/markery/` — but that base URL is not stored
anywhere in the codebase, so it must be injected at build time.

**Changes required**

**`render.py` — `_page()` signature**

Add an optional `og: dict | None = None` keyword argument. When present, inject four
`<meta property>` tags after `<title>`:

```python
def _page(
    title: str,
    body: str,
    nav_links: dict[str, str],
    depth: int = 0,
    og: dict | None = None,
) -> str:
    prefix = "../" * depth
    nav = "".join(
        f'<a href="{prefix}{href}">{_esc(label)}</a>'
        for label, href in nav_links.items()
    )
    og_tags = ""
    if og:
        og_tags = (
            f'<meta property="og:title"       content="{_esc(og.get("title", title))}">\n'
            f'<meta property="og:description" content="{_esc(og.get("description", ""))}">\n'
            f'<meta property="og:url"         content="{_esc(og.get("url", ""))}">\n'
            f'<meta property="og:type"        content="article">\n'
        )
    return (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f'<title>{_esc(title)}</title>\n'
        + og_tags
        + f'<style>{_CSS}</style>\n'
        '</head>\n<body>\n'
        ...
    )
```

**`render.py` — callers**

Each `render_*` function gains an optional `base_url: str | None = None` parameter
and constructs the OG dict before calling `_page()`:

| Function | `og:title` | `og:description` | `og:url` (path suffix) |
|---|---|---|---|
| `render_landing` | `"{Project Title} — Markery"` | `"{N} confirmed matches across {M} entities"` | `"{base_url}/{project}/index.html"` |
| `render_trademark_gallery` | `"Trademark Gallery"` | `"All trademarks in the {project} project"` | `"{base_url}/{project}/trademarks.html"` |
| `render_patent_gallery` | `"Patent Gallery"` | `"All patents in the {project} project"` | `"{base_url}/{project}/patents.html"` |
| `render_entity_page` | `"{entity name}"` | `"{trademark_count} trademarks · {patent_count} patents"` | `"{base_url}/{project}/entities/{slug}.html"` |
| `render_match_essay` | `"{trademark} ↔ {patent_no}"` | `"Match essay for {trademark} and {patent_no}"` | `"{base_url}/{project}/matches/{slug}.html"` |

When `base_url` is `None`, `og` is not passed to `_page()` — no OG tags are written.
This keeps local builds clean (no broken absolute URLs).

**`build.py` — `build_site()` signature**

```python
def build_site(
    project: str,
    out_dir: Path | None = None,
    base_url: str | None = None,
) -> list[Path]:
```

Pass `base_url` through to every `render_*` call:

```python
pages.append(r.render_landing(..., base_url=base_url))
pages.append(r.render_trademark_gallery(..., base_url=base_url))
pages.append(r.render_patent_gallery(..., base_url=base_url))
# entity pages:
p = r.render_entity_page(..., base_url=base_url)
# match essays:
p = r.render_match_essay(..., base_url=base_url)
```

**`cli.py` — `publisher_main()`**

```python
bp.add_argument(
    "--base-url",
    metavar="URL",
    default=None,
    help="Absolute base URL for Open Graph og:url tags (e.g. https://example.github.io/markery)",
)
# in build action:
build_site(args.project, Path(args.out) if args.out else None, base_url=args.base_url)
```

**`src/markery/cli.py` — `cmd_site()`**

```python
build.add_argument(
    "--base-url",
    metavar="URL",
    default=None,
    help="Absolute base URL for Open Graph og:url tags",
)
# in build action:
build_site(args.project, Path(args.out) if args.out else None, base_url=args.base_url)
```

**`.github/workflows/pages.yml` — pass base URL**

```yaml
      - name: Build sites
        run: markery site build information-systems --base-url https://cosmogspacely.github.io/markery
```

**Tests**

Extend `tests/specialist/publisher/test_render.py`:

```python
def test_page_no_og_tags():
    result = _page("Title", "<p>body</p>", {})
    assert 'property="og:' not in result

def test_page_with_og_tags():
    og = {"title": "T", "description": "D", "url": "https://example.com/page.html"}
    result = _page("Title", "<p>body</p>", {}, og=og)
    assert 'property="og:title"' in result
    assert 'content="T"' in result
    assert 'property="og:url"' in result
    assert 'content="https://example.com/page.html"' in result
    assert 'property="og:type"' in result
    assert 'content="article"' in result
```

**Files changed**

| File | Change |
|---|---|
| `src/markery/specialist/publisher/render.py` | `_page()` gains `og` kwarg; each `render_*` gains `base_url` kwarg |
| `src/markery/specialist/publisher/build.py` | `build_site()` gains `base_url` kwarg; passes through to all `render_*` |
| `src/markery/specialist/publisher/cli.py` | `--base-url` argument added to `build` subparser |
| `src/markery/cli.py` | `--base-url` added to `cmd_site()` build parser |
| `.github/workflows/pages.yml` | `markery site build … --base-url https://cosmogspacely.github.io/markery` |
| `tests/specialist/publisher/test_render.py` | Two new test functions |

---

### Component 3 — Documentation update

Four files are stale after the Phase A–E refactor. Update them in a single commit.

**`STATUS.md`**

Current state: references `src/markery/db/tsdr_client.py`, `src/markery/matching/`,
`tools/image_enhancement/` — all deleted or moved.

Changes:
- Update "Phase" line to reflect Phase 2 (reorg) is complete, Phase 3 (corpus) and
  Phase 4 publication in progress
- Replace infrastructure ledger entries:

| Old path | New path |
|---|---|
| `src/markery/db/build_trademarks_db.py` | `specialist/trademark/build.py` |
| `src/markery/db/tsdr_client.py` | `specialist/trademark/tsdr_client.py` |
| `src/markery/db/build_patents_db.py` | `specialist/patent/epo_client.py` + `specialist/patent/build.py` |
| `src/markery/db/build_entities_db.py` | `specialist/matchmaker/build.py` |
| `tools/image_enhancement/` | `specialist/publisher/image_enhancement/` |
| `tools/site_builder/` | `specialist/publisher/` |
| `tools/patent_docs/` | `specialist/patent/figures.py` + `specialist/patent/signals.py` |
| `src/markery/review.py` | `specialist/historian/review.py` |
| `src/markery/status.py` | `specialist/historian/status.py` |

**`CONTEXT.md`**

Current "Next action" line: update to reflect that the specialist refactor (Phase 2)
is complete and the next prioritised task is corpus expansion (Phase 3: D001 —
remaining CPC class fetch) or publishing improvements (Phase 4: D006 filter complete
if Component 1 is done, P3 Open Graph if Component 2 is done).

**`ROADMAP.md`**

- Mark Phase 2 items as complete (`[x]`):
  - R1 (patent specialist), R2 (site build subcommand), R3 (entity slug fix), R4 (delete `tools/`)
- If D006 implemented: mark D006 as complete
- If P3 implemented: mark P3 as complete

**`docs/workflows/research-session.md`**

Step 1 currently reads:
```
python src/markery/db/build_entities_db.py
```

Update to:
```
markery matchmaker build
```

Scan the rest of the file for any other references to the old `src/markery/db/`
paths or `tools/` paths and update them to their current CLI equivalents.

**Files changed**

| File | Change |
|---|---|
| `STATUS.md` | Phase and infrastructure ledger update |
| `CONTEXT.md` | "Next action" paragraph |
| `ROADMAP.md` | Tick completed items |
| `docs/workflows/research-session.md` | CLI command updates |

---

### Step-by-step migration sequence

**Component 1 (D006 filter) — can be done independently:**

1. Add `import re` and `_LEGAL_SUFFIXES`, `_normalise()`, `is_company_name_mark()` to
   `src/markery/specialist/matchmaker/score.py`
2. Add `from markery.specialist.matchmaker.score import is_company_name_mark` to
   `link.py`; add one `if is_company_name_mark(…): continue` line before the inner loop
3. Write `tests/specialist/matchmaker/test_score.py` with 7 `is_company_name_mark`
   tests and 6 `date_score`/`class_score`/`total_score` tests
4. Run `pytest tests/specialist/matchmaker/` — all pass
5. Smoke: `markery match information-systems` — candidate count decreases; no crash
6. Commit: `"Add company-name mark exclusion filter (D006)"`

**Component 2 (P3 Open Graph) — can be done independently:**

1. Edit `_page()` in `render.py`: add `og: dict | None = None` kwarg; inject OG tags
   between `<title>` and `<style>` when `og` is not None
2. Edit each `render_*` function: add `base_url: str | None = None` kwarg; build `og`
   dict when `base_url` is not None; pass `og=og` to `_page()`
3. Edit `build_site()` in `build.py`: add `base_url` kwarg; pass through to all
   `render_*` calls
4. Edit `publisher_main()` in `publisher/cli.py`: add `--base-url` arg
5. Edit `cmd_site()` in `src/markery/cli.py`: add `--base-url` arg
6. Edit `.github/workflows/pages.yml`: append `--base-url https://cosmogspacely.github.io/markery`
7. Add two tests to `tests/specialist/publisher/test_render.py`
8. Run `pytest tests/specialist/publisher/` — all pass
9. Smoke: `markery site build information-systems --base-url https://cosmogspacely.github.io/markery`
   — open `projects/information-systems/site/index.html` in browser; inspect source
   for `og:` tags
10. Commit: `"Add Open Graph metadata to rendered pages (P3)"`

**Component 3 (docs) — can be done at any time:**

1. Update `STATUS.md` infrastructure ledger
2. Update `CONTEXT.md` "Next action"
3. Update `ROADMAP.md` — tick R1–R4 and any newly completed deferred items
4. Update `docs/workflows/research-session.md` CLI commands
5. Commit: `"Update STATUS, CONTEXT, ROADMAP, and research-session workflow docs"`


