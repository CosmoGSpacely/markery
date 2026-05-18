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

