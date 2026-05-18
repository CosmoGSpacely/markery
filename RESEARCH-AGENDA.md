# Research Agenda — Information Systems Project

Pre-computer information systems: filing appliances, card-index systems, visible records equipment, tabulating machines, 1900–1939. See `RESEARCH.md` for the scholarly framework.

---

## Candidate subjects

| Mark | Serial | Filed | Company | Patent connection |
|---|---|---|---|---|
| SOUNDEX | 71246709 | 1927-03-31 | Rand Kardex Bureau | Russell 1918, Odell 1922 — phonetic indexing ✅ confirmed |
| SOUNDEX QUICK AS A FLASH | 71255821 | 1927-10-08 | Rand Kardex Bureau | Odell 1922 ✅ confirmed |
| KARDEX | 71467213 | 1939-12-14 | Remington Rand | Visible card-index patent cluster 1930–1939 ✅ confirmed |
| VARIADEX | 71461278 | 1939-04-07 | Remington Rand | US2152606A Card Index (1939) ✅ confirmed |
| VI-DEX | 71235764 | 1927-02-22 | Wilson Jones | Visible index products ✅ confirmed |
| REDIREF | 71237470 | 1927-09-19 | Wilson Jones | Quick-reference filing ✅ confirmed |
| HANDIREF | 71237469 | 1927-09-19 | Wilson Jones | Filed same day as REDIREF ✅ confirmed |
| SHANNON | ~1930 | 1930 | Yawman & Erbe | Shannon lever-arch file brand ✅ confirmed |
| SMEAD'S TELL VISION SYSTEM | 71403472 | 1938-02-26 | Smead Mfg. | Visible record system; entity not yet in registry |
| WHEELDEX | 71321669 | 1931-12-01 | Unknown | Rotary card file |

---

## Discovery methodology

1. Add target company to `entities.duckdb` — edit `src/markery/specialist/matchmaker/build.py` → `markery matchmaker build`
2. Run `markery match information-systems` to generate candidates
3. Review `candidates.jsonl` — filter to product-name marks (not company names), high score, date overlap
4. Confirm pair: add entry to `confirmed.jsonl`, write essay in `content/`
5. Fetch patent PDF from Google Patents for primary source; enhance mark image via `markery enhance`

---

## Key reference works

- JoAnne Yates, *Control Through Communication* (1989) — filing systems and business communication 1880–1920
- JoAnne Yates, *Structuring the Information Age* (2005) — IBM and tabulating systems
- James W. Cortada, *Before the Computer* (1993) — IBM, NCR, Burroughs, Remington Rand
- Geoffrey Austrian, *Herman Hollerith* (1982) — punched card and tabulating history
- Alfred D. Chandler Jr., *The Visible Hand* (1977) — the management systems that created demand for information products

---

## Output format standards

| Format | When used | Notes |
|---|---|---|
| PNG (4×, ~3200px) | All enhanced marks | Print-ready at 300 DPI; universal |
| SVG | Clean word marks and geometric designs only | Skipped when illustration content is present |
| PDF | Patent documents | Downloaded from Google Patents |
| HTML (site) | Publication output | Base64-embedded images, Open Graph metadata |
| Markdown | Research essays, README | Tracked in git |
