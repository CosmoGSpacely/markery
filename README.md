# Markery

Research tool for studying American commercial history through the combined USPTO trademark and patent record. The project cross-references trademark registrations with patent filings for the same companies and time periods, producing documented patent-trademark pairs that reveal the commercial lifecycle of early 20th-century technologies.

The primary research focus is **pre-computer information systems** — the filing cabinets, card index systems, visible record equipment, tabulating machines, and phonetic coding schemes that American businesses used to organize knowledge before the digital era. These were significant industrial products, patented and trademarked at scale by major manufacturers, and almost entirely absent from the standard history of information technology.

**Period:** 1900–1939  
**Status:** v0.2.0-alpha

---

## Databases

Three DuckDB files form the data layer. All are committed to the repository.

### `trademarks.duckdb`
Built from the 2011 USPTO Trademark Case Files Dataset, filtered to applications filed 1900–1939.

| Table | Rows | Contents |
|---|---|---|
| `case_file` | 25,473 | Mark name, drawing code, filing/registration/status dates |
| `owner` | 38,349 | Applicant and owner names, addresses, entity type |
| `owner_name_change` | 8,600 | Ownership transfer history |
| `classification` | 25,497 | Classification records with first-use dates |
| `intl_class` | 28,119 | Nice international class codes |
| `us_class` | 26,188 | US class codes |
| `design_search` | 18,790 | Design search codes (visual element classification) |
| `prior_mark` | 11,329 | Prior mark references |
| `statement` | 35,077 | Goods and services descriptions |
| `mark_images` | varies | PNG mark images fetched from USPTO TSDR API (BLOB) |

Rebuilt by `build_trademarks_db.py` from CSV files in `csv/` (not committed — obtain from USPTO).

### `patents.duckdb`
Built from the EPO Open Patent Services API, covering US patents in CPC classes relevant to pre-computer information systems.

**Currently populated:** B42F (filing appliances, card-index systems), B42D (books, forms, index cards) — 11,284 patents, 1900–1939.

| Table | Contents |
|---|---|
| `patents` | Patent number, title, application date, grant date, assignee name |
| `patent_classes` | CPC class and full symbol per patent (multiple rows per patent) |
| `patent_inventors` | Inventor names (epodoc format) |
| `fetch_log` | Which CPC class + year windows have been fetched |

Rebuilt by `build_patents_db.py`. Requires `EPO_CONSUMER_KEY` and `EPO_CONSUMER_SECRET` in `.env`. Registration is free at https://developers.epo.org. See `EPO.md` for full API reference.

### `entities.duckdb`
Canonical company registry mapping organization names to all spelling variants found in the patent and trademark databases. The hub for cross-database queries.

| Table | Contents |
|---|---|
| `company_entity` | Canonical name, type, industry, notes (one row per company) |
| `entity_name_variant` | All name spellings, tagged by source (`patent_assignee` / `trademark_owner`) |

**Current entities:** Remington Rand, Wilson Jones, Yawman & Erbe, Boorum & Pease.

Rebuilt by `build_entities_db.py`. Idempotent — safe to re-run; skips existing rows.

#### Cross-database queries via ATTACH

```python
import duckdb
conn = duckdb.connect("entities.duckdb", read_only=True)
conn.execute("ATTACH 'patents.duckdb'    AS pat (READ_ONLY)")
conn.execute("ATTACH 'trademarks.duckdb' AS tm  (READ_ONLY)")

# Patents and trademarks for all known entities
conn.execute("""
    SELECT e.canonical_name,
           COUNT(DISTINCT p.patent_no)   AS patents,
           COUNT(DISTINCT cf.serial_no)  AS trademarks
    FROM company_entity e
    LEFT JOIN entity_name_variant vp ON e.entity_id = vp.entity_id
                                     AND vp.source = 'patent_assignee'
    LEFT JOIN pat.patents p ON p.assignee_name = vp.variant_name
    LEFT JOIN entity_name_variant vt ON e.entity_id = vt.entity_id
                                     AND vt.source = 'trademark_owner'
    LEFT JOIN tm.owner o   ON o.own_name = vt.variant_name
    LEFT JOIN tm.case_file cf ON cf.serial_no = o.serial_no
    GROUP BY 1
""").fetchall()
```

---

## Match Pipeline

`match/` generates scored patent-trademark candidate pairs for a project's entities.

```bash
# Generate candidates for the information-systems project
python -m match information-systems

# List all entities in the registry
python -m match --list-entities

# Single entity
python -m match --entity "Remington Rand"
```

Output is written to `projects/<project>/matches/candidates.jsonl` — one JSON object per candidate pair, scored by date proximity and CPC class relevance. Confirmed pairs are recorded by hand in `matches/confirmed.jsonl`.

The scoring model (`match/score.py`) gives highest weight to patents granted shortly before the trademark filing date, with a boost for CPC classes in the information-systems domain. Top score is 0.80 (patent granted within weeks of trademark filing).

---

## Image Enhancement

Mark images are fetched from the USPTO TSDR API and can be enhanced with the `image_tools` pipeline — 4× Real-ESRGAN upscaling, optional SVG vectorization via vtracer, HTML gallery output.

**Enhancement is a manual, selective step.** See `image_tools/ENHANCE.md` for the workflow. Do not run batch enhancement on unreviewed query results.

```bash
# Enhance specific serial numbers
python -m image_tools batch "cf.serial_no IN ('71246709','71255821')" \
  --out-dir projects/information-systems/output/soundex-marks

# Build gallery
python -m image_tools gallery projects/information-systems/output/soundex-marks \
  --title "Soundex Marks" --subtitle "2 marks · Rand Kardex Bureau, 1927"
```

---

## Research Projects

Projects live under `projects/` and are the unit of research output.

```
projects/
  information-systems/
    README.md               research scope
    entities.txt            entity IDs in scope (links to entities.duckdb)
    matches/
      candidates.jsonl      scored patent-trademark pairs (generated)
      confirmed.jsonl       curated confirmed pairs (committed)
    content/
      soundex.md            Soundex marks and the Russell/Odell patents
      kardex.md             KARDEX trademark and the visible-index patent cluster
    input/                  gitignored
    output/                 gitignored (images, PDFs, gallery HTML)
  monthly-image-review/
    README.md
    output/
      may1930-designs/      39 design marks filed May 1930
```

Research documents (`.md` essays, `README.md`, `confirmed.jsonl`) are tracked in git. Generated output (images, PDFs, gallery HTML) is gitignored.

---

## Setup

```bash
# 1. Clone and create virtualenv
git clone git@github.com:CosmoGSpacely/markery.git
cd markery
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Add API credentials to .env
echo "EPO_CONSUMER_KEY=your_key"     >> .env
echo "EPO_CONSUMER_SECRET=your_secret" >> .env
echo "USPTO_API_KEY=your_key"        >> .env

# 3. The three databases are committed — no rebuild needed to start.
#    To rebuild from scratch:
python build_entities_db.py
python build_patents_db.py --classes B42F B42D    # ~20 min
# build_trademarks_db.py requires the csv/ directory (USPTO bulk download)

# 4. Test EPO credentials
python test_epo_ops.py

# 5. Generate match candidates
python -m match information-systems
```

---

## Key Reference Docs

| File | Contents |
|---|---|
| `EPO.md` | EPO OPS API — auth, endpoints, CQL, response structure, rate limits, data quality |
| `TSDR.md` | USPTO TSDR API — mark image retrieval, case status |
| `CONTEXT.md` | Working notes — database quirks, known data issues |
| `ROADMAP.md` | Near-term plans, research agenda, candidate subjects |
| `image_tools/ENHANCE.md` | Mark image enhancement workflow |
