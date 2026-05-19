# Deferred Work Register

Items explicitly deferred — not forgotten, not blocked, just not the current priority. Each entry has a reopen trigger. When the trigger condition arises, promote the item to active work.

| ID | Deferred item | Reopen trigger |
|---|---|---|
| D001 | Fetch remaining CPC classes: G06C (1930–1939), G06K, G09F | EPO OPS 403 daily quota hit 2026-05-19. B41J (10,031) and B41L (3,073) complete; G06C partial (1900–1929, 2,568 patents). Reopen trigger: run `markery patent build --classes G06C G06K G09F --resume` the next day when quota resets. Note: project work, not Markery infrastructure. |
| ~~D002~~ | ~~Referenced images — switch from base64-embedded to file references~~ | ✅ Done — `_img_src()` in `publisher/render.py`; `build_site()` writes `out/images/{marks,patents}/`; render functions accept `images_dir` |
| ~~D003~~ | ~~Patent drawings extraction from PDF figures~~ | ✅ Done — `[[figure:patent_no]]` in `_render_markdown()` resolves via `figure_index`; `<figure class="patent-figure">` rendered in essays |
| ~~D004~~ | ~~Events table from `event.csv`~~ | ✅ Done — `events` DDL in `_ENRICHMENT_DDL`; `load_events()`; `get_events()`; `markery trademark load-events` |
| ~~D005~~ | ~~Foreign application data (Madrid Protocol records)~~ | ✅ Done — `foreign_app` DDL in `_ENRICHMENT_DDL`; `load_foreign_app()`; `get_foreign_apps()`; `markery trademark load-foreign` |
| ~~D006~~ | ~~Scoring refinement for company-name marks~~ | ✅ Done — `is_company_name_mark()` in `specialist/matchmaker/score.py`; applied as hard exclusion in `generate_candidates()` |

## Notes

All items closed. DEFERRED register is empty. Phase 7 work (database improvements per DATABASE_REVIEW.md) is tracked separately.
