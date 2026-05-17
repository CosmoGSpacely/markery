# Project Status

## Current State

**Phase:** 1 — Complete / entering Phase 2 reorganization  
**Stage:** Phase 1 gate closed — operations workflow documented in `docs/workflows/research-session.md`  
**Version:** v0.2.0-alpha  
**Last updated:** 2026-05-17

---

## Current Project Focus

`projects/information-systems/` — pre-computer information systems, 1900–1939.

| Metric | Count |
|---|---|
| Entities in registry | 4 (Remington Rand, Wilson Jones, Yawman & Erbe, Boorum & Pease) |
| Candidate pairs | 2,412 |
| Confirmed pairs | 4 |
| Essays written | 2 (soundex.md, kardex.md) |

**Next action:** Begin Phase 2 codebase reorganization — see `ROADMAP.md` Phase 2 migration steps.

---

## Infrastructure Ledger

| Component | Status | Notes |
|---|---|---|
| `trademarks.duckdb` — 25,473 case files, 1900–1939 | ✅ Built | Includes `mark_images` (96 rows) and `mark_case_status` (10 rows) |
| `patents.duckdb` — 11,284 EPO patents (B42F, B42D) | ✅ Built | 5 additional CPC classes deferred (see D001 in DEFERRED.md) |
| `entities.duckdb` — canonical company registry | ✅ Built | 4 entities; add new companies via `build_entities_db.py` |
| `src/markery/db/tsdr_client.py` — USPTO TSDR API client | ✅ Built | Image fetch + case status JSON |
| `tools/image_enhancement/` — Real-ESRGAN upscale + SVG pipeline | ✅ Built | See `tools/image_enhancement/ENHANCE.md` |
| `src/markery/matching/` — patent-trademark candidate scoring pipeline | ✅ Built | Run: `markery match information-systems` |
| `tools/historian/` — Claude specialist | ✅ Built | Reads trademarks.duckdb directly |
| `/enhance-marks` skill | ✅ Built | |
| `projects/information-systems/` | 🚧 Active | 2 essays, 3 confirmed pairs |
| Publication pipeline (static site, GitHub Pages) | 🔲 Deferred | D002 — after 5 confirmed entries |
| Five additional CPC classes (B41J, B41L, G06C, G06K, G09F) | 🔲 Deferred | D001 — when typewriter/calculator entries needed |

---

## Phase 1 Gate

End-to-end research session is repeatable without consulting raw API docs:

- [x] New entity can be added to registry and candidates regenerated
- [x] Candidate list can be reviewed and a pair promoted to `confirmed.jsonl`
- [x] Essay can be written using the historian specialist
- [x] Mark images can be enhanced and a gallery built
- [x] Operations are documented in a single runnable checklist (`docs/workflows/research-session.md`)

Phase 1 is complete.

---

## Phase 2 — Codebase Reorganization (next)

Goal: `src/markery/` is the canonical package; unified `markery` CLI; all docs under `docs/`.

- Migrate `match/` → `src/markery/matching/`, db builders → `src/markery/db/`
- ✅ Move extensions to `tools/` tree (image_enhancement, patent_docs, historian)
- Build unified CLI replacing `scripts/` wrappers
- Move databases to `data/`, consolidate docs to `docs/reference/` and `docs/workflows/`

## Phase 3 — Corpus and Match Quality (planned)

Goal: information-systems project has 5 confirmed pairs with essays.

- Fetch remaining CPC classes (D001 — typewriters, calculators, tabulating)
- Build `tools/trademark_docs/` for non-image mark retrieval
- Systematic scoring review (D006 — company-name mark false positives)
- Add 2–3 new entities (Smead, Library Bureau, others from candidate list)

## Phase 4 — Publication (planned)

Goal: one project publicly browsable at a stable URL.

- Static site generator (Jinja2, two-level: project index + entry detail pages)
- GitHub Pages deployment
- Open Graph metadata for social sharing

See `DEFERRED.md` for items blocking these phases and their reopen triggers.
