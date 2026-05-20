# Markery Roadmap

Active and upcoming tool development. Items originate in `DEFERRED.md` and are promoted here when active. Completed phases are in `archive/`.

---

## Phase 8 — Specialist Completeness

**Goal:** All five specialists have accurate, complete personas. Key operations are covered by instruction cards. Reference material reflects the current schema. Deferred functional gap D007 (patent bulk CSV) has a clear implementation path.

The persona stubs created in this session (D009) are the starting point. The historian persona (D008) has stale content from the Phase 7 schema migration and must be fixed before the historian is used in a Claude project.

---

### P0 — Codify working contracts *(complete)*

Written `CLAUDE.md` at repo root, establishing:
- Three-tier work classification (Markery / Specialist / Project) with canonical paths
- Work routing rules — when to write to ROADMAP vs DEFERRED
- Review file lifecycle — create at root, archive when complete, remove from root
- Specialist boundary enforcement — pointer to each specialist's `Scope` section

Added `## Scope` section to each of the five specialist `identity.md` files. Each scope section enumerates owned paths (reads and writes) and forbidden paths, with an explicit out-of-scope routing rule: stop, add DEFERRED entry, halt.

---

### P1 — Fix historian persona stale content and session workflow *(D008, S01-HI, S03-HI)*

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

### P2 — Flesh out patent specialist persona *(D009 partial)*

Current stubs: `README.md`, `identity.md`, `instructions/build.md`, `reference/epo-ops.md`.

**New instruction cards:**
- `instructions/pull.md` — on-demand single patent fetch; when to use vs bulk build; citation chain as a discovery path
- `instructions/figures.md` — fetching and storing drawing figures; when the historian needs them; what to do when no figure is available
- `instructions/citations.md` — backward citation chain expansion; how it grows the corpus organically from confirmed pairs

**New reference docs:**
- `reference/cpc-classes.md` — CPC class system overview; how to identify the right classes for a research subject; how to read class codes; why pre-1940 assignments were retroactive

**`migrate-figures` subcommand** *(S02-P)*: `markery patent migrate-figures` is registered in the CLI and appears in the top-level docstring. It has no instruction card and no documentation. Determine whether it is a one-time migration tool (if so, gate it with an `--internal` flag or remove it from `--help` output) or a recurring operation (if so, add `instructions/migrate-figures.md`). Either way, it should not appear alongside regular operations without explanation.

---

### P3 — Flesh out trademark specialist persona *(D009 partial)*

Current stubs: `README.md`, `identity.md`, `instructions/build.md`, `instructions/enrich.md`, `reference/bulk-tables.md`.

**New instruction cards:**
- `instructions/entity-forward.md` — surfacing post-1939 extended marks for a named entity; how to use `markery trademark entity-forward`; when this matters for research
- `instructions/load-supplemental.md` — loading the on-demand tables (`events`, `foreign_app`) from CSV; when prosecution history or Madrid Protocol data is needed

**Reference expansion:**
- Expand `reference/bulk-tables.md` to cover the `serial_no` type split (BIGINT vs VARCHAR) and the cross-layer cast pattern in more detail, with example queries

---

### ~~P4 — Flesh out matchmaker specialist persona and add queries module~~ *(complete)*

~~Current stubs: `README.md`, `identity.md`, `instructions/generate.md`, `reference/scoring.md`.~~

~~**Add `queries.py` module** *(S01-MM — breaks three-surface model)*: Matchmaker is the only specialist without a `queries.py`. Database reads for entity lookup and candidate retrieval are embedded in `entities.py` and `link.py` alongside write operations. Extract the read-only functions into a new `queries.py`: entity lookup by ID and name variant, candidate list retrieval, pipeline state reads. This gives other specialists a stable pure-read interface to the entity registry without importing from write modules.~~

~~**New instruction cards:**~~
~~- `instructions/entities.md` — adding a new entity to the registry; editing `entities.csv` and `variants.csv`; how source values (`patent_assignee`, `trademark_owner`) affect matching; idempotent build~~
~~- `instructions/rescore.md` — when to run `markery match rescore` vs full regeneration; what signal enrichment does to the score; how pipeline_state.json tracks enrichment state *(S02-MM)*~~
~~- `instructions/status.md` — reading `markery match status` output; what `pipeline_state.json` fields mean; how to interpret enriched_at and rescored_at timestamps *(S02-MM)*~~

~~**Update `instructions/generate.md`** *(S03-MM)*: Current card covers the base invocation only. Add: `--full` flag (generate + signal enrichment in one step), `--force` flag (overwrite enriched candidates), and minimum-score threshold behavior.~~

~~**New reference docs:**~~
~~- `reference/uncertainty-band.md` — what the 0.40–0.60 uncertainty band means; how signal enrichment narrows it; when to fetch abstracts vs goods descriptions; when to escalate to historian review~~
~~- `reference/entities-schema.md` — full CSV format for `entities.csv` and `variants.csv`; column definitions; how `source` values map to database fields; example rows~~

---

### ~~P5 — Flesh out publisher specialist persona~~ *(complete)*

~~Current stubs: `README.md`, `identity.md`, `instructions/build-site.md`, `reference/content-pipeline.md`.~~

~~**New instruction cards:**~~
~~- `instructions/enhance.md` — mark image enhancement workflow; when to enhance vs use raw TSDR images; batch vs single-mark enhancement; where enhanced images are stored and how the site builder picks them up~~
~~- `instructions/wikipedia.md` — Wikipedia drafting workflow; what content qualifies; neutral point of view requirements; how to use `markery wikipedia draft`; review before submission~~

~~**Reference expansion:**~~
~~- Expand `reference/content-pipeline.md` to cover the figure resolution fallback chain (DB BLOB → on-disk PNG → placeholder) and how to diagnose missing figures~~

~~**Document `publisher build` vs `site build` aliasing** *(S03-PB)*: `markery publisher build <project>` and `markery site build <project>` both call `build_site()` through different entry points. Neither `build-site.md` nor any root doc explains that these are equivalent or which to prefer. Add a note to `instructions/build-site.md` clarifying the aliasing.~~

---

### P6 — Patent bulk CSV route: research and design *(D007)*

The SETUP.md stub documents the intended behavior but no implementation exists. This action produces a design, not working code.

**Deliverables:**
1. Identify the most practical bulk patent data source for Markery's use case: PatentsView (tab-separated, annual releases), Google Patents Public Data (BigQuery, requires export), USPTO bulk data (XML, complex parsing). Evaluate schema fit against `patents.duckdb` tables.
2. Write `src/markery/specialist/patent/BULK_CSV.md` documenting the chosen source, download process, schema mapping, and the planned `markery patent bulk-import` command signature.
3. Add a DEFERRED entry for the implementation once the design is settled.

**Closes:** D007 (design phase); implementation remains deferred until design is approved.

---

### P7 — Root documentation and codebase accuracy fixes *(MARKERY_REVIEW G02–G07, G10–G12, G14–G15)*

Quick-fix pass on root docs and non-specialist code identified in `MARKERY_REVIEW.md`. All items are small; the pass should complete in a single session.

**`CONTEXT.md`:**
- Add `CLAUDE.md` row to Root File Responsibilities table *(G03)*
- Add `entities.csv`, `variants.csv`, `seed_patents.json`, `matches/rejected.jsonl` to match-review-essay project structure table *(G04)*
- Add `BRIEF.md`, `OBJECTIVES.md`, `references/` to match-review-essay project structure table — these are committed project files defined in `config.py` *(G12)*
- Remove "Anthropic API (for essay drafting)" from Historian credentials — essay drafting is done through a Claude project persona, not Python SDK calls *(G10)*

**`DESIGN.md`:**
- Remove or rewrite opening sentence that references a root-level `RESEARCH.md` — no such file exists at root; `RESEARCH.md` is a project artifact *(G02)*
- Add `rejected.jsonl` to Historian row in Specialist Ownership Pattern table *(G05)*
- Add a note in the Agentic Architecture section on `CLAUDE.md` as the session-level enforcement contract and `## Scope` sections in `identity.md` as the per-specialist boundary *(G06)*

**`SETUP.md`:**
- Correct disk space estimate from ~100 MB to ~50 MB *(G07)*

**`README.md`:**
- Add missing subcommands to CLI section: `markery historian`, `markery publisher`, `markery wikipedia`, `markery patent signals`, `markery patent fetch <project> --confirmed` *(G11)*

**`pyproject.toml`:**
- Tighten `duckdb` lower bound from `>=0.9.0` to `>=1.0.0` *(G14)*

**`tests/__pycache__/`:**
- Delete ghost `test_score.cpython-312-pytest-9.0.3.pyc` *(G15)*

---

**Phase gate:** Historian persona is current with Phase 7 schema and session commands. Each of the four new specialist personas has at least three instruction cards and two reference documents. Matchmaker has a `queries.py`. Patent bulk CSV route has a written design. Root documentation and codebase accuracy issues from `MARKERY_REVIEW.md` resolved. D007, D008, D009 closed; S01-HI, S01-MM, S02-MM, S03-MM resolved.
