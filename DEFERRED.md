# Deferred Work Register

Items explicitly deferred — not forgotten, not blocked, just not the current priority. Each entry has a reopen trigger. When the trigger condition arises, promote the item to active work.

| ID | Deferred item | Reopen trigger |
|---|---|---|
| D001 | Fetch remaining G09F patents (1910–1939) for information-systems project | EPO OPS 403 daily quota hit 2026-05-20. G06C and G06K fully complete. G09F: 1900–1909 done (1,862 patents); 1910–1939 still needed (6 windows). Run: `markery patent build --classes G09F --resume --year-start 1900 --year-end 1939` when quota resets. Project work, not Markery infrastructure. |
| D007 | Patent bulk CSV acquisition route | Stub documented in SETUP.md 2026-05-20 but not implemented. Reopen when: a project needs large-scale patent data infeasible via EPO OPS rate limits (e.g. broad class sweep across many decades), or when an offline/air-gapped environment is required. Sources: PatentsView, Google Patents Public Data. |
| D008 | Historian persona stale content (Phase 7) | Historian persona `README.md` and `reference/markery-database.md` reference `mark_case_status` (removed in Phase 7), hardcode information-systems project row counts (25,473 trademarks, 11,284 patents, B42F/B42D classes), and use old path `src/markery/matching/`. Reopen when updating the historian persona for a new project or before using the historian persona in a Claude project. |
| D009 | Flesh out four new specialist personas | Stubs created 2026-05-20 for patent, trademark, matchmaker, and publisher specialists. Each has `README.md`, `identity.md`, one or two instruction cards, and one reference doc. Reopen when: starting a new project that will use these specialists as Claude projects; or in the next documentation pass (explicitly deferred from this session). |
| ~~D002~~ | ~~Referenced images — switch from base64-embedded to file references~~ | ✅ Done — `_img_src()` in `publisher/render.py`; `build_site()` writes `out/images/{marks,patents}/`; render functions accept `images_dir` |
| ~~D003~~ | ~~Patent drawings extraction from PDF figures~~ | ✅ Done — `[[figure:patent_no]]` in `_render_markdown()` resolves via `figure_index`; `<figure class="patent-figure">` rendered in essays |
| ~~D004~~ | ~~Events table from `event.csv`~~ | ✅ Done — `events` DDL in `_ENRICHMENT_DDL`; `load_events()`; `get_events()`; `markery trademark load-events` |
| ~~D005~~ | ~~Foreign application data (Madrid Protocol records)~~ | ✅ Done — `foreign_app` DDL in `_ENRICHMENT_DDL`; `load_foreign_app()`; `get_foreign_apps()`; `markery trademark load-foreign` |
| ~~D006~~ | ~~Scoring refinement for company-name marks~~ | ✅ Done — `is_company_name_mark()` in `specialist/matchmaker/score.py`; applied as hard exclusion in `generate_candidates()` |
