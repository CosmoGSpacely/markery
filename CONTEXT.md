# Project Context

Working notes and decisions for the markery project. For stable reference documentation see `README.md`; for API details see `EPO.md` and `TSDR.md`.

---

## Project Focus

Markery is a **patent-trademark cross-reference tool** for early 20th-century American commercial history. The core operation is: given a company that both patented products and trademarked product names in the 1900–1939 period, identify which patents correspond to which trademarks, and document what that correspondence reveals about the commercial life of the technology.

The analytical unit is a **confirmed patent-trademark pair** — a specific patent and a specific trademark, for the same entity, where the patent describes the technical invention underlying the named product. These pairs are recorded in `projects/<project>/matches/confirmed.jsonl` and developed into research essays in `projects/<project>/content/`.

The current research project is `information-systems`: the filing cabinets, card-index systems, visible records equipment, tabulating machines, and phonetic coding schemes of the pre-computer era.

### The three-database architecture

- `trademarks.duckdb` — what companies called their products and when they entered commerce
- `patents.duckdb` — what was technically novel and who owned it
- `entities.duckdb` — the cross-reference hub: maps all name variants to canonical entities, enabling ATTACH queries that join across both databases

Adding a new company to the analysis means adding it to `build_entities_db.py` (one entry in `ENTITIES`, several in `VARIANTS`) and re-running `python build_entities_db.py`.

---

## trademarks.duckdb — Working Notes

### Two-tier TSDR fetch approach

The project uses two TSDR tables depending on whether the mark has a visual image:

**Primary: marks with images** — design marks (3xxx) and stylized marks (5xxx). These have scanned drawings in the TSDR `rawImage` store and are the primary visual research targets. Fetched into `mark_images`.

**Supplementary: text-only marks** — typeset marks (1xxx) and standard character marks (4xxx). The `rawImage` endpoint returns 404 for these because there is no drawing to scan. Full case status (filing dates, goods/services description, first-use dates) is fetched from the TSDR case status endpoint and stored in `mark_case_status`. These are brought in for analysis when they belong to the same entity and trademark class as a primary image mark — they are the product name marks (KARDEX, LINEDEX, FAVORITE, SHANNON) whose histories the research essays document.

### mark_images table

Stores trademark drawing images fetched from the TSDR `rawImage` endpoint. Populated for design and stylized marks.

```sql
CREATE TABLE mark_images (
    serial_no    VARCHAR PRIMARY KEY,
    image_data   BLOB NOT NULL,
    image_format VARCHAR NOT NULL,   -- MIME type, e.g. 'image/png'
    image_size   INTEGER NOT NULL,   -- byte length
    fetched_dt   DATE NOT NULL DEFAULT CURRENT_DATE
);
```

Images are stored as raw bytes. To use in Python:

```python
row = conn.execute("SELECT image_data FROM mark_images WHERE serial_no = ?", ["71165547"]).fetchone()
png_bytes = bytes(row[0])
```

Note: DuckDB's `length()` does not accept BLOB. Use `image_size` or `octet_length(image_data)`.

### mark_case_status table

Stores parsed case status data for typeset marks that have no image. Fetched from the TSDR JSON case status endpoint (`/ts/cd/casestatus/sn{serial}/info`).

```sql
CREATE TABLE mark_case_status (
    serial_no           VARCHAR PRIMARY KEY,
    mark_text           VARCHAR,
    filing_dt           DATE,
    registration_no     VARCHAR,
    registration_dt     DATE,
    status_cd           VARCHAR,
    goods_desc          VARCHAR,    -- first goods/services description
    intl_class          VARCHAR,    -- Nice class code(s), comma-separated
    first_use_dt        VARCHAR,   -- ISO 8601 reduced precision (see below)
    first_use_comm_dt   VARCHAR,   -- ISO 8601 reduced precision (see below)
    raw_json            VARCHAR,    -- full JSON response for future extraction
    fetched_dt          DATE NOT NULL DEFAULT CURRENT_DATE
);
```

Fields come from `trademarks[0].status` (mark_text, filing_dt, registration_no, status_cd) and `trademarks[0].gsList[0]` (goods_desc, intl_class, first_use dates).

First-use dates are stored as **ISO 8601 reduced precision VARCHAR** to preserve the precision actually recorded:

| Stored value | Meaning |
|---|---|
| `"1916-01-15"` | Full date — year, month, and day all specified |
| `"1924-01"` | Month precision — applicant specified year and month only (day field was `00` in the API) |
| `"1885"` | Year precision — applicant specified year only |

The API returns these as integers (e.g. `19160115`, `19240100`, `18850000`). Day `00` and month `00` were permitted under USPTO rules and indicate the applicant did not specify that component. Coercing `00` to `01` would introduce false precision; the reduced-precision string representation is exact. For date range queries, `CAST(LEFT(first_use_comm_dt, 4) AS INTEGER)` extracts the year reliably regardless of precision.

### Images available for historical marks

The TSDR `rawImage` endpoint returns PNG images for design and stylized marks even when the paper file is destroyed. Typeset marks (1xxx) return 404 — no image was ever filed with the application, so there is nothing to retrieve. Typical image size for a scanned historical mark: 6–8 KB, ~750–900px wide.

### Drawing code discrepancy

| Source | Format | Example |
|---|---|---|
| CSV dataset (`case_file.mark_draw_cd`) | 4-character | `3000`, `5W23` |
| TSDR API (`markDrawingCd`) | Single digit | `3`, `5` |

The first character of the CSV code matches the API single digit. All filter queries use the CSV format.

### Status code discrepancy

The CSV dataset uses numeric codes (e.g. `626`, `710`). The TSDR API returns these plus a `tm5Status` field (0–15, EUIPO-harmonized) with `tm5StatusDesc`. Ignore `tm5Status` for most purposes.

### Owner table joins

The `owner` table has multiple rows per `serial_no` when ownership was transferred. Join carefully — use `own_entity_cd` or filter by `own_type_cd` to distinguish original applicant from subsequent owners.

### Known quirks

- Six marks in the 1900–1939 scope show status 626/624 (live) in the 2011 snapshot.
- Owner names are inconsistently cased (`Guild Products Corporation` vs `GUILD PRODUCTS CORPORATION` for the same entity). Use `UPPER()` for matching.
- `serial_no` is stored as `VARCHAR` throughout, not `INTEGER`.
- Physical prosecution files for many early marks are marked `FILE DESTROYED` in the TSDR system. Mark images are often still available even when the file is destroyed.

### Data gaps

- **No events table**: `event.csv` (~3 GB) was not loaded. Contains prosecution history.
- **No foreign_app table**: Madrid Protocol and foreign application data not loaded.
- `statement.csv` (goods/services text) was appended after the initial build, not in the original `build_trademarks_db.py` run.

---

## patents.duckdb — Working Notes

Source is EPO OPS (Open Patent Services) API, not PatentsView. PatentsView was decommissioned in March 2026; EPO OPS is the replacement. See `EPO.md` for full details.

CPC classification was applied retroactively to pre-2013 patents by algorithmic mapping from USPC. Broad class assignments (e.g. B42F) are reliable; fine subgroup precision is variable for pre-1940 material.

Assignee names come in `epodoc` format: uppercase with country suffix, e.g. `SHAW WALKER CO [US]`. Some patents have no assignee (individual inventors only). Abstracts are NULL for virtually all pre-1970 patents.

Currently populated: **B42F** (filing appliances) and **B42D** (books, forms, index cards), 1900–1939, 11,284 patents. Five additional CPC classes are defined in `build_patents_db.py` but not yet fetched: B41J, B41L, G06C, G06K, G09F.

---

## entities.duckdb — Working Notes

Deduplication in `build_entities_db.py` keys on `(entity_id, variant_name, source)`. A company name that appears as both a `patent_assignee` and a `trademark_owner` needs two separate rows — one per source. The dedup check must include `source` or the second insert will be silently skipped.

When adding a new entity:
1. Add a tuple to `ENTITIES` with the next sequential `entity_id`.
2. Add tuples to `VARIANTS` for every spelling found in each database. Query both databases first to enumerate exact spellings — do not guess.
3. Add the `entity_id` to the relevant project's `entities.txt`.
4. Re-run `python build_entities_db.py`.
5. Re-run `python -m match <project>` to regenerate candidates.

---

## match/ — Working Notes

`match/score.py` scoring components:
- **date_order / date_proximity** (max 0.5): patent grant precedes trademark filing → positive; trademark filed before patent → slight negative (not disqualifying — brand names sometimes preceded the specific patent).
- **class_signal** (0.3 if any CPC class is in the product signal set): B42F, B42D, B41J, B41L, G06C, G06K, G09F.
- Maximum score: 0.80.

High-score pairs (0.70+) where the trademark name is a product name (not a company name like REMINGTON or RAND) are the primary candidates for promotion to `confirmed.jsonl`. Company-name marks score high because every patent in the window matches them, but they are not product-level correspondences.

`candidates.jsonl` is regenerated on every run and is not a curation surface — do not edit it. All curation goes into `confirmed.jsonl`.
