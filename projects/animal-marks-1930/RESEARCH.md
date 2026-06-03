# Research: Animal Marks in Early American Technology (pre-1931)

## Central argument

Early American technology companies — manufacturers of motor trucks, aircraft engines, electrical components, film equipment, and industrial batteries — chose animal imagery for their trademarks at a moment when brand identity was still forming as a commercial practice. The animal was not decorative: each choice encodes a specific claim about the product's character, the company's self-image, or the competitive context in which the product was sold. Reading the animal against the patent record reveals how the same engineering organization simultaneously pursued intellectual property protection and commercial brand differentiation as two halves of a single market strategy.

## Entities and their animals

| ID | Entity | Animal | Mark | Serial | Filed |
|---|---|---|---|---|---|
| 13 | Mack Trucks | Bulldog | (figurative) | 71247861 | 1927-04-22 |
| 14 | Pratt and Whitney Aircraft | Eagle | PRATT & WHITNEY DEPENDABLE ENGINES | 71289592 | 1929-09-10 |
| 15 | Eagle Electric Manufacturing | Eagle | EAGLE PERFECTION IS NOT AN ACCIDENT | 71241267 | 1926-12-10 |
| 16 | Pathe Cinema | Rooster | PATHE | 71198721 | 1924-06-17 |
| 17 | Albert Setzer | Mule | MULE | 71164129 | 1922-05-19 |

## The "why animal" question by entity

**Mack Trucks / bulldog:** British soldiers in World War I nicknamed Mack trucks "bulldogs" because of their short hood and unstoppable reliability under battlefield conditions. Mack adopted the bulldog as an official emblem — the animal is the product's reputation, given back as a brand. The bulldog is a character reference, not a metaphor.

**Pratt & Whitney / eagle:** An eagle for an aircraft engine maker is the most literal possible choice — the animal that does what the product enables. But the specific claim in the mark ("DEPENDABLE ENGINES") reframes it: the eagle is not about flight, it is about reliability. Power without failure. The eagle as proof of engineering quality.

**Eagle Electric / eagle:** The company name *is* the animal. Eagle Electric did not choose an eagle to represent something about its products; it chose a name and then registered a mark that depicted what the name said. This is brand identity through nomination, not metaphor — a different relationship between animal and product than the other four entities.

**Pathé / rooster:** The Pathé cockerel is the Gallic rooster — the national symbol of France — carried into the American market by a French company expanding its distribution. The rooster signals foreign origin, not product character. For American customers in 1924, a French rooster on a film camera said something specific about European technical sophistication in the photographic arts.

**Albert Setzer / mule:** MULE for electric storage batteries is the most oblique choice. A mule is a beast of burden — dependable, unspectacular, suited for work that does not require speed or grace. Electric storage batteries in 1922 were industrial infrastructure: they powered telephone exchanges, starting motors, and lighting plants. The mule is an honest metaphor for an honest product.

## Scope note on patent acquisition

None of these five entities has patent records in `patents.duckdb` at project setup (the existing DB was swept for radio-era CPC classes H04B/H01J/H03F/H04R). Patent acquisition in P3 will use targeted per-assignee pulls via `markery patent pull <no>` for known specific patents. CPC sweeps are not used in this project — confirmed zero-coverage risk via `patent coverage-check` is the expected result for all relevant classes.

## Operational model

**`MARKERY_MODEL=claude-haiku-4-5-20251001` is the committed operational model for this project.** All historian, librarian extract, and any inference operations use Haiku. This is not a test — it is the primary model. If a step cannot be completed on Haiku, the failure mode and minimum required model tier are documented in RESEARCH-AGENDA.md.
