# Project Status

## Current State

**Phase:** 3 — Complete / Phase 4 publication active  
**Stage:** Specialist refactor (Phases A–F) complete; site live on GitHub Pages; D006 and P3 done  
**Version:** v0.2.0-alpha  
**Last updated:** 2026-05-18

---

## Current Project Focus

`projects/information-systems/` — pre-computer information systems, 1900–1939.

| Metric | Count |
|---|---|
| Entities in registry | 4 (Remington Rand, Wilson Jones, Yawman & Erbe, Boorum & Pease) |
| Candidate pairs | 2,412 |
| Confirmed pairs | 4 |
| Essays written | 2 (soundex.md, kardex.md) |

**Next action:** D001 — fetch remaining CPC classes (B41J, B41L, G06C, G06K, G09F) to expand patent corpus for typewriter and calculator entities.

---

## Infrastructure Ledger

| Component | Status | Notes |
|---|---|---|
| `trademarks.duckdb` — 25,473 case files, 1900–1939 | ✅ Built | Includes `mark_images` (96 rows) and `mark_case_status` (10 rows) |
| `patents.duckdb` — 11,284 EPO patents (B42F, B42D) | ✅ Built | 5 additional CPC classes deferred (see D001 in DEFERRED.md) |
| `entities.duckdb` — canonical company registry | ✅ Built | 4 entities; add new companies via `markery matchmaker build` |
| `specialist/trademark/tsdr_client.py` — USPTO TSDR API client | ✅ Built | Image fetch + case status JSON |
| `specialist/publisher/image_enhancement/` — Real-ESRGAN upscale + SVG pipeline | ✅ Built | Run: `markery enhance enhance <serial> --out-dir <dir>` |
| `specialist/matchmaker/` — patent-trademark candidate scoring pipeline | ✅ Built | Run: `markery match information-systems` |
| `specialist/historian/` — interactive review and status | ✅ Built | Run: `markery review information-systems` / `markery status` |
| `specialist/publisher/` — static site generator | ✅ Built | Run: `markery site build information-systems` |
| GitHub Pages deployment (CI workflow) | ✅ Built | `.github/workflows/pages.yml` — rebuilds on push to `main` |
| Open Graph metadata (P3) | ✅ Built | `--base-url` flag; injected in CI workflow |
| Company-name mark filter (D006) | ✅ Built | `is_company_name_mark()` in `specialist/matchmaker/score.py` |
| `projects/information-systems/` | 🚧 Active | 8 confirmed pairs, 7 match essays, all entity pages written |
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

## Phase 2 — Codebase Reorganization ✅ Complete

Specialist-pattern architecture: `src/markery/specialist/` (patent, trademark, matchmaker, historian, publisher); unified `markery` CLI; databases in `data/`; docs in `docs/`. See `MARKERY_REVIEW.md` for the full design record.

## Phase 3 — Corpus and Match Quality ✅ Complete

8 confirmed pairs with essays; all entity summaries and gallery narratives written; `markery site build information-systems` produces 14 pages with no placeholder content.

## Phase 4 — Publication (active)

- ✅ P1 — Initial GitHub Pages deployment
- ✅ P2 — CI workflow (`.github/workflows/pages.yml`)
- ✅ P3 — Open Graph metadata (`--base-url` flag, injected in CI)
- 🔲 Referenced images — switch from base64-embedded to file references for cacheability

## Next priority

**D001** — Fetch remaining CPC classes (B41J typewriters, B41L duplicating, G06C calculating machines, G06K data recognition, G09F display devices) to expand patent corpus for typewriter and calculator entities.

See `DEFERRED.md` for the full deferred register and reopen triggers.
