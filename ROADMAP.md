# Markery Roadmap

Active and upcoming tool development. Items originate in `DEFERRED.md` and are promoted here when active. Completed phases are in `archive/`.

---

## Phase 8 — Specialist Completeness

**Goal:** All five specialists have accurate, complete personas. Key operations are covered by instruction cards. Reference material reflects the current schema. Deferred functional gap D007 (patent bulk CSV) has a clear implementation path.

The persona stubs created in this session (D009) are the starting point. The historian persona (D008) has stale content from the Phase 7 schema migration and must be fixed before the historian is used in a Claude project.

---

### P0 — Codify working contracts — CLOSED

Written `CLAUDE.md` at repo root, establishing:
- Three-tier work classification (Markery / Specialist / Project) with canonical paths
- Work routing rules — when to write to ROADMAP vs DEFERRED
- Review file lifecycle — create at root, archive when complete, remove from root
- Specialist boundary enforcement — pointer to each specialist's `Scope` section

Added `## Scope` section to each of the five specialist `identity.md` files. Each scope section enumerates owned paths (reads and writes) and forbidden paths, with an explicit out-of-scope routing rule: stop, add DEFERRED entry, halt.

---

### P1 — Fix historian persona stale content and session workflow — CLOSED

The historian persona and session workflow contain stale content from the Phase 7 schema migration and a subsequent CLI rename. Fix all classes before the historian is used in a Claude project.

**Stale schema content in `persona/README.md` and `persona/reference/markery-database.md`:**
1. **Table name**: `mark_case_status` was removed in Phase 7; replaced by `extended_marks`
2. **Hardcoded row counts**: `25,473 USPTO trademark filings` and `11,284 US patents in filing-system CPC classes (B42F, B42D)` are information-systems-project values, not tool values
3. **Old code path**: `src/markery/matching/` no longer exists; matchmaker is at `src/markery/specialist/matchmaker/`

**Stale command names in `persona/research-session.md`** *(S01-HI — critical: these produce command-not-found at the terminal)*:

| `research-session.md` (wrong) | Correct current command |
|---|---|
| `markery score-signals <project>` | `markery patent signals <project>` |
| `markery fetch-patents <project> --confirmed` | `markery patent fetch <project> --confirmed` |
| `markery fetch-patents --patent US1261167A` | `markery patent pull US1261167A` |

All three appear in prose sections and the quick-reference table (lines 97, 171, 177, 183, 248, 250).

**Missing instruction card** *(S03-HI)*:
- `instructions/prepare.md` — `markery historian prepare <project>` generates `BRIEF.md`; the expected first step in every research session; currently undocumented in any instruction card

**Side effect** *(S04-HI)*: The historian's request cards (`candidate-refresh.md`, `figure-fetch.md`, `patent-signals.md`, `trademark-enrich.md`) reference the stale command names as examples. Update these to match after fixing `research-session.md`.

**Deliverables:** Updated `historian/persona/README.md`, updated `historian/persona/reference/markery-database.md`, corrected `historian/persona/research-session.md` (3 command names + quick-reference table), new `historian/persona/instructions/prepare.md`, updated stale command references in the four request cards.

**Closes:** D008, S01-HI, S03-HI

---

### P2 — Flesh out patent specialist persona — CLOSED

Current stubs: `README.md`, `identity.md`, `instructions/build.md`, `reference/epo-ops.md`.

**New instruction cards:**
- `instructions/pull.md` — on-demand single patent fetch; when to use vs bulk build; citation chain as a discovery path
- `instructions/figures.md` — fetching and storing drawing figures; when the historian needs them; what to do when no figure is available
- `instructions/citations.md` — backward citation chain expansion; how it grows the corpus organically from confirmed pairs

**New reference docs:**
- `reference/cpc-classes.md` — CPC class system overview; how to identify the right classes for a research subject; how to read class codes; why pre-1940 assignments were retroactive

**`migrate-figures` subcommand** *(S02-P)*: Determined to be a one-time migration tool (one-time schema migration: disk PNGs → BLOB storage, completed). Deferred to D016 for eventual CLI removal.

**Closes:** D009 partial, S03-P partial

---

### P3 — Flesh out trademark specialist persona — CLOSED

Current stubs: `README.md`, `identity.md`, `instructions/build.md`, `instructions/enrich.md`, `reference/bulk-tables.md`.

**New instruction cards:**
- `instructions/entity-forward.md` — surfacing post-1939 extended marks for a named entity; how to use `markery trademark entity-forward`; when this matters for research
- `instructions/load-supplemental.md` — loading the on-demand tables (`events`, `foreign_app`) from CSV; when prosecution history or Madrid Protocol data is needed

**Reference expansion:**
- Expanded `reference/bulk-tables.md` to cover the `serial_no` type split (BIGINT vs VARCHAR) and the cross-layer cast pattern in more detail, with example queries

**Closes:** D009 partial, S02-TM partial; D018 added for remaining trademark instruction cards

---

### P4 — Flesh out matchmaker specialist persona and add queries module — CLOSED

Current stubs: `README.md`, `identity.md`, `instructions/generate.md`, `reference/scoring.md`.

**Added `queries.py` module** *(S01-MM)*: Extracted read-only functions into a new `queries.py`: entity lookup by ID and name variant, candidate list retrieval, pipeline state reads. Other specialists now have a stable pure-read interface to the entity registry.

**New instruction cards:**
- `instructions/entities.md` — adding a new entity to the registry; editing `entities.csv` and `variants.csv`; how source values affect matching; idempotent build
- `instructions/rescore.md` — when to run `markery match rescore` vs full regeneration; what signal enrichment does to the score; pipeline_state.json tracking
- `instructions/status.md` — reading `markery match status` output; pipeline_state.json fields; enriched_at and rescored_at timestamps

**Updated `instructions/generate.md`** *(S03-MM)*: Added `--full`, `--force`, minimum-score threshold behavior, `--resolve` flag.

**New reference docs:**
- `reference/uncertainty-band.md` — the 0.40–0.60 uncertainty band; signal enrichment; when to fetch abstracts vs goods descriptions; when to escalate to historian review
- `reference/entities-schema.md` — full CSV format for `entities.csv` and `variants.csv`; source values; entities.txt scope file

**Closes:** D009 partial, S01-MM, S02-MM, S03-MM; D019 added for queries.py deduplication cleanup

---

### P5 — Flesh out publisher specialist persona — CLOSED

Current stubs: `README.md`, `identity.md`, `instructions/build-site.md`, `reference/content-pipeline.md`.

**New instruction cards:**
- `instructions/enhance.md` — mark image enhancement workflow; when to enhance vs use raw TSDR images; batch vs single-mark enhancement; where enhanced images are stored and how the site builder picks them up
- `instructions/wikipedia.md` — Wikipedia drafting workflow; what content qualifies; neutral point of view requirements; how to use `markery wikipedia draft`; review before submission

**Reference expansion:**
- Expanded `reference/content-pipeline.md` to cover the figure resolution fallback chain (DB BLOB → figure_index at build time → absent = empty element) and how to diagnose missing figures

**Documented `publisher build` vs `site build` aliasing** *(S03-PB)*: Both call `build_site()`. `markery site build` is canonical. Note added to `instructions/build-site.md`.

**Closes:** D009 complete (all four specialists done), S02-PB, S03-PB

---

### P6 — Patent bulk CSV route: research and design — CLOSED

Source evaluation complete. PatentsView selected as the recommended route: direct TSV download, no API key, covers 1836+, CPC retroactive mapping, disambiguated assignees.

**Deliverables:**
1. Source evaluation: PatentsView ✅, Google Patents Public Data ❌ (BigQuery dependency), USPTO Bulk XML ❌ (complex parser)
2. `src/markery/specialist/patent/BULK_CSV.md` written: download process, schema mapping for all four `patents.duckdb` tables, `patent_no` construction rule (`US{number}{kind}`), command signature, DuckDB implementation notes
3. D007 updated in DEFERRED with full implementation spec

**Closes:** D007 (design phase); implementation remains D007 in DEFERRED

---

### P7 — Root documentation and codebase accuracy fixes — CLOSED

Quick-fix pass on root docs and non-specialist code identified in `MARKERY_REVIEW.md`.

**`CONTEXT.md`:** Added `CLAUDE.md` to Root File Responsibilities table; expanded match-review-essay project structure with `OBJECTIVES.md`, `BRIEF.md`, `entities.csv`, `variants.csv`, `seed_patents.json`, `matches/rejected.jsonl`, `matches/pipeline_state.json`, `references/`; corrected Historian credentials (removed Anthropic API reference).

**`DESIGN.md`:** Removed stale `RESEARCH.md` reference from opening sentence; added `rejected.jsonl` to Historian ownership row; added `CLAUDE.md` + `## Scope` paragraph to Agentic Architecture section.

**`SETUP.md`:** Disk space corrected from ~100 MB to ~50 MB.

**`README.md`:** Added missing CLI subcommands: `markery match rescore`, `markery historian prepare`, `markery patent signals`, `markery patent fetch --confirmed`, `markery publisher build`, `markery wikipedia draft`.

**`pyproject.toml`:** `duckdb>=0.9.0` → `duckdb>=1.0.0`.

**`tests/__pycache__/`:** Deleted ghost `test_score.cpython-312-pytest-9.0.3.pyc`.

**Closes:** G02, G03, G04, G05, G06, G07, G10, G11, G12, G14, G15

---

**Phase gate:** Historian persona is current with Phase 7 schema and session commands. Each of the four new specialist personas has at least three instruction cards and two reference documents. Matchmaker has a `queries.py`. Patent bulk CSV route has a written design. Root documentation and codebase accuracy issues from `MARKERY_REVIEW.md` resolved. D007, D008, D009 closed; S01-HI, S01-MM, S02-MM, S03-MM resolved. — PASSED
