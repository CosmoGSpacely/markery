# Markery Status

**Last updated:** 2026-05-18

---

## Tool Infrastructure

| Component | Status | Notes |
|---|---|---|
| `trademarks.duckdb` — 25,473 case files, 1900–1939 | ✅ | Includes `mark_images` (96 rows), `mark_case_status` (10 rows) |
| `patents.duckdb` — 11,284 patents (B42F, B42D) | ✅ | 5 CPC classes pending — see D001 in DEFERRED.md |
| `entities.duckdb` — canonical company registry | ✅ | |
| `specialist/patent/` — EPO OPS fetch, figures, signals | ✅ | `markery patent build/fetch/figures/signals` |
| `specialist/trademark/` — USPTO TSDR client, DB build | ✅ | `markery trademark` |
| `specialist/matchmaker/` — entity registry, scoring, candidate generation | ✅ | `markery match / matchmaker` |
| `specialist/historian/` — interactive review, status | ✅ | `markery review / status` |
| `specialist/publisher/` — static site generator, image enhancement | ✅ | `markery site build / enhance` |
| GitHub Pages CI (`pages.yml`) | ⏸ Paused | Disabled — deploy failures; re-enable after fixing |

---

## Active Projects

| Project | Entities | Confirmed pairs | Essays | Site | Next action |
|---|---|---|---|---|---|
| `information-systems` | 4 | 8 | 7 | Built | Add Smead entity; fetch D001 CPC classes |

See each project's `STATUS.md` for detail.
