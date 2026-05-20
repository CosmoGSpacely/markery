# Markery Status

**Last updated:** 2026-05-20

---

## Tool Infrastructure

| Component | Status | Notes |
|---|---|---|
| `trademarks.duckdb` — 25,473 case files, 1900–1939 | ✅ | `mark_images` (96 rows), `extended_marks` (18 rows) |
| `patents.duckdb` — ~30,500 patents (B42F, B42D, B41J, B41L, G06C, G06K; G09F partial 1900–1909) | ✅ | G09F 1910–1939 pending — see D001 in DEFERRED.md |
| `entities.duckdb` — 5 entities, 32 variants | ✅ | |
| `specialist/patent/` — EPO OPS fetch, figures, signals | ✅ | `markery patent build/fetch/figures/signals` |
| `specialist/trademark/` — USPTO TSDR client, DB build | ✅ | `markery trademark` |
| `specialist/matchmaker/` — entity registry, scoring, candidate generation | ✅ | `markery match / matchmaker` |
| `specialist/historian/` — interactive review, status | ✅ | `markery review / status` |
| `specialist/publisher/` — static site generator, image enhancement | ✅ | `markery site build / enhance` |
| GitHub Pages CI (`pages.yml`) | ❌ Disabled | Workflows deleted 2026-05-20 — deploy failures |

---

## Project Types

Project types define the workflow a project follows. Type definitions and session workflows are owned by the HISTORIAN specialist; see `src/markery/specialist/historian/persona/reference/project-types.md`.

| Type | Session workflow | Example project |
|---|---|---|
| Match-review-essay | `research-session.md` | `information-systems` |
| Gallery/exploration | Project `README.md` | `monthly-image-review` |

---

## Active Projects

| Project | Type | Next action |
|---|---|---|
| `information-systems` | Match-review-essay | Fetch G09F 1910–1939 (D001); add Smead entity (D010) |
| `monthly-image-review` | Gallery/exploration | Run June–December 1930 months |

See each project's `STATUS.md` for detail.
