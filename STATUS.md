# Markery Status

**Last updated:** 2026-05-24

---

## Tool Infrastructure

| Component | Status | Notes |
|---|---|---|
| `trademarks.duckdb` — 25,473 case files, 1900–1939 | ✅ | `mark_images` (226 rows), `extended_marks` (139 rows) |
| `patents.duckdb` — 40,029 patents (B42F, B42D, B41J, B41L, G06C, G06K, G09F complete 1900–1939) | ✅ | |
| `entities.duckdb` — 5 entities, 32 variants | ✅ | |
| `specialist/patent/` — EPO OPS fetch, figures, signals | ✅ | `markery patent build/fetch/figures/signals` |
| `specialist/trademark/` — USPTO TSDR client, DB build | ✅ | `markery trademark` |
| `specialist/matchmaker/` — entity registry, scoring, candidate generation | ✅ | `markery match / matchmaker` |
| `specialist/historian/` — interactive review, status | ✅ | `markery review / status` |
| `specialist/publisher/` — static site, image enhancement, Wikipedia tooling | ✅ | `markery site build / enhance / wikipedia` |
| `enhance` — gallery subcommand | ✅ | Works without optional deps (lazy import fix 2026-05-20) |
| `enhance` — enhance/batch subcommands | ✅ | Lanczos fallback active; Real-ESRGAN activates automatically if installed |
| `wikipedia` — draft/submit/from-essay subcommands | ✅ | `from-essay` works without confirmed.jsonl for any project |
| GitHub Pages CI (`pages.yml`) | ✅ | Fixed in v0.3.1a1 (2026-05-24) — `notes` column removed from query, Node.js 24 opted in |

---

## Active Roadmap Phase

**Phase 14 — Efficiency Baseline: Token and Model Benchmarking** (opened 2026-05-24)

| Sub-phase | Status |
|---|---|
| P1 — Token instrumentation (`--tokens` flag, `MARKERY_TOKEN_LOG`) | 🔲 Not started |
| P2 — Baseline sweep on `information-systems` | 🔲 Not started |
| P3 — Hotspot reductions (≥ 20% prompt-token reduction) | 🔲 Not started |
| P4 — Free-model run (Haiku end-to-end validation) | 🔲 Not started |
| P5 — MVO contracts and `tests/test_mvo.py` | 🔲 Not started |

**Phases 9–13 closed 2026-05-24.** Phase 9 P4 final state: Stage 4a ✅ (rev 1355562394) · Stage 4b ✅ live (rev 1355562959) · 48h window elapsed unreverted. Stages 4c–4d deferred as D023, D024.

---

## Project Types

Project types define the workflow a project follows. Type definitions and session workflows are owned by the HISTORIAN specialist; see `src/markery/specialist/historian/persona/reference/project-types.md`.

| Type | Session workflow | Example project |
|---|---|---|
| Match-review-essay | `specialist/historian/persona/research-session.md` | `information-systems` |
| Gallery/exploration | Project `README.md` | `monthly-image-review` |

---

## Active Projects

| Project | Type | Next action |
|---|---|---|
| `information-systems` | Match-review-essay | Resume candidate review |
| `monthly-image-review` | Gallery/exploration | Run July–December 1930 months; Stage 4c Wikipedia inline citation deferred (D023) |

See each project's `STATUS.md` for detail.
