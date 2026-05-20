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
