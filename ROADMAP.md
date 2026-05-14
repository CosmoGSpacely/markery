# Markery Roadmap

Research design and phase plan for the Markery project. Current state and metrics live in `STATUS.md`; deferred items live in `DEFERRED.md`.

---

## What Markery Is

Markery is a research tool for studying American commercial history through the combined USPTO trademark and patent record. The project cross-references trademark registrations with patent filings for the same companies and time periods, producing documented patent-trademark pairs that reveal the commercial lifecycle of early 20th-century technologies.

The core hypothesis: the trademark record establishes what a company called its product and when it entered commerce; the patent record establishes what was technically novel. Neither source alone shows the full picture. No existing work systematically cross-references them for the 1900–1939 period.

**Primary research focus:** pre-computer information systems — the filing cabinets, card indexes, visible record systems, tabulating machines, and phonetic coding schemes that American businesses used to organize knowledge before the digital era.

---

## Phase 1 — Working Research Tool *(largely complete)*

**Goal:** End-to-end research session is repeatable — a new entity can be added, candidates generated, a pair confirmed, and an essay written without consulting raw API docs.

| Stage | What was built | Skill developed |
|---|---|---|
| TSDR client | `tsdr_client.py` — case status JSON + raw mark image fetch | External API integration, rate limiting |
| Trademark database | `trademarks.duckdb` — 25,473 case files, 1900–1939 | DuckDB database design, bulk CSV import |
| Historian specialist | `commerce-and-technology-historian/` — Claude specialist persona | Specialist agent design, system prompt engineering |
| Image pipeline | `image_tools/` — Real-ESRGAN 4× upscale + SVG vectorization | ML inference pipeline, image processing |
| Patent database | `patents.duckdb` — 11,284 EPO patents (B42F, B42D), 1900–1939 | EPO OPS API, CQL queries, OAuth2 |
| Entity registry | `entities.duckdb` — canonical company registry with name variants | Entity resolution, cross-database ATTACH queries |
| Match pipeline | `match/` — scored patent-trademark candidate pairs | Scoring model design, research workflow |
| Projects tree | `projects/information-systems/` — first research project | Research methodology, primary source curation |

**Phase gate:** Phase 1 closes when the operations workflow is documented as a single runnable checklist (in progress — see `STATUS.md`).

---

## Phase 2 — Corpus and Match Quality *(planned)*

**Goal:** `information-systems` project has 5 confirmed entries with essays.

**Stages:**

1. **Remaining CPC classes** — fetch B41J (typewriters), B41L (duplicating), G06C (calculating machines), G06K (data recognition), G09F (display devices) into `patents.duckdb`. Deferred as D001 until typewriter/calculator entries are needed. Command: `python build_patents_db.py --classes B41J B41L G06C G06K G09F --resume`.

2. **New entities** — add Smead Mfg. (SMEAD'S TELL VISION SYSTEM, 1938), Library Bureau, and others identified through the candidate list. Procedure: `README.md` → entities section.

3. **Scoring refinement** — address company-name mark false positives (D006). A heuristic that flags marks whose `mark_element` matches an entity canonical name would filter most without changing the scoring formula.

4. **Confirmed entries** — develop Wilson Jones (VI-DEX, REDIREF, HANDIREF), Yawman & Erbe (SHANNON), and at least one typewriter or tabulating machine entry once Phase 2 CPC data is available.

**Phase gate:** 5 confirmed entries in `information-systems/matches/confirmed.jsonl`, each with an essay in `content/`.

---

## Phase 3 — Publication *(planned)*

**Goal:** One project publicly browsable at a stable URL.

**Stages:**

1. **Static site generator** — Jinja2, two levels: project index + per-entry detail page. Each detail page: mark image(s), patent drawing(s), prose essay, primary source links (TSDR serial, Google Patents).

2. **GitHub Pages** — `gh-pages` branch or `docs/` folder; single `make publish` (or equivalent) regenerates and pushes.

3. **Open Graph metadata** — entries share cleanly on social/web; pages are crawlable.

**Phase gate:** `information-systems` project is live at a stable URL with at least 3 entries.

---

## Research Agenda — Information Systems Project

### Candidate subjects (marks in the database)

| Mark | Serial | Filed | Company | Patent connection |
|---|---|---|---|---|
| SOUNDEX | 71246709 | 1927-03-31 | Rand Kardex Bureau | Russell 1918, Odell 1922 — phonetic indexing ✅ confirmed |
| SOUNDEX QUICK AS A FLASH | 71255821 | 1927-10-08 | Rand Kardex Bureau | Odell 1922 ✅ confirmed |
| KARDEX | 71467213 | 1939-12-14 | Remington Rand | Visible card-index patent cluster 1930–1939 — essay written |
| VARIADEX | 71461278 | 1939-04-07 | Remington Rand | US2152606A Card Index (1939) — essay written |
| VI-DEX | 71235764 | 1927-02-22 | Wilson Jones | Visible index products; candidate patents in B42F 1926–1927 |
| REDIREF | 71237470 | 1927-09-19 | Wilson Jones | Quick-reference filing; filed same day as HANDIREF |
| HANDIREF | 71237469 | 1927-09-19 | Wilson Jones | Quick-reference filing; filed same day as REDIREF |
| SHANNON | ~1930 | 1930 | Yawman & Erbe | Shannon lever-arch file brand; still manufactured today |
| SMEAD'S TELL VISION SYSTEM | 71403472 | 1938-02-26 | Smead Mfg. | Visible record system; entity not yet in registry |
| WHEELDEX | 71321669 | 1931-12-01 | Unknown | Rotary card file |

### Discovery methodology

1. Add target company to `entities.duckdb` (procedure in `README.md`)
2. Run `python -m match information-systems` to generate candidates
3. Review `candidates.jsonl` — filter to product-name marks (not company names), high score, date overlap
4. Confirm pair: add entry to `confirmed.jsonl`, write essay in `content/`
5. Fetch patent PDF from Google Patents for primary source; enhance mark image via `image_tools/`

### Key reference works

- JoAnne Yates, *Control Through Communication* (1989) — filing systems and business communication 1880–1920
- JoAnne Yates, *Structuring the Information Age* (2005) — IBM and tabulating systems
- James W. Cortada, *Before the Computer* (1993) — IBM, NCR, Burroughs, Remington Rand
- Geoffrey Austrian, *Herman Hollerith* (1982) — punched card and tabulating history
- Alfred D. Chandler Jr., *The Visible Hand* (1977) — the management systems that created demand for information products

---

## Output Format Standards

| Format | When used | Notes |
|---|---|---|
| PNG (4×, ~3200px) | All enhanced marks | Print-ready at 300 DPI; universal |
| SVG | Clean word marks and geometric designs only | Skipped when illustration content is present |
| PDF | Patent documents | Downloaded from Google Patents |
| HTML (gallery) | Browsing output | Self-contained, base64-embedded; not for web publication |
| HTML (site) | Publication output | Referenced images, crawlable, Open Graph (Phase 3) |
| Markdown | Research essays, README | Tracked in git |

---

## Version History

| Tag | Notes |
|---|---|
| v0.2.0-alpha | TSDR mark_case_status, patents.duckdb (EPO OPS, B42F+B42D), entities.duckdb, match pipeline, STATUS.md, DEFERRED.md |
| v0.1.1-alpha | image_tools pipeline, /enhance-marks skill, historian specialist, projects/ tree |
| v0.1.0-alpha | TSDR client, trademarks.duckdb build, mark image retrieval |
