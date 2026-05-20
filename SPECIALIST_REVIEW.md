# Specialist Codebase Gap Analysis

**Date:** 2026-05-20
**Scope:** `src/markery/specialist/` — all five specialists and orchestrator; cross-checked against `tests/specialist/` and each specialist's `persona/`

**Note:** This review also corrects one finding from `MARKERY_REVIEW.md`. G01 ("markery trademark verify-credentials does not exist") was wrong. `verify-credentials` is implemented in `trademark/cli.py` at line 138 and is routed correctly through the top-level CLI. The SETUP.md instruction is correct; G01 is closed.

---

## Cross-cutting Findings

### Three-surface model compliance

DESIGN.md commits to three surfaces per specialist: a **queries module** (pure DB reads, no side effects), a **build/pipeline module** (writes or transforms), and a **CLI module** (entry point). Four of five specialists comply:

| Specialist | queries.py | build/pipeline module | CLI |
|---|---|---|---|
| PATENT | ✅ queries.py | ✅ build.py, fetch.py, signals.py, figures.py | ✅ cli.py |
| TRADEMARK | ✅ queries.py | ✅ build.py, enrich.py, fetch.py | ✅ cli.py |
| MATCHMAKER | ❌ absent | ✅ entities.py, link.py, pipeline.py, score.py | ✅ cli.py |
| HISTORIAN | ✅ queries.py | ✅ prepare.py, review.py | ✅ cli.py |
| PUBLISHER | ✅ queries.py | ✅ build.py, render.py | ✅ cli.py |

MATCHMAKER is the exception and is the only specialist that other agents cannot query through a stable pure-read interface. Cross-specialist reads that need entity or candidate data currently go through link.py or pipeline.py, which also write. See S01 below.

### Instruction card coverage

Instruction cards in `persona/instructions/` exist for 9 of the ~30 defined CLI subcommands across all specialists. This gap is the core of D009 and is mapped per specialist below. The Phase 8 roadmap (P2–P5) addresses the highest-priority cards; the review notes which are planned and which are not.

### Build module test coverage

No specialist has tests for its primary build module. The modules that perform bulk data ingestion or site generation — the most operationally consequential code in each specialist — are untested at the unit level. Client and queries modules have reasonable coverage; the orchestration layer above them does not.

---

## PATENT Specialist

**Python modules:** `build.py`, `cli.py`, `epo_client.py`, `fetch.py`, `figures.py`, `queries.py`, `signals.py`

**CLI subcommands:** `build`, `fetch`, `figures`, `verify-credentials`, `signals`, `pull`, `citations`, `migrate-figures`

**Tests:** `test_epo_client.py`, `test_fetch_6d.py`, `test_figures.py`, `test_queries.py`

**Instruction cards:** `build.md`

**Reference docs:** `epo-ops.md`

---

**S01-P · Missing tests for `build.py` and `signals.py`**
`build.py` (EPO OPS fetch loop, 5-year windowing, resume state) and `signals.py` (text signal enrichment of candidates) have no test files. `test_fetch_6d.py` tests a specific Phase 6D fix in `fetch.py`, not the module broadly. These are the modules most likely to break quietly on schema or API changes.

**S02-P · `migrate-figures` subcommand is undocumented**
`migrate-figures` is registered in the patent CLI and appears in the top-level `cli.py` docstring. It has no instruction card, no mention in SETUP.md or any root doc, and no test. It appears to be a one-time migration tool from an earlier figure storage schema. Either document it or gate it behind an internal flag so it does not appear in `--help` output alongside regular operations.

**S03-P · Instruction cards absent for 6 subcommands (partially planned)**
`pull`, `figures`, `citations` — planned in ROADMAP P2. `fetch`, `signals`, `verify-credentials` — not in the current plan. `fetch` and `signals` are both used in active research sessions and are referenced (as stale names) in `research-session.md`.

---

## TRADEMARK Specialist

**Python modules:** `build.py`, `cli.py`, `enrich.py`, `fetch.py`, `queries.py`, `tsdr_client.py`

**CLI subcommands:** `build`, `enrich`, `enrich-project`, `verify-credentials`, `status`, `load-events`, `load-foreign`, `fetch`, `entity-forward`

**Tests:** `test_enrich.py`, `test_events_d04d05.py`, `test_fetch_6d.py`, `test_queries.py`, `test_tsdr_client.py`

**Instruction cards:** `build.md`, `enrich.md`

**Reference docs:** `bulk-tables.md`

---

**S01-TM · Missing test for `build.py`**
`build.py` performs the USPTO bulk CSV load — parsing ~5M rows across multiple companion tables with a date filter. No test exists for it. Given the `serial_no` BIGINT/VARCHAR type-split (documented in `identity.md` and `bulk-tables.md` as a correctness constraint), the absence of tests for the bulk load path is a latent correctness risk.

**S02-TM · Instruction cards absent for 7 subcommands (partially planned)**
`entity-forward` — planned in ROADMAP P3. `load-events`, `load-foreign` — planned in ROADMAP P3 partial. `enrich-project`, `fetch`, `status`, `verify-credentials` — not in the current plan. The distinction between `enrich` (per-mark) and `enrich-project` (batch for a project's confirmed/candidates) is particularly likely to confuse; both exist but only `enrich.md` covers one of them.

---

## MATCHMAKER Specialist

**Python modules:** `cli.py`, `entities.py`, `link.py`, `pipeline.py`, `score.py` — **no `queries.py`**

**CLI subcommands (`markery match`):** `<project>`, `rescore`, `status`

**CLI subcommands (`markery matchmaker`):** `build`, `list`, `status`

**Tests:** `test_entities.py`, `test_link.py`, `test_link_6c.py`, `test_pipeline.py`, `test_score.py`, `test_score_6c.py`

**Instruction cards:** `generate.md`

**Reference docs:** `scoring.md`

---

**S01-MM · No `queries.py` — three-surface model broken**
Every other specialist has a `queries.py` that exposes pure-read functions for cross-specialist use (via DuckDB ATTACH or direct connection). The matchmaker has no equivalent. Database reads for entity lookups and candidate scoring are embedded in `entities.py` and `link.py` alongside write operations. When another specialist (or the orchestrator) needs entity registry data, it either calls the matchmaker CLI (a subprocess, not an API) or imports from `link.py` (a write module). Add a `queries.py` that extracts the read-only functions: entity lookup, name variant resolution, candidate list retrieval.

**S02-MM · `rescore` and `match status` have no persona coverage**
`markery match rescore` (re-apply scores after signal enrichment without regenerating) and `markery match status` (read pipeline_state.json) are both useful mid-session operations. Neither appears in `generate.md` or any other instruction card. A researcher using the historian persona would not know these options exist.

**S03-MM · `generate.md` does not mention `--full`, `--force`, or minimum-score flags**
The instruction card covers the base `markery match <project>` invocation. The `--full` flag (generate + signal enrichment in one step) and `--force` (overwrite enriched candidates) are not mentioned. These flags prevent common researcher mistakes (running signals separately, or aborting on an enriched file).

---

## HISTORIAN Specialist

**Python modules:** `cli.py`, `prepare.py`, `queries.py`, `review.py`, `status.py`

**CLI subcommands:** `prepare <project>` (via `markery historian`); `markery review <project>`; `markery status` — all routed through the top-level CLI

**Tests:** `test_prepare.py`, `test_queries.py`, `test_review.py`, `test_status.py`

**Instruction cards:** `candidate-refresh.md`, `figure-fetch.md`, `patent-signals.md`, `trademark-enrich.md`

**Reference docs:** `historical-context.md`, `image-enhancement.md`, `mark-drawing-codes.md`, `markery-database.md`, `project-types.md`, `status-codes.md`

---

**S01-HI · `research-session.md` contains three stale command names (critical)**
The session checklist is used directly during active research sessions. Three commands it lists no longer exist under those names:

| `research-session.md` command | Correct current command |
|---|---|
| `markery score-signals <project>` | `markery patent signals <project>` |
| `markery fetch-patents <project> --confirmed` | `markery patent fetch <project> --confirmed` |
| `markery fetch-patents --patent US1261167A` | `markery patent pull US1261167A` |

All three appear in both the prose sections and the quick-reference table (lines 97, 171, 177, 183, 248, 250). A researcher following the checklist will get command-not-found errors. This is D008 partial — the stale table structure is the documented issue, but these command names are a separate, more immediate correctness problem.

**S02-HI · Historian persona `README.md` and `markery-database.md` are stale (D008)**
Three classes of stale content documented in ROADMAP P1:
1. `README.md` references `mark_case_status` (removed in Phase 7; replaced by `extended_marks`)
2. `README.md` hardcodes information-systems row counts (25,473 marks, 11,284 patents, B42F/B42D classes)
3. `README.md` references `src/markery/matching/` (does not exist; matchmaker lives at `src/markery/specialist/matchmaker/`)

`markery-database.md` likely carries similar staleness for the schema tables. Addressed by ROADMAP P1.

**S03-HI · `markery historian prepare` has no instruction card**
`prepare` generates `BRIEF.md` — the machine-readable project state document that the historian reads before each session. It is the expected first step in a research session but is not mentioned in `research-session.md` or any instruction card. A historian agent would not know to run it or what it produces.

**S04-HI · Historian instruction cards are request cards, not command cards**
`candidate-refresh.md`, `figure-fetch.md`, `patent-signals.md`, `trademark-enrich.md` are correctly structured as request-emission cards — they tell the historian persona when and how to ask another specialist to perform an operation. This is appropriate for a persona that does not itself run those commands. The gap is that the cards reference CLI commands by name (e.g., `markery match information-systems`) and some of those names are stale (S01-HI). The cards themselves are not mislabeled; they are stale as a side effect of S01-HI.

---

## PUBLISHER Specialist

**Python modules:** `build.py`, `cli.py`, `queries.py`, `render.py`; submodules `image_enhancement/` (own CLI), `wikipedia/` (own CLI + `wikitext.py`, `api.py`)

**CLI subcommands:** `markery publisher build <project>`; `markery site build <project>` (alias); `markery enhance enhance|batch|gallery`; `markery wikipedia draft|submit`

**Tests:** `test_queries.py`, `test_render.py`, `test_render_6b.py`, `test_render_d02d03.py`; `wikipedia/test_wikitext.py`

**Instruction cards:** `build-site.md`

**Reference docs:** `content-pipeline.md`

---

**S01-PB · Missing test for `build.py`**
`build.py` is the site generation orchestrator — it reads `confirmed.jsonl`, resolves figure references, writes HTML files, manages asset paths. `render.py` (the per-page rendering layer) is tested; `build.py` (the outer loop that calls it) is not. A broken figure resolution path or asset-path miscalculation would not be caught by the current test suite.

**S02-PB · `image_enhancement` and `wikipedia` have no instruction cards (planned)**
Three subcommands with no persona coverage: `enhance` (single-mark super-resolution), `batch` (SQL-condition batch enhancement), `wikipedia draft|submit`. All three are planned in ROADMAP P5 (`enhance.md`, `wikipedia.md`). The wikipedia workflow in particular — neutral point of view requirements, secondary-source grounding, review before submission — is complex enough that the absence of an instruction card is a real risk to output quality.

**S03-PB · `markery publisher build` vs `markery site build` aliasing is undocumented**
Both commands exist and both route to `build_site()`. The difference in entry point (`publisher_main()` vs the inline `cmd_site()` in the top-level CLI) is invisible to users and to the historian persona. A persona consulting `build-site.md` would not know that `markery publisher build` and `markery site build` are equivalent, or which to prefer.

---

## Orchestrator

**File:** `src/markery/specialist/orchestrator.py`

**Functions:** `fetch_patent()`, `fetch_patent_citations()`, `fetch_trademark()`, `entity_forward_report()`, `enrich_signal_fields()`

**Tests:** `test_orchestrator.py` — 2 tests, both for `enrich_signal_fields` only

---

**S01-OR · Four of five orchestrator functions have no tests**
`enrich_signal_fields` is tested (2 tests). `fetch_patent`, `fetch_patent_citations`, `fetch_trademark`, and `entity_forward_report` are untested. The orchestrator is the trust boundary for cross-specialist calls — a broken dispatch here would silently fail to call the right specialist. The existing 2 tests confirm the pattern works; the remaining 4 functions should have at least smoke-test coverage.

---

## Summary

| ID | Specialist | Severity | Finding |
|---|---|---|---|
| S01-HI | HISTORIAN | Critical | `research-session.md`: 3 stale command names (score-signals, fetch-patents, fetch-patents --patent) |
| S01-MM | MATCHMAKER | Critical | No `queries.py` — three-surface model broken; no stable read-only API |
| S01-P | PATENT | Incomplete | No tests for `build.py` or `signals.py` |
| S01-TM | TRADEMARK | Incomplete | No test for `build.py` |
| S01-PB | PUBLISHER | Incomplete | No test for `build.py` |
| S01-OR | ORCHESTRATOR | Incomplete | 4 of 5 orchestrator functions untested |
| S02-HI | HISTORIAN | Incomplete | Persona README + markery-database.md stale (D008 / ROADMAP P1) |
| S02-MM | MATCHMAKER | Incomplete | `rescore` and `match status` have no persona coverage |
| S02-P | PATENT | Incomplete | `migrate-figures` undocumented; should be gated or removed from --help |
| S02-PB | PUBLISHER | Incomplete | `enhance` and `wikipedia` have no instruction cards (ROADMAP P5) |
| S02-TM | TRADEMARK | Incomplete | 7 subcommands lack instruction cards (ROADMAP P3 covers 3) |
| S03-HI | HISTORIAN | Incomplete | `historian prepare` has no instruction card |
| S03-MM | MATCHMAKER | Incomplete | `generate.md` missing `--full`, `--force`, minimum-score flag documentation |
| S03-P | PATENT | Incomplete | 6 subcommands lack instruction cards (ROADMAP P2 covers 3) |
| S03-PB | PUBLISHER | Incomplete | `publisher build` vs `site build` aliasing undocumented |
| S04-HI | HISTORIAN | Low | Instruction request cards reference stale command names (side effect of S01-HI) |

---

## Relationship to ROADMAP Phase 8

| ROADMAP item | Gaps it closes |
|---|---|
| P1 — Fix historian persona | S02-HI (stale schema); **does not cover S01-HI (stale commands)** — those should be fixed in P1 |
| P2 — Flesh out patent persona | S03-P partial (3 of 6 instruction cards) |
| P3 — Flesh out trademark persona | S02-TM partial (3 of 7 instruction cards) |
| P4 — Flesh out matchmaker persona | S02-MM, S03-MM; **does not address S01-MM (missing queries.py)** |
| P5 — Flesh out publisher persona | S02-PB |
| Not planned | S01-HI (stale commands — **fix in P1**), S01-MM (queries.py), S01/S01-OR (build module tests), S02-P (migrate-figures), S03-HI (prepare card), S03-PB (alias) |

---

## Phase 8 Work Log

### P0 — Codify working contracts *(2026-05-20 — complete)*

**Deliverables confirmed:**
- `CLAUDE.md` written at repo root — four sections: three-tier work classification with path tables, work routing rules (ROADMAP vs DEFERRED triggers), review file lifecycle (create → use → archive → remove from root), specialist boundary enforcement with pointers to each `identity.md`
- `## Scope` section added to all five specialist `identity.md` files — each enumerates owned reads, owned writes, and forbidden paths by name, with a uniform out-of-scope routing rule: stop, add DEFERRED entry, halt

**Verification:** All six files confirmed present. `grep -l "## Scope"` returns all five `identity.md` paths. `CLAUDE.md` exists at repo root.

**Commit:** `a18e477` — "Phase 8 P0: add CLAUDE.md and Scope sections to all five specialist identity files"

**Status:** Complete. Closed in ROADMAP.

---

### P5 — Flesh out publisher specialist persona *(2026-05-20 — complete)*

**Deliverables confirmed:**

`instructions/enhance.md` (new): `markery enhance enhance <serial_no>` (single) and `markery enhance batch "<where>"` (batch); when to enhance vs use raw TSDR images; `--force` flag; gallery building from enhanced PNGs or raw DB images; how the site builder picks up enhanced images (must be in `site/images/marks/`); GPU/CPU requirements and model weight download.

`instructions/wikipedia.md` (new): Three-step workflow — `markery wikipedia draft <project> <slug>` (generates from match essay) → review and edit `<slug>.wiki` → `markery wikipedia submit <project> <slug>` (shows diff, prompts before POST); `--title` and `--summary` flags; Wikipedia content policy requirements (no original research, NPOV, verifiability, notability); when not to draft (content that cannot meet policy standards).

`reference/content-pipeline.md` expanded: Figure fallback chain rewritten with technical accuracy — `[[figure:patent_no]]` resolves via `figure_index` built from `patent_figures` BLOBs at build time; if BLOB absent, the `[[figure:]]` tag renders as nothing (no silent on-disk fallback for inline references); diagnostic steps for missing figures; language guidance for permanently unavailable figures.

`instructions/build-site.md` updated (S03-PB): Added section documenting that `markery site build` and `markery publisher build` are fully equivalent (both call `build_site()` in `publisher/build.py`); canonical form is `markery site build`.

`README.md` updated: reference table expanded to include all new instruction and reference files.

**Commit:** `e97bc27` — "Phase 8 P5: flesh out publisher specialist persona (enhance, wikipedia, content-pipeline expansion, site-build aliasing)"

**Closes:** P5 (D009 complete — all four specialists done, S03-PB)

**Status:** Complete. Closed in ROADMAP.

---

### Test harness run *(2026-05-20 — after P4)*

`307 passed in 15.24s` — full suite green after P4 changes (queries.py, generate.md, README.md, ROADMAP.md, DEFERRED.md). No regressions.

---

### P4 — Flesh out matchmaker specialist persona and add queries module *(2026-05-20 — complete)*

**Deliverables confirmed:**

`queries.py` (new — closes S01-MM): Read-only module over `entities.duckdb`. Exports `connect()`, `get_entity()`, `find_entity()`, `list_entities()`, `list_variants()`, `read_candidates()`, `read_confirmed()`, `read_rejected()`, `read_pipeline_state()`. Other specialists can now import entity reads from a pure-read interface rather than from `entities.py` or `link.py` (which mix reads with writes). Restores the three-surface model for matchmaker.

`instructions/entities.md` (new): Adding a new entity — edit `entities.csv` and `variants.csv`, run `markery matchmaker build`, confirm with `markery matchmaker list`; how `source` values (`patent_assignee`, `trademark_owner`) map to database columns; exact-match requirement with guidance on finding the right strings; how to remove a variant (requires clean rebuild); idempotent build behavior.

`instructions/rescore.md` (new — closes S02-MM): When to rescore vs regenerate — rescore after signal enrichment, regenerate to add new pairs; `--force` requirement to regenerate over enriched candidates; semantic bonus component breakdown (title_name_hit +0.20, abstract_name_hit +0.10, goods_title_overlap +0.10, goods_abstract_overlap +0.05, cap 0.25); how to check rescore state via `markery match status`.

`instructions/status.md` (new — closes S02-MM): Reading `markery match status <project>` output — pipeline timestamps (generated_at, enriched_at, rescored_at), score percentiles (P50/P90), review counts (confirmed, rejected, unreviewed); `markery matchmaker status` for entity registry row counts.

`instructions/generate.md` (updated — closes S03-MM): Added `--full` (generate + enrich + rescore in one step), `--force` (overwrite enriched candidates with warning), `--min-score` (default 0.10; tradeoff between coverage and review volume), `--resolve` (report uncertainty band and missing data); link to `instructions/rescore.md` for rescore vs regenerate guidance.

`reference/uncertainty-band.md` (new): Band definition (0.40–0.60); how temporal-only and class-only pairs land in the band; signal enrichment components and their shift potential; when to fetch abstracts (`markery patent signals`) vs goods descriptions (`markery trademark enrich-project`); when to escalate to historian review.

`reference/entities-schema.md` (new): Full CSV format for `entities.csv` (entity_id, canonical_name, entity_type, industry) and `variants.csv` (entity_id, variant_name, source); source value table; SQL patterns for finding the right variant strings in patent and trademark databases; `entities.txt` project scope file format.

`README.md` updated: reference table expanded to include all new instruction and reference files.

**Commit:** `1ce0d45` — "Phase 8 P4: add matchmaker queries.py and flesh out persona (entities, rescore, status, generate update, uncertainty-band, entities-schema)"

**Closes:** P4 (D009 partial, S01-MM, S02-MM, S03-MM)

**Status:** Complete. Closed in ROADMAP.

---

### P3 — Flesh out trademark specialist persona *(2026-05-20 — complete)*

**Deliverables confirmed:**

`instructions/entity-forward.md` (new): `markery trademark entity-forward <entity_name> [--after-year YEAR]` — when to use (brand continuity, company survival, scope expansion); how matching works via entity name variants in `entities.duckdb`; critical constraint that only TSDR-fetched marks in `extended_marks` appear (not bulk-only marks); fetch-then-query pattern for marks not yet in extended_marks.

`instructions/load-supplemental.md` (new): Both on-demand tables in one card — `events` (prosecution history via `markery trademark load-events`) with full column schema and when to use (prosecution timeline, office action gaps, abandonment analysis); `foreign_app` (Madrid Protocol via `markery trademark load-foreign`) with full column schema and when to use (foreign priority claims, international brand reach); notes on drop-and-recreate behavior and `case_file` filtering.

`reference/bulk-tables.md` expanded: On-demand table section rewritten to include full column schemas for `events` and `foreign_app`; new "serial_no Type Split" section with the rule stated explicitly (`CAST(cf.serial_no AS VARCHAR)`) and four concrete cross-layer query patterns demonstrating when to cast and when not to.

`README.md` updated: reference table expanded to include all new instruction and reference files.

**DEFERRED updated:** D018 added — trademark persona instruction cards for `fetch`, `status`, and `verify-credentials` (next persona completeness pass after Phase 8).

**Commit:** `37be307` — "Phase 8 P3: flesh out trademark specialist persona (entity-forward, load-supplemental, bulk-tables expansion); add D018"

**Closes:** P3 (D009 partial)

**Status:** Complete. Closed in ROADMAP.

---

### P2 — Flesh out patent specialist persona *(2026-05-20 — complete)*

**Deliverables confirmed:**

`instructions/pull.md` (new): `markery patent pull <patent_no>` — when to use vs bulk build, upsert behavior, figures not included, relationship to citation chain expansion, post-pull candidate regeneration.

`instructions/figures.md` (new): Both figure commands covered — `markery patent figures <patent_no>` (single) and `markery patent fetch <project> --confirmed` (batch); check BRIEF.md first; `patent_figures` table schema; post-fetch prepare + site rebuild; no-figure fallback language for essays.

`instructions/citations.md` (new): `markery patent citations <patent_no>` — confirm → pull → cite → match pattern; one-level backward expansion; pre-1940 coverage caveats; cross-entity citation filtering.

`reference/cpc-classes.md` (new): CPC code structure and how to read it; 4-character subclass as the `--classes` argument; all seven classes used in the information-systems project with descriptions; how to identify classes for a new subject; pre-1940 retroactive classification caveats and why the scoring model uses binary class signals.

`README.md` updated: reference table expanded to include all four new files.

**S02-P (migrate-figures) resolved:** CLI docstring and parser already label the command "One-time migration: disk PNGs → BLOB storage". Migration confirmed complete for the information-systems project. Added D016 (remove `migrate-figures` from patent CLI) and D017 (instruction cards for `signals`, `fetch`, `verify-credentials`) to DEFERRED.

**Commit:** `c09c9f3` — "Phase 8 P2: flesh out patent specialist persona (pull, figures, citations, cpc-classes); add D016-D017"

**Closes:** P2 (D009 partial), S02-P

**Status:** Complete. Closed in ROADMAP.

---

### P1 — Fix historian persona stale content and session workflow *(2026-05-20 — complete)*

**Deliverables confirmed:**

`historian/persona/README.md`:
- `mark_case_status` → `extended_marks` in Databases table
- Row counts removed; replaced with "date window set per project" / "scope set per project"
- `src/markery/matching/` → `src/markery/specialist/matchmaker/`

`historian/persona/reference/markery-database.md`:
- `serial_no` type corrected from VARCHAR to BIGINT in all five bulk tables (`case_file`, `owner`, `statement`, `classification`, `design_search`)
- `extended_marks` table added with full column schema and cross-layer cast example
- Opening sentence: hardcoded row count removed
- Closing notes: "serial_no is VARCHAR throughout" replaced with the BIGINT/VARCHAR split explanation

`historian/persona/research-session.md`:
- Step 0 expanded: `markery historian prepare <project>` added as the first command in every session
- Step 1 (add entity): procedure rewritten — `entities.csv` / `variants.csv` + `markery matchmaker build --data-dir projects/<project>` + `markery matchmaker list`; old `build.py` editing procedure removed
- Step 3: `markery score-signals <project>` → `markery patent signals <project>`
- Step 7: `markery fetch-patents <project> --confirmed` → `markery patent fetch <project> --confirmed`; `markery fetch-patents --patent US1261167A` → `markery patent pull US1261167A`
- End of session: "Update `CONTEXT.md` → `## Next Action`" → "Update the project's `STATUS.md`"
- Quick-reference table: all stale commands corrected; `prepare` and `patent pull` added

`historian/persona/instructions/prepare.md` (new):
- Documents `markery historian prepare <project>`; explains BRIEF.md sections and how to read them; includes human-readable and structured request forms

`historian/persona/instructions/trademark-enrich.md`:
- `markery trademark enrich <project>` → `markery trademark enrich-project <project>`
- `mark_case_status` → `extended_marks` in prose, table reference, and SQL example

**Commit:** `0521246` — "Phase 8 P1: fix historian persona stale content and session workflow"

**Closes:** D008, S01-HI, S02-HI, S03-HI, S04-HI (side effect)

**Status:** Complete. Closed in ROADMAP.
