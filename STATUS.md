# Project Status

## Current State

**Phase:** 1 — Working Research Tool  
**Stage:** Active research — building confirmed entries for information-systems project  
**Version:** v0.2.0-alpha  
**Last updated:** 2026-05-13

---

## Current Project Focus

`projects/information-systems/` — pre-computer information systems, 1900–1939.

| Metric | Count |
|---|---|
| Entities in registry | 4 (Remington Rand, Wilson Jones, Yawman & Erbe, Boorum & Pease) |
| Candidate pairs | 2,412 |
| Confirmed pairs | 3 |
| Essays written | 2 (soundex.md, kardex.md) |

**Next action:** Develop next confirmed entry — Wilson Jones VI-DEX (serial 71235764) or REDIREF/HANDIREF (serials 71237470, 71237469).

---

## Infrastructure Ledger

| Component | Status | Notes |
|---|---|---|
| `trademarks.duckdb` — 25,473 case files, 1900–1939 | ✅ Built | Includes `mark_images` (96 rows) and `mark_case_status` (10 rows) |
| `patents.duckdb` — 11,284 EPO patents (B42F, B42D) | ✅ Built | 5 additional CPC classes deferred (see D001 in DEFERRED.md) |
| `entities.duckdb` — canonical company registry | ✅ Built | 4 entities; add new companies via `build_entities_db.py` |
| `tsdr_client.py` — USPTO TSDR API client | ✅ Built | Image fetch + case status JSON |
| `image_tools/` — Real-ESRGAN upscale + SVG pipeline | ✅ Built | See `image_tools/ENHANCE.md` |
| `match/` — patent-trademark candidate scoring pipeline | ✅ Built | Run: `python -m match information-systems` |
| `commerce-and-technology-historian/` — Claude specialist | ✅ Built | Reads trademarks.duckdb directly |
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
- [ ] Operations are documented in a single runnable checklist (in progress)

Phase 1 is functionally complete. The gate will close when the operations checklist is in place.

---

## Phase 2 — Corpus and Match Quality (planned)

Goal: information-systems project has 5 confirmed pairs with essays.

- Fetch remaining CPC classes (D001 — typewriters, calculators, tabulating)
- Systematic scoring review (D006 — company-name mark false positives)
- Add 2–3 new entities (Smead, Yawman & Erbe expansion, others from candidate list)

## Phase 3 — Publication (planned)

Goal: one project publicly browsable at a stable URL.

- Static site generator (Jinja2, two-level: project index + entry detail pages)
- GitHub Pages deployment
- Open Graph metadata for social sharing

See `DEFERRED.md` for items blocking these phases and their reopen triggers.
