# Project Context

Working notes and decisions for the markery project. See README.md for stable reference documentation.

## Database: trademarks.duckdb

Built from the 2011 USPTO Trademark Case Files Dataset, filtered to applications filed 1900–1939. 25,473 case records.

### mark_images table

Stores trademark drawing images fetched from the TSDR API. Added after the initial database build.

```sql
CREATE TABLE mark_images (
    serial_no    VARCHAR PRIMARY KEY,
    image_data   BLOB NOT NULL,
    image_format VARCHAR NOT NULL,   -- MIME type, e.g. 'image/png'
    image_size   INTEGER NOT NULL,   -- byte length
    fetched_dt   DATE NOT NULL DEFAULT CURRENT_DATE
);
```

Images are stored as raw bytes directly in the BLOB column. To use in Python:

```python
import duckdb
conn = duckdb.connect("trademarks.duckdb")
row = conn.execute("SELECT image_data FROM mark_images WHERE serial_no = ?", ["71165547"]).fetchone()
png_bytes = bytes(row[0])
```

Note: DuckDB's `length()` function does not accept BLOB — use `image_size` instead, or cast: `octet_length(image_data)`.

### Images available for historical marks

The TSDR `rawImage` endpoint returns PNG images even for marks whose paper files are destroyed. All 1900–1939 design marks tested successfully returned images.

Typical image size for scanned historical marks: 6–8 KB, ~750–900px wide.

## Drawing Code Discrepancy

Two different drawing code formats appear in this project:

| Source | Format | Example |
|---|---|---|
| CSV dataset (`case_file.mark_draw_cd`) | 4-character alphanumeric | `3000`, `5W23`, `5000` |
| TSDR API (`markDrawingCd`) | Single digit | `3`, `5` |
| Daily XML (`apc260504.xml`) | Single digit | `3`, `5` |

The first digit of the CSV code matches the API/XML single digit. Filter queries use the CSV format.

## Status Code Discrepancy

The CSV dataset uses numeric status codes (e.g. `626`, `710`). The TSDR API also returns these, plus a separate `tm5Status` field (0–15 range) with `tm5StatusDesc` — these are EUIPO-harmonized codes and can be ignored for most purposes.

## Data Gaps

- **No events/correspondence table**: The `event.csv` and `correspondent_domrep_attorney.csv` files (combined ~3 GB) were not loaded into the database. These contain prosecution history events and attorney information.
- **No foreign_app table**: Madrid Protocol and foreign application data not loaded.
- **No statement table in initial build**: The `statement` table (goods/services text) was appended after the initial build.

## Known Quirks

- Six marks in the 1900–1939 scope show status 626/624 (live) in the 2011 snapshot. These are still technically registered.
- Owner names are inconsistently cased in the CSV data (e.g. `Guild Products Corporation` vs `GUILD PRODUCTS CORPORATION` for the same entity). Use `UPPER()` for matching.
- `serial_no` is stored as VARCHAR throughout, not INTEGER.
- The `owner` table has multiple rows per `serial_no` when ownership was transferred. Join carefully; use `own_entity_cd` or `partyType` to distinguish applicant vs. subsequent owner.
