# Deferred Work Register

Items explicitly deferred — not forgotten, not blocked, just not the current priority. Each entry has a reopen trigger. When the trigger condition arises, promote the item to active work.

| ID | Deferred item | Reopen trigger |
|---|---|---|
| D001 | Fetch remaining CPC classes: B41J (typewriters), B41L (duplicating), G06C (calculating machines), G06K (data recognition), G09F (display devices) | When information-systems project needs typewriter, tabulating, or calculator entries |
| D002 | Referenced images — switch from base64-embedded to file references (`site/images/<serial>.png`) for HTTP cacheability | When page-weight or caching becomes a concern; P1 (deploy), P2 (CI), and P3 (Open Graph) are complete |
| D003 | Patent drawings extraction from PDF figures | When an essay needs inline patent figure images |
| D004 | Events table from `event.csv` (~3 GB) | When prosecution history is needed for a specific research question |
| D005 | Foreign application data (Madrid Protocol records) | When an international trademark comparison is needed |
| ~~D006~~ | ~~Scoring refinement for company-name marks~~ | ✅ Done — `is_company_name_mark()` in `specialist/matchmaker/score.py`; applied as hard exclusion in `generate_candidates()` |

## Notes

D001 is the most likely to become active soon. B41J and G06C are the highest-priority classes for the information-systems research agenda (typewriters and calculating machines are well-represented in the 1900–1939 trademark record).

D006 is closed. D002 is partially closed — only referenced images remains.
