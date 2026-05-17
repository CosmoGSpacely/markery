# Markery Roadmap

Research design and phase plan for the Markery project. Current state and metrics live in `STATUS.md`; deferred items live in `DEFERRED.md`.

---

## What Markery Is

Markery is a research tool for studying American commercial history through the combined USPTO trademark and patent record. The project cross-references trademark registrations with patent filings for the same companies and time periods, producing documented patent-trademark pairs that reveal the commercial lifecycle of early 20th-century technologies.

The core hypothesis: the trademark record establishes what a company called its product and when it entered commerce; the patent record establishes what was technically novel. Neither source alone shows the full picture. No existing work systematically cross-references them for the 1900–1939 period.

**Primary research focus:** pre-computer information systems — the filing cabinets, card indexes, visible record systems, tabulating machines, and phonetic coding schemes that American businesses used to organize knowledge before the digital era.

**Scope boundary:** The core tool handles USPTO/EPO data ingestion, candidate generation, and project management. Image enhancement, patent document handling, and the historian AI specialist are extensions — useful but separate from the core research workflow.

---

## Phase 1 — Working Research Tool *(largely complete)*

**Goal:** End-to-end research session is repeatable — a new entity can be added, candidates generated, a pair confirmed, and an essay written without consulting raw API docs.

| Stage | What was built | Skill developed |
|---|---|---|
| TSDR client | `tsdr_client.py` — case status JSON + raw mark image fetch | External API integration, rate limiting |
| Trademark database | `trademarks.duckdb` — 25,473 case files, 1900–1939 | DuckDB database design, bulk CSV import |
| Historian specialist | `tools/historian/` — Claude specialist persona | Specialist agent design, system prompt engineering |
| Image pipeline | `tools/image_enhancement/` — Real-ESRGAN 4× upscale + SVG vectorization | ML inference pipeline, image processing |
| Patent database | `patents.duckdb` — 11,284 EPO patents (B42F, B42D), 1900–1939 | EPO OPS API, CQL queries, OAuth2 |
| Entity registry | `entities.duckdb` — canonical company registry with name variants | Entity resolution, cross-database ATTACH queries |
| Match pipeline | `src/markery/matching/` — scored patent-trademark candidate pairs | Scoring model design, research workflow |
| Projects tree | `projects/information-systems/` — first research project | Research methodology, primary source curation |

**Phase gate:** Phase 1 closes when the operations workflow is documented as a single runnable checklist (in progress — see `STATUS.md`).

### Phase 1 Close Plan

All infrastructure is built and verified (see STATUS.md infrastructure ledger). The single open gate item is the operations checklist. Close in three steps:

**Step 1 — Write the operations workflow document**

Create `docs/workflows/research-session.md` (or `WORKFLOW.md` at root until Phase 2 reorganization moves it). The document must be a literal runnable checklist — commands, not descriptions — covering:

1. *Environment* — activate `.venv`, confirm `.env` has `EPO_CONSUMER_KEY`, `EPO_CONSUMER_SECRET`, `USPTO_API_KEY`; verify DuckDB files present at expected paths.
2. *Add an entity* — `python build_entities_db.py` with a new company; confirm it appears in `entities.duckdb` with expected name variants.
3. *Generate candidates* — `python -m match information-systems`; confirm `candidates.jsonl` updates and row count is plausible.
4. *Review candidates* — `scripts/review`; step through the interactive reviewer, fetch patent docs, inspect text signals and figures.
5. *Confirm a pair* — promote a candidate to `confirmed.jsonl`; verify the entry structure matches existing confirmed entries.
6. *Write an essay* — open `tools/historian/` in a Claude session; produce a draft essay and save to `projects/information-systems/content/`.
7. *Enhance mark image* — `scripts/enhance <serial>`; confirm 4× PNG output; optionally run SVG vectorization.
8. *Build gallery* — run gallery generator against project output folder; open `gallery.html` and verify images render.

**Step 2 — Dry-run the checklist against current code**

Execute each step from a clean shell (`.venv` activated, no previous process state) and note any command that fails or requires undocumented knowledge. Fix any gaps before marking complete.

**Step 3 — Update STATUS.md**

Check off the operations checklist gate item and set Phase to "1 — Complete / entering Phase 2 reorganization".

---

## Phase 2 — Codebase Reorganization *(next)*

**Goal:** Restore structural clarity so that the core research workflow, extensions, and AI tooling each have a home that matches their purpose. Eliminate the flat module layout at root, consolidate scattered entry points into a single CLI, and move non-code assets out of the source tree.

### Motivation

The project review (`MARKERY_REVIEW.md`) identified three structural problems that will compound as the corpus grows:
- Flat root layout mixes core modules (`match/`), extensions (`image_tools/`, `patent_docs/`), and AI agents (`commerce-and-technology-historian/`) with no hierarchy.
- No single entry point: operations are spread across `scripts/`, `python -m match`, and direct module invocation.
- Documentation scattered at root with no organization by audience or purpose.

### Target directory structure

```
markery/
├── src/markery/              # Core installable package
│   ├── db/                   # build_*_db.py, tsdr_client.py → here
│   ├── matching/             # match/ contents → here
│   └── cli.py                # Unified markery CLI entry point
├── tools/                    # Extension modules (optional, not core)
│   ├── image_enhancement/    # image_tools/ → here
│   ├── patent_docs/          # patent_docs/ → here
│   ├── trademark_docs/       # new — non-image mark retrieval (see Phase 3)
│   └── historian/            # commerce-and-technology-historian/ → here
├── projects/                 # Research projects only (unchanged)
│   ├── information-systems/
│   └── monthly-image-review/
├── data/                     # DuckDB files and raw CSV (gitignored binaries)
│   ├── trademarks.duckdb
│   ├── patents.duckdb
│   ├── entities.duckdb
│   └── csv/
├── docs/                     # All documentation
│   ├── workflows/            # Step-by-step operational guides
│   ├── reference/            # EPO.md, TSDR.md, DESIGN.md → here
│   └── contributing/         # Extension development guide
├── scripts/                  # Thin shell wrappers only (minimize)
└── tests/                    # Test suite (unchanged structure)
```

### Migration steps

1. **Create `src/markery/` package** — move `match/` → `src/markery/matching/`; extract database builders and `tsdr_client.py` into `src/markery/db/`; update all imports.
2. **Create `tools/` tree** — move `image_tools/` → `tools/image_enhancement/`; move `patent_docs/` → `tools/patent_docs/`; move `commerce-and-technology-historian/` → `tools/historian/`.
3. **Build unified CLI** — create `src/markery/cli.py` with subcommands replacing the current `scripts/` entry points:
   - `markery match <project>` — replaces `scripts/run-match`
   - `markery review <project>` — replaces `scripts/review`
   - `markery enhance <serial>` — replaces `scripts/enhance`
   - `markery fetch-patents <project>` — replaces `scripts/fetch-patent-docs`
   - `markery fetch-trademarks <project>` — new; implemented in Phase 3 (`tools/trademark_docs/`)
   - `markery status` — replaces `scripts/check-status`
4. **Move databases to `data/`** — update all hardcoded paths; verify `.gitignore` covers binaries.
5. **Consolidate documentation** — move `EPO.md`, `TSDR.md`, `DESIGN.md`, `SETUP.md` → `docs/reference/`; create `docs/workflows/research-session.md` as the single runnable checklist (closes Phase 1 gate).
6. **Update `pyproject.toml`** — define `[project.scripts]` entry points for `markery` and `markery-tools`.
7. **Remove deprecated entry points** — delete `scripts/` wrappers once CLI subcommands are verified; add deprecation notices if any external references exist.

**Phase gate:** `src/markery/` is the canonical package; `markery match information-systems` runs end-to-end from the new layout; no Python files remain at root except `pyproject.toml` / `setup.cfg`.

---

## Phase 3 — Corpus and Match Quality *(planned)*

**Goal:** `information-systems` project has 5 confirmed entries with essays; site builds without placeholder pages.

### Prerequisites (unblock before corpus work)

These gaps were identified during the Phase 2 → Phase 3 handoff. Address before the site builder is run for the first time.

- ~~**R1** — Fix `own_id = 1` in `tools/site_builder/queries.py`~~ ✅
- ~~**R2** — Add `markery site build <project>` to CLI~~ ✅
- ~~**R3** — Resolve `kardex.md` orphan; add Rand Kardex Bureau entity variants~~ ✅
- ~~**R4** — Fix entity slug for Yawman & Erbe (`yawman-&-erbe` → `yawman-and-erbe`)~~ ✅

### Stages

1. **Remaining CPC classes** — fetch B41J (typewriters), B41L (duplicating), G06C (calculating machines), G06K (data recognition), G09F (display devices) into `patents.duckdb`. Deferred as D001 until typewriter/calculator entries are needed. Command: `python build_patents_db.py --classes B41J B41L G06C G06K G09F --resume`.

2. **New entities** — add Smead Mfg. (SMEAD'S TELL VISION SYSTEM, 1938), Library Bureau, and others identified through the candidate list. Procedure: `README.md` → entities section.

3. **Trademark document retrieval** — build `tools/trademark_docs/` to fetch non-image mark content from TSDR for confirmed and candidate pairs in a project. The TSDR client already fetches case status and mark images; this extends it to retrieve goods-and-services descriptions, specimen of use text, and prosecution correspondence for a given serial. This text enriches the historian's analysis for word marks and text-heavy filings where the goods/services description is the primary source for what the company was actually selling under that mark. Entry point: `markery fetch-trademarks <project>`, which writes retrieved content alongside the existing `candidates.jsonl` / `confirmed.jsonl` in the project matches directory.

4. **Scoring refinement** — address company-name mark false positives (D006). A heuristic that flags marks whose `mark_element` matches an entity canonical name would filter most without changing the scoring formula.

5. **Confirmed entries and content** — reach 5 confirmed pairs with essays. Priority order:

   | Content file | Status | Notes |
   |---|---|---|
   | `content/soundex.md` | ✅ Written | Covers both SOUNDEX pairs (Russell + Odell patents) |
   | `content/variadex.md` | ✗ Missing | Single confirmed pair; schema-compliant essay needed |
   | `content/soundex-quick-as-a-flash.md` | ✗ Missing | Odell patent + slogan mark; brief essay |
   | `content/kardex.md` | ⚠ Orphaned | Exists but not linked to a confirmed pair; resolve R3 first |
   | `content/entity-remington-rand.md` | ✗ Missing | Entity summary schema |
   | `content/entity-wilson-jones.md` | ✗ Missing | Entity summary schema |
   | `content/entity-yawman-and-erbe.md` | ✗ Missing | Entity summary schema |
   | `content/entity-boorum-and-pease.md` | ✗ Missing | Entity summary schema |
   | `content/trademarks-narrative.md` | ✗ Missing | Gallery narrative schema |
   | `content/patents-narrative.md` | ✗ Missing | Gallery narrative schema |
   | `content/index-narrative.md` | ✗ Missing | Project landing schema |

   Research candidates for the 5-entry target: Wilson Jones VI-DEX (serial 71252433, B42F patents 1925–1927), Wilson Jones REDIREF and HANDIREF (serials 71254949 and 71254950, filed same day — likely coordinated product launch), Yawman & Erbe SHANNON (~1930).

**Phase gate:** 5 confirmed entries in `information-systems/matches/confirmed.jsonl`, each with an essay in `content/`; all entity summaries and gallery narratives written; `markery site build information-systems` produces a site with no placeholder pages.

---

## Phase 4 — Publication *(planned)*

**Goal:** One project publicly browsable at a stable URL.

**Note:** `tools/site_builder/` is already built (Phase 2). It generates all five page types (landing, trademark gallery, patent gallery, entity pages, match essays) as self-contained HTML. Phase 4 work is wiring and deployment, not building a site generator from scratch.

**Stages:**

1. **Wire `markery site build` CLI** (prerequisite R2, Phase 3) — already listed as a Phase 3 prerequisite; complete before Phase 4 begins.

2. **GitHub Pages** — `gh-pages` branch or `docs/` folder; single `markery site publish <project>` (or a Makefile target) regenerates and pushes.

3. **Open Graph metadata** — add `<meta property="og:*">` tags to `render.py` page generator; entries share cleanly on social/web; pages are crawlable.

4. **Referenced images** — the current site builder embeds images as base64. For publication, switch to referenced image files (`site/images/<serial>.png`) so pages are cacheable and load faster. Update `render.py` to write image files and reference them by path.

**Phase gate:** `information-systems` project is live at a stable URL with at least 3 entries and no placeholder pages.

---

## Research Agenda — Information Systems Project

### Candidate subjects (marks in the database)

| Mark | Serial | Filed | Company | Patent connection |
|---|---|---|---|---|
| SOUNDEX | 71246709 | 1927-03-31 | Rand Kardex Bureau | Russell 1918, Odell 1922 — phonetic indexing ✅ confirmed |
| SOUNDEX QUICK AS A FLASH | 71255821 | 1927-10-08 | Rand Kardex Bureau | Odell 1922 ✅ confirmed |
| KARDEX | 71467213 | 1939-12-14 | Remington Rand | Visible card-index patent cluster 1930–1939 — essay written |
| VARIADEX | 71461278 | 1939-04-07 | Remington Rand | US2152606A Card Index (1939) — essay written |
| VI-DEX | 71235764 | 1927-02-22 | Wilson Jones | Visible index products; candidate patents in B42F 1926–1927 |
| REDIREF | 71237470 | 1927-09-19 | Wilson Jones | Quick-reference filing; filed same day as HANDIREF |
| HANDIREF | 71237469 | 1927-09-19 | Wilson Jones | Quick-reference filing; filed same day as REDIREF |
| SHANNON | ~1930 | 1930 | Yawman & Erbe | Shannon lever-arch file brand; still manufactured today |
| SMEAD'S TELL VISION SYSTEM | 71403472 | 1938-02-26 | Smead Mfg. | Visible record system; entity not yet in registry |
| WHEELDEX | 71321669 | 1931-12-01 | Unknown | Rotary card file |

### Discovery methodology

1. Add target company to `entities.duckdb` (procedure in `README.md`)
2. Run `markery match information-systems` to generate candidates
3. Review `candidates.jsonl` — filter to product-name marks (not company names), high score, date overlap
4. Confirm pair: add entry to `confirmed.jsonl`, write essay in `content/`
5. Fetch patent PDF from Google Patents for primary source; enhance mark image via `markery enhance`

### Key reference works

- JoAnne Yates, *Control Through Communication* (1989) — filing systems and business communication 1880–1920
- JoAnne Yates, *Structuring the Information Age* (2005) — IBM and tabulating systems
- James W. Cortada, *Before the Computer* (1993) — IBM, NCR, Burroughs, Remington Rand
- Geoffrey Austrian, *Herman Hollerith* (1982) — punched card and tabulating history
- Alfred D. Chandler Jr., *The Visible Hand* (1977) — the management systems that created demand for information products

---

## Output Format Standards

| Format | When used | Notes |
|---|---|---|
| PNG (4×, ~3200px) | All enhanced marks | Print-ready at 300 DPI; universal |
| SVG | Clean word marks and geometric designs only | Skipped when illustration content is present |
| PDF | Patent documents | Downloaded from Google Patents |
| HTML (gallery) | Browsing output | Self-contained, base64-embedded; not for web publication |
| HTML (site) | Publication output | Referenced images, crawlable, Open Graph (Phase 4) |
| Markdown | Research essays, README | Tracked in git |

---

## Version History

| Tag | Notes |
|---|---|
| v0.2.0-alpha | TSDR mark_case_status, patents.duckdb (EPO OPS, B42F+B42D), entities.duckdb, match pipeline, STATUS.md, DEFERRED.md |
| v0.1.1-alpha | image_tools pipeline, /enhance-marks skill, historian specialist, projects/ tree |
| v0.1.0-alpha | TSDR client, trademarks.duckdb build, mark image retrieval |
