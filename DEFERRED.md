# Deferred Work Register

Items explicitly deferred — not forgotten, not blocked, just not the current priority. Each entry has a reopen trigger. When the trigger condition arises, promote the item to active work.

| ID | Deferred item | Reopen trigger |
|---|---|---|
| D001 | Fetch remaining CPC classes: B41J (typewriters), B41L (duplicating), G06C (calculating machines), G06K (data recognition), G09F (display devices) | When information-systems project needs typewriter, tabulating, or calculator entries |
| D002 | Publication deployment (GitHub Pages, Open Graph, referenced images) | After information-systems project has 5 confirmed entries with essays — site builder (`tools/site_builder/`) is already built; Phase 4 work is CLI wiring + deployment only |
| D003 | Patent drawings extraction from PDF figures | When an essay needs inline patent figure images |
| D004 | Events table from `event.csv` (~3 GB) | When prosecution history is needed for a specific research question |
| D005 | Foreign application data (Madrid Protocol records) | When an international trademark comparison is needed |
| D006 | Scoring refinement for company-name marks | After systematic review of high-score false positives (REMINGTON, RAND, WILSON JONES COMPANY scoring 0.80 against every patent in the window) |

## Notes

D001 is the most likely to become active soon. B41J and G06C are the highest-priority classes for the information-systems research agenda (typewriters and calculating machines are well-represented in the 1900–1939 trademark record).

D006 is a quality improvement. The current scoring model treats company-name marks identically to product-name marks. A simple heuristic — flag marks whose `mark_element` matches a known entity canonical name — would filter most false positives without changing the scoring logic.
