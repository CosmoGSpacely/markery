# Information Systems

Research project documenting the commercial history of pre-computer information systems through the combined USPTO trademark and patent record.

**Period:** 1900–1939  
**Scope:** American manufacturers of filing appliances, card-index systems, visible record equipment, loose-leaf binders, and related office information products

---

## What This Project Is

Between roughly 1880 and 1940, American businesses built sophisticated systems for managing information at scale using entirely non-electronic means — filing cabinets, card indexes, visible record trays, tabulating machines, phonetic coding schemes. These systems were patented, trademarked, and sold by major industrial companies. They were used at massive scale. They are almost entirely absent from the standard history of information technology.

This project recovers that history one confirmed patent-trademark pair at a time. For each entry, a specific patent and a specific trademark registration are linked to the same corporate entity and the same product, and the connection is documented in a research essay.

See `RESEARCH.md` in the project root for the full intellectual framework and literature context.

---

## Current Coverage

### Entities

Four companies are currently in the entity registry and active in this project:

| Entity | Patents (B42F+B42D) | Trademarks | Entity ID |
|---|---|---|---|
| Remington Rand | 171 | 9 | 1 |
| Wilson Jones | 130 | 6 | 2 |
| Yawman & Erbe | 59 | 3 | 3 |
| Boorum & Pease | 38 | 3 | 4 |

Entity name variants (the different spellings that appear in each database) are defined in `build_entities_db.py` and stored in `entities.duckdb`.

### Candidate pairs

The `match/` pipeline has generated **2,412 scored candidate pairs** across these four entities, stored in `matches/candidates.jsonl`. Run `python -m match information-systems` to regenerate.

Top candidates by score (patent granted within weeks of trademark filing):

| Score | Patent | Granted | Trademark | Filed | Entity |
|---|---|---|---|---|---|
| 0.80 | US2152606A Card Index | 1939-03-28 | VARIADEX | 1939-04-07 | Remington Rand |
| 0.80 | US1973497A Loose Leaf Binder | 1934-09-11 | SCOTTIE | 1934-10-08 | Remington Rand |
| 0.80 | US1527374A | 1925-02-24 | FAVORITE | 1925-03-20 | Wilson Jones |
| 0.80 | US1713945A Accounting And Filing System | 1929-05-21 | REMRANDCO | 1929-06-19 | Remington Rand |
| 0.80 | US2178449A Card-Holding Clip | 1939-10-31 | KARDEX | 1939-12-14 | Remington Rand |

---

## Confirmed Entries

### [Soundex](content/soundex.md)
*Rand Kardex Bureau — SOUNDEX (1927) and SOUNDEX QUICK AS A FLASH (1927)*

The Russell (1918) and Odell (1922) patents for phonetic name-indexing, both assigned to Remington Typewriter Company, commercialized as the SOUNDEX product line by Rand Kardex Bureau immediately before the 1927 merger that formed Remington Rand. The most fully documented entry and the founding case for this project.

Confirmed pairs: US1261167A → serial 71246709; US1435663A → serials 71246709 and 71255821.

### [Kardex](content/kardex.md)
*Remington Rand — KARDEX (1939), VARIADEX (1939), LINEDEX (1931), SCOTTIE (1934)*

The visible card-index system and its associated product family, traced through 171 Remington Rand patents from 1917 to 1939 and four trademark registrations. Covers the commercial peak of visible-record filing technology and the consolidation of Remington Rand's brand assets in the late 1930s.

---

## Next Candidates

High-priority entries identified from the candidate list and prior research:

**Wilson Jones — VI-DEX (1927)**  
Serial 71252433. Wilson Jones's visible index product line, filed 1927-07-22, first use 1925-06-27. Draw code 5S11 (stylized mark — has image). The "VI" almost certainly stands for visible index. Candidate patent: among Wilson Jones's 130 B42F patents, those granted in 1925–1927 are the primary search window.

**Wilson Jones — REDIREF / HANDIREF (1927)**  
Serials 71254949 and 71254950, both filed September 19, 1927 — the same day. Loose-leaf binders and sheets. The simultaneous filing suggests a coordinated product launch.

**Yawman & Erbe — SHANNON (1930)**  
Serial in the Yawman and Erbe trademark records. The Shannon lever-arch file brand, acquired by Yawman & Erbe and trademarked 1930. Shannon arch binders are still manufactured today.

**Smead Mfg. — SMEAD'S TELL VISION SYSTEM (1938)**  
Serial 71403472. A visible record system from a company not yet in the entity registry. Candidate for the next entity addition.

---

## Candidate Assessment

The candidate pipeline scores pairs but does not distinguish product-name trademarks from company-name trademarks. When reviewing `candidates.jsonl`:

- **Product-name marks** (KARDEX, VARIADEX, VI-DEX, SOUNDEX, SHANNON, FAVORITE) — primary research targets
- **Company-name marks** (REMINGTON, RAND, WILSON JONES COMPANY) — every patent matches these; not useful as product-level pairs
- **High score + product name + period overlap** — promote to `confirmed.jsonl`

To review candidates interactively:
```bash
scripts/review                          # all candidates, score >= 0.5
scripts/review --mark VI-DEX            # single trademark
scripts/review --min-score 0.65         # tighter threshold
```

---

## Output Collections

Generated images and galleries live in `output/` (gitignored — regenerate with `scripts/enhance`):

| Folder | Contents |
|---|---|
| `output/soundex-marks/` | SOUNDEX and SOUNDEX QUICK AS A FLASH mark images, patent PDFs |
| `output/filing-systems/` | 40 design marks for filing and records organization |
| `output/stationery-marks/` | 55 design marks for stationery and writing paper goods |

---

## Key References

- JoAnne Yates, *Control Through Communication* (1989)
- JoAnne Yates, *Structuring the Information Age* (2005)
- James W. Cortada, *Before the Computer* (1993)
- Geoffrey Austrian, *Herman Hollerith: Forgotten Giant of Information Processing* (1982)
- Alfred D. Chandler Jr., *The Visible Hand* (1977)
