# Research Agenda: Animal Marks in Early American Technology

## Open questions

**Q1 — Why the bulldog and not another dog?** The Mack bulldog story is known (WWI soldiers' nickname), but what was the legal mechanism? When was the bulldog first used commercially and who filed for it? Was the 1927 trademark the first filing, or was it a re-registration of an earlier common-law use?

**Q2 — Is the Pathé rooster legally French or American?** The 1924 filing is by "PATHE CINEMA, ANCIENS ETABLISSEMENTS PATHE FRERES" — a French entity. What US patent assignee name covers Pathé's American film equipment patents, if any? The rooster mark for a foreign company entering the US market is a distinct case from the domestic entities.

**Q3 — What patents does Pratt & Whitney have in the 1925–1930 window?** The aircraft company was founded 1925. The trademark was filed 1929. A four-year company with a filed trademark and "dependable engine" branding suggests active patent prosecution. What are the specific engine patents and what do they claim?

**Q4 — Did Albert Setzer invent anything, or is MULE a distribution trademark?** A single individual filing a trademark for electric storage batteries in 1922 is unusual. Is this a manufacturer, a distributor, or a retailer of a branded product? If there are no associated patents, the pair is structural-only (temporal proximity, no technical correspondence).

**Q5 — Eagle Electric vs. General Electric: is the eagle a proximity signal?** Eagle Electric filed in 1926, 37 years after GE was founded. The eagle as a brand image in electrical equipment in the 1920s existed in a field dominated by GE's own bird imagery. Was the choice competitive positioning, coincidence, or something else?

## Candidate pairs to investigate

| Entity | Trademark | Anticipated patent domain | Notes |
|---|---|---|---|
| Mack Trucks | 71247861 (bulldog, motor trucks) | Automotive: engine, transmission, axle patents | Pull specific Mack patents from Google Patents |
| Pratt & Whitney | 71289592 (eagle, aircraft engines) | Aerospace: radial engine, cylinder, supercharger | P&W Wasp (1925) and Hornet (1926) are the key engines |
| Eagle Electric | 71241267 (eagle, electrical components) | Electrical: wiring devices, switches, receptacles | Check EPO for Eagle Electric assignee strings |
| Pathe Cinema | 71198721 (rooster, cameras/projectors) | Optical/film: camera mechanism, projector patents | Likely French-origin patents; limited US filing expected |
| Albert Setzer | 71164129 (mule, electric batteries) | Industrial: storage battery chemistry and construction | Low patent probability — may be structural-only pair |

## Patent coverage after P3 sweeps

**6 of 18 entities have patent coverage (66 unique patents):**

| Entity | Patents | Classes swept | Notes |
|---|---|---|---|
| Pratt & Whitney (14) | 1 | B64D 1923–1932 | US1871055A "Liquid Supplying Means For Aircraft Engines" |
| Deere (19) | 47 | A01B 1908–1932 | Strong coverage across agricultural machinery patents |
| Worthington Pump (21) | 3 | F04B 1918–1926 | Pump patents confirmed |
| Goodyear (23) | 6 | B60C 1918–1930 | Tire patents confirmed |
| Colt (24) | 3 | F41A/F41C 1918–1928 | Firearms patents confirmed |
| General Motors (26) | 6 | F02B 1920–1930 | Engine/automotive patents confirmed |

**12 entities with no patent coverage** — candidates will not be generated for these in P4:
Mack Trucks (13), Eagle Electric (15), Pathé (16), MULE/Setzer (17), Shell Oil (18), Alfa Romeo (20), Raleigh Cycle (22), J.I. Case (25), James Walker (27), Gillette Tire (28), American Brass (29), Standard-Johnson (30).

**Why no coverage:** EPO OPS sweeps for pre-1940 patents in these specific domains either returned zero (no CPC reclassification) or returned records with no matching assignee names. Targeted `markery patent pull <no>` with specific patent numbers from Google Patents lookup would be needed — not possible without internet access during this session. These entities remain in the project for their trademark-only research value (animal imagery, public domain drawings, "why animal" analysis).

**False positives detected and excluded:**
- CASE RES LAB INC → photo-electric devices, NOT J.I. Case agricultural machinery
- SHAW WALKER CO → filing cabinets, NOT James Walker & Co. gaskets (UK)
- GILLETTE SAFETY RAZOR CO → razors, NOT Gillette Tire Company
- SHELL COMPANY OF CALIFORNIA → advertising/coupon patents, NOT petroleum fuel patents

## CLI bypass log

| Phase | Bypass | Command needed | DEFERRED |
|---|---|---|---|
| P1 | design_search discovery via raw DuckDB query | `markery trademark design-search 03 --filing-before 1930 --goods-contains electric` | D034 |
| P1 | `markery project init` crashes non-interactively; scaffolded manually | `markery project init <name>` | D027 (triggered) |
| P1 | variants.csv comma-in-name bug: unquoted owner names containing commas parsed incorrectly by DictReader; entity 16 (Pathé) silent zero-match until fixed | variants.csv should quote fields containing commas; `markery matchmaker build` should validate CSV parse integrity | D035 |
