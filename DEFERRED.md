# Deferred Work Register

Items explicitly deferred — not forgotten, not blocked, just not the current priority. Each entry has a reopen trigger. When the trigger condition arises, promote the item to active work.

| ID | Deferred item | Reopen trigger |
|---|---|---|
| D001 | Fetch remaining CPC classes: B41J (typewriters), B41L (duplicating), G06C (calculating machines), G06K (data recognition), G09F (display devices) | When information-systems project needs typewriter, tabulating, or calculator entries |
| ~~D002~~ | ~~Referenced images — switch from base64-embedded to file references~~ | ✅ Done — `_img_src()` in `publisher/render.py`; `build_site()` writes `out/images/{marks,patents}/`; render functions accept `images_dir` |
| ~~D003~~ | ~~Patent drawings extraction from PDF figures~~ | ✅ Done — `[[figure:patent_no]]` in `_render_markdown()` resolves via `figure_index`; `<figure class="patent-figure">` rendered in essays |
| ~~D004~~ | ~~Events table from `event.csv`~~ | ✅ Done — `events` DDL in `_ENRICHMENT_DDL`; `load_events()`; `get_events()`; `markery trademark load-events` |
| ~~D005~~ | ~~Foreign application data (Madrid Protocol records)~~ | ✅ Done — `foreign_app` DDL in `_ENRICHMENT_DDL`; `load_foreign_app()`; `get_foreign_apps()`; `markery trademark load-foreign` |
| ~~D006~~ | ~~Scoring refinement for company-name marks~~ | ✅ Done — `is_company_name_mark()` in `specialist/matchmaker/score.py`; applied as hard exclusion in `generate_candidates()` |

## Notes

D001 is the only remaining open item. B41J and G06C are the highest-priority classes for the information-systems research agenda (typewriters and calculating machines are well-represented in the 1900–1939 trademark record). The infrastructure for loading CPC classes already exists; this is a data-population task for the project phase.
