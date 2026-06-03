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

## Known data gaps

- No patent records in `patents.duckdb` for any entity at project setup. All patent acquisition is P3 scope.
- Pathé is French; EPO OPS coverage for French filers in 1920s film equipment is uncertain.
- Albert Setzer (entity 17) may need to be replaced if no patent records can be found.

## CLI bypass log

| Phase | Bypass | Command needed | DEFERRED |
|---|---|---|---|
| P1 | design_search discovery via raw DuckDB query | `markery trademark design-search 03 --filing-before 1930 --goods-contains electric` | D034 |
| P1 | `markery project init` crashes non-interactively; scaffolded manually | `markery project init <name>` | D027 (triggered) |
