# EPO Open Patent Services — Reference and Project Log

## What EPO OPS Is

EPO Open Patent Services (OPS) is the European Patent Office's public REST API for patent data. It provides programmatic access to the EPO's worldwide patent database (DOCDB), which covers patents from 1790 to the present across all major jurisdictions. For this project it is the primary source for US patent data from 1900–1939 — a period not covered at the record level by any freely accessible USPTO API.

Registration is free at https://developers.epo.org. The free tier allows 4 GB of data per week, which is sufficient for bulk historical research queries.

Credentials go in `.env`:
```
EPO_CONSUMER_KEY=your_key_here
EPO_CONSUMER_SECRET=your_secret_here
```

---

## Authentication

EPO OPS uses OAuth2 client-credentials flow. Tokens expire in 1200 seconds (20 minutes).

**Token request:**
```
POST https://ops.epo.org/3.2/auth/accesstoken
Authorization: Basic base64(key:secret)
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "token_type": "Bearer",
  "expires_in": 1199
}
```

**Subsequent requests:**
```
Authorization: Bearer <access_token>
Accept: application/json
```

`EPOClient` in `build_patents_db.py` handles this automatically, refreshing the token 60 seconds before expiry. Tokens are stored in memory only — there is no disk cache.

---

## Endpoints Used

### Bibliographic search
```
GET https://ops.epo.org/3.2/rest-services/published-data/search/biblio
```

Returns full bibliographic data (title, dates, parties, CPC classifications) directly in search results. The `/search` endpoint without `/biblio` returns references only and requires a separate fetch per patent; `/search/biblio` avoids that round-trip and is what `build_patents_db.py` uses.

**Pagination header:** `X-OPS-Range: 1-100` (1-indexed, inclusive). Maximum 100 results per request. Hard cap of 2000 results per CQL query — queries that would return more must be subdivided.

**Query parameter:** `q=<CQL expression>`

### Single-patent bibliographic lookup
```
GET https://ops.epo.org/3.2/rest-services/published-data/publication/epodoc/{id}/biblio
```

Used in `test_epo_ops.py` to fetch a known patent by publication number for credential verification.

---

## CQL (Common Query Language)

CQL is the query language for EPO OPS searches. The syntax used in this project:

```
cpc=B42F AND pd within "19180101,19181231" AND pn=US
```

| Operator | Meaning |
|---|---|
| `cpc=B42F` | Any patent where B42F is an assigned CPC symbol (including subgroups like B42F17/02) |
| `pd within "YYYYMMDD,YYYYMMDD"` | Publication/grant date range, inclusive |
| `pn=US` | US patents only |
| `AND` | Boolean conjunction |

**5-year windows** are used to stay well under the 2000-result cap per query. The builder automatically subdivides to 1-year windows if a window exceeds 2000 results.

---

## JSON Response Structure

All text values in the OPS JSON response are wrapped in objects with a `$` key:
```json
{ "invention-title": { "$": "Filing Cabinet", "@lang": "en" } }
```
This is different from the XML-to-JSON convention used by some other APIs where text lives in `#text`. The helper `_text(v)` in `build_patents_db.py` handles this.

Attribute fields use `@attr` keys (e.g., `@country`, `@doc-number`, `@scheme`).

### Search result envelope
```
ops:world-patent-data
  ops:biblio-search
    @total-result-count       total matching patents (string, not int)
    ops:search-result
      exchange-documents      list of result wrappers, or single dict if 1 result
        exchange-document     the patent document (or list of family members)
          @country
          @doc-number
          @kind               A, B, etc.
          bibliographic-data
            publication-reference
              document-id[]   contains grant date (look for @document-id-type = "docdb")
            application-reference
              document-id[]   contains application date
            invention-title   string or list (multiple languages)
            parties
              applicants
                applicant[]   @data-format = "epodoc" gives clean assignee name
              inventors
                inventor[]    @data-format = "epodoc" gives clean inventor name
            patent-classifications
              patent-classification[]
                classification-scheme   @scheme = "CPCI" for CPC
                section / class / subclass / main-group / subgroup
```

### Parsing notes

- `exchange-documents` is a list when multiple results are returned, a single dict when exactly one result is returned. The `_list()` helper normalises both cases.
- Each `exchange-document` may itself be a list when a patent family has multiple members. The builder takes the first US-country member.
- Inventor and applicant entries come in multiple `@data-format` variants (`docdb`, `epodoc`, `original`). The `epodoc` format gives the cleanest names and is the one stored. Storing all formats produces duplicate rows.
- CPC classification scheme is `"CPCI"` (uppercase) in the response — not `"CPC"` or `"cpci"`. The scheme check is case-insensitive: `scheme.upper() in ("CPC", "CPCI")`.
- The full CPC symbol is constructed by concatenating `section + class + subclass + main-group + "/" + subgroup` (e.g., `B42F13/12`).

---

## Rate Limits and Fair Use

The free tier quota is 4 GB/week of response data. In practice, for bibliographic search results (no full text), this is far more than needed for the 1900–1939 US patent corpus.

The builder sleeps 0.5 seconds between requests (`RATE_SLEEP`). On a 503 response (throttling), it retries with delays of 5, 15, and 30 seconds before giving up.

The EPO OPS service agreement requires fair use. Running bulk fetches outside business hours is good practice.

---

## Data Coverage and Quality

EPO OPS covers US patents from 1790 onwards. CPC classifications were applied retroactively to pre-2013 patents by algorithmic mapping from the original USPC (United States Patent Classification) and IPC (International Patent Classification) systems. Quality notes:

- **Broad class assignments** (e.g., B42F) are generally reliable for patents from 1900–1939.
- **Fine subgroup precision** (e.g., B42F13/12 vs B42F13/26) is less consistent for pre-1940 material — the retroactive mapping was automated.
- **Assignee names** for pre-1940 patents come in uppercase with country suffix (e.g., `SHAW WALKER CO [US]`), which is the `epodoc` format. Some patents have no assignee (individual inventors only).
- **Application dates** are often missing for very early patents — the application filing system was less standardised before ~1910.
- **Abstracts** are rarely present for patents before the 1970s. The `abstract` column is NULL for nearly all patents in the current dataset.

---

## Alternative Sources Investigated (and Why EPO OPS Was Chosen)

Before settling on EPO OPS, the following sources were exhausted:

| Source | Status | Reason unusable |
|---|---|---|
| PatentsView API (`search.patentsview.org`) | NXDOMAIN | Decommissioned March 2026 as part of USPTO migration |
| `patft.uspto.gov` | Resolves to `10.10.10.10` | USPTO internal IP — inaccessible from public internet |
| `ppubs.uspto.gov` | Returns "Fixed response content" | Decommissioned March 2026 |
| `data.uspto.gov` | Returns HTML for all API paths | JavaScript SPA, not a REST API |
| Google Patents | 503 after ~5 queries | IP rate-limited; structured queries (date filters, assignee:) blocked |
| The Lens (lens.org) | 14-day trial only | No free permanent API |

PatentsView also only covered 1976–present at the record level, making it unsuitable for 1900–1939 research regardless of availability.

The full account of this investigation, with a Dickens-style illustration of the `patft.uspto.gov → 10.10.10.10` moment, is at [`projects/information-systems/patent-data-expedition.html`](projects/information-systems/patent-data-expedition.html).

---

## Current Data: patents.duckdb

**Populated classes:** B42F, B42D  
**Year range:** 1900–1939  
**Total patents:** 11,284

| Class | Description | Patents |
|---|---|---|
| B42F | Filing appliances, card-index systems, loose-leaf binders | ~7,100 |
| B42D | Books, printed matter, forms, index cards, ledger sheets | ~4,200 |

**Planned classes** (not yet fetched — see D001 in `DEFERRED.md` for reopen trigger):

| Class | Description |
|---|---|
| B41J | Typewriters, selective printing mechanisms |
| B41L | Addressing and duplicating machines for office use |
| G06C | Mechanical calculators, tabulating machines |
| G06K | Punched cards, record carriers, recognition of data |
| G09F | Displaying, advertising, visible record systems, signs |

To fetch additional classes when the trigger condition is met:
```bash
python build_patents_db.py --classes B41J B41L --resume
```

### Schema

```sql
patents (
    patent_no      VARCHAR PRIMARY KEY,   -- e.g. US1261167A
    title          VARCHAR,
    app_dt         DATE,                  -- application date (often NULL pre-1910)
    grant_dt       DATE,
    abstract       VARCHAR,               -- NULL for nearly all pre-1970 patents
    assignee_name  VARCHAR,               -- epodoc format, e.g. "SHAW WALKER CO [US]"
    assignee_city  VARCHAR,               -- currently NULL (not in OPS biblio)
    assignee_state VARCHAR                -- currently NULL
)

patent_classes (
    patent_no  VARCHAR NOT NULL,
    cpc_class  VARCHAR,    -- 4-char prefix, e.g. B42F
    cpc_full   VARCHAR     -- full symbol, e.g. B42F17/02
)

patent_inventors (
    patent_no     VARCHAR NOT NULL,
    inventor_name VARCHAR            -- epodoc format, e.g. "HUNTER DAVID E [US]"
)

fetch_log (
    cpc_class     VARCHAR,
    year_start    INTEGER,
    year_end      INTEGER,
    fetch_dt      TIMESTAMP,
    patents_added INTEGER
)
```

### Seed patents

Two patents are hardcoded as seed data and loaded without API calls (`--seed-only`). Both have manually written abstracts since OPS returns no abstract for pre-1940 patents:

| Patent | Inventor | Assignee | Subject |
|---|---|---|---|
| US1261167A | Robert C. Russell | Remington Typewriter Company | Soundex phonetic indexing system (1918) |
| US1435663A | Margaret K. Odell | Remington Typewriter Company | Improved Soundex (1922) |

---

## Cross-Reference with Trademarks: entities.duckdb

`entities.duckdb` maps canonical company names to all name variants found in `patents.duckdb` (assignee field) and `trademarks.duckdb` (owner field). DuckDB's `ATTACH` allows cross-database queries without copying data.

### Schema

```sql
company_entity (
    entity_id      INTEGER PRIMARY KEY,
    canonical_name VARCHAR NOT NULL,
    entity_type    VARCHAR,   -- 'manufacturer', 'publisher', 'individual'
    industry       VARCHAR,   -- 'office-systems', 'blank-books', etc.
    notes          VARCHAR
)

entity_name_variant (
    variant_id   INTEGER PRIMARY KEY,
    entity_id    INTEGER NOT NULL,
    variant_name VARCHAR NOT NULL,
    source       VARCHAR NOT NULL   -- 'patent_assignee' | 'trademark_owner' | 'canonical'
)
```

### Current entities

**Remington Rand** (entity_id 1) — the test case. Formed 1927 by merger of Remington Typewriter Company and Rand Kardex Bureau. Dominant producer of visible card-index systems, filing cabinets, and loose-leaf binders through the 1930s. Merged into Sperry Rand 1955.

Patent assignee variants stored:
- `Remington Typewriter Company`
- `REMINGTON TYPEWRITER CO [US]`
- `REMINGTON TYPEWRITER CO`
- `REMINGTON RAND INC`
- `FIRM REMINGTON RAND INC`

Trademark owner variants stored:
- `REMINGTON TYPEWRITER COMPANY, THE`
- `REMINGTON RAND INC.`
- `REMINGTON RAND BUSINESS SERVICE, INC.`
- `Remington Rand Corporation`

### Example cross-database query

```python
import duckdb
conn = duckdb.connect("data/entities.duckdb", read_only=True)
conn.execute("ATTACH 'data/patents.duckdb'    AS pat (READ_ONLY)")
conn.execute("ATTACH 'data/trademarks.duckdb' AS tm  (READ_ONLY)")

# All trademarks filed by Remington Rand entities
conn.execute("""
    SELECT e.canonical_name, cf.mark_id_char, cf.filing_dt, cf.registration_no
    FROM company_entity e
    JOIN entity_name_variant v ON e.entity_id = v.entity_id
                               AND v.source = 'trademark_owner'
    JOIN tm.owner o  ON o.own_name = v.variant_name
    JOIN tm.case_file cf ON cf.serial_no = o.serial_no
    ORDER BY cf.filing_dt
""").fetchall()
```

### Known trademark–patent matches (Remington Rand)

| Trademark | Reg# | Filed | Correspondence in patents.duckdb |
|---|---|---|---|
| REMRANDCO | 0262537 | 1929 | Company name abbreviation mark |
| LINEDEX | 0289923 | 1931 | Line-based index filing system products |
| SCOTTIE | 0323202 | 1934 | Specific product line (unidentified) |
| ARISTOCRAT | 0345996 | 1937 | Premium binder/index product line |
| VARIADEX | 0371824 | 1939 | Variable/rotary index products |
| RAND | 0375203 | 1939 | Company name mark |
| REMINGTON | 0374758 | 1939 | Company name mark |
| KARDEX | 0377986 | 1939 | Visible card-index tray system — directly corresponds to visible index patents cluster 1930–1939 |

### Other companies with confirmed trademark+patent presence

Identified through cross-reference of top B42F/B42D patent assignees against `trademarks.duckdb`:

| Company | Patents | Key trademarks |
|---|---|---|
| Wilson Jones Co | 105 | VI-DEX, REDIREF, HANDIREF (all 1927), LEATHER LIFE (1932) |
| Yawman & Erbe Mfg Co | 31 | SHANNON (1930), Y AND E (1930) |
| Boorum & Pease Company | 32 | B&P (1914), STANDARD B&P BLANK BOOKS AND LOOSE LEAF DEVICES (1921), BULLDOG (1924) |
| Library Bureau | 17 | ARMORCLAD (1924), AUTOMATIC (1924), LB (1925) |
| Acme Card System Co | 33 | ACME (1935) |

All four companies are currently active in the `information-systems` project. Additional candidates (Library Bureau, Acme Card System Co, Smead Mfg.) are not yet in the registry.

---

## Project Structure

```
markery/
├── build_db.py                     Trademark database builder (trademarks.duckdb)
├── build_patents_db.py             Patent database builder (EPO OPS → patents.duckdb)
├── build_entities_db.py            Entity registry builder (entities.duckdb)
├── test_epo_ops.py                 EPO OPS credential smoke-test
├── tsdr_client.py                  USPTO TSDR API client (trademark status/documents)
│
├── patents.duckdb                  US patents 1900–1939, B42F+B42D, 11,284 records
├── trademarks.duckdb               USPTO trademark data (case_file, owner, etc.)
├── entities.duckdb                 Canonical company registry; cross-references both DBs
│
├── CONTEXT.md                      Project overview
├── ROADMAP.md                      Near-term plans and research agenda
├── EPO.md                          This file
├── TSDR.md                         USPTO TSDR API reference
├── requirements.txt
│
├── tools/
│   ├── image_enhancement/          Image processing pipeline for trademark scans
│   │   ├── pipeline.py             Orchestrates upscale → binarize → SVG
│   │   ├── upscale.py              Real-ESRGAN 4× upscaling
│   │   ├── binarize.py             Threshold/adaptive binarization
│   │   ├── gallery.py              HTML gallery generator
│   │   └── cli.py / __main__.py
│   ├── patent_docs/                Patent PDF fetch and text-signal scoring
│   └── historian/                  Specialist persona for research queries
│       ├── identity.md
│       ├── rules.md
│       ├── examples.md
│       └── reference/
│           ├── historical-context.md
│           ├── image-enhancement.md
│           ├── mark-drawing-codes.md
│       ├── markery-database.md
│       └── status-codes.md
│
├── projects/
│   ├── information-systems/
│   │   ├── README.md
│   │   ├── patent-data-expedition.html   Narrative account of data source search
│   │   ├── soundex-marks/
│   │   │   └── background.md             Research essay on Soundex trademark history
│   │   ├── input/                        (gitignored)
│   │   └── output/
│   │       ├── filing-systems/           Trademark mark images, filing-system companies
│   │       ├── soundex-marks/            Mark images + patent PDFs for Soundex research
│   │       └── stationery-marks/         Mark images, stationery/paper goods companies
│   │
│   └── monthly-image-review/
│       ├── README.md
│       ├── input/                        (gitignored)
│       └── output/
│           ├── may1930-designs/          May 1930 trademark image review
│           └── enhanced-may1930-designs/ Upscaled versions
│
├── csv/                            (gitignored) Raw USPTO TSDR CSV exports
├── input/                          (gitignored) Working input files
├── output/                         (gitignored) Working output files
└── .claude/
    └── commands/
        └── enhance-marks.md        /enhance-marks skill definition
```

---

## Environment Variables

| Variable | Used by | Purpose |
|---|---|---|
| `EPO_CONSUMER_KEY` | `build_patents_db.py`, `test_epo_ops.py` | EPO OPS OAuth2 client key |
| `EPO_CONSUMER_SECRET` | `build_patents_db.py`, `test_epo_ops.py` | EPO OPS OAuth2 client secret |
| `USPTO_API_KEY` | `tsdr_client.py` | USPTO TSDR API static key |

All loaded from `.env` via `python-dotenv`. The `.env` file is gitignored.

---

## Quick-Start Commands

```bash
# Test EPO credentials
python test_epo_ops.py

# Rebuild patents.duckdb from scratch (B42F + B42D, 1900–1939)
rm data/patents.duckdb
python src/markery/db/build_patents_db.py --seed-only
python src/markery/db/build_patents_db.py --classes B42F B42D

# Fetch a single year window for testing
python src/markery/db/build_patents_db.py --classes B42F --year-start 1918 --year-end 1918

# Resume a partial build
python src/markery/db/build_patents_db.py --classes B42F B42D --resume

# Rebuild entities.duckdb
python src/markery/db/build_entities_db.py

# Cross-database query (from Python)
import duckdb
conn = duckdb.connect("data/entities.duckdb", read_only=True)
conn.execute("ATTACH 'data/patents.duckdb' AS pat (READ_ONLY)")
conn.execute("ATTACH 'data/trademarks.duckdb' AS tm (READ_ONLY)")
```
