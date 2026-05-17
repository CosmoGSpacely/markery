# Markery Database Reference

The `trademarks.duckdb` database contains 25,473 USPTO trademark applications filed 1900–1939, built from the 2011 USPTO Trademark Case Files Dataset. Connect with DuckDB.

```python
import duckdb
conn = duckdb.connect("data/trademarks.duckdb", read_only=True)
```

---

## Tables

### case_file — Core application record
One row per trademark application.

| Column | Type | Notes |
|---|---|---|
| `serial_no` | VARCHAR | Primary key. 8-digit USPTO serial number. |
| `mark_id_char` | VARCHAR | The mark text (word marks). Null for pure design marks. |
| `mark_draw_cd` | VARCHAR | Drawing code — see `mark-drawing-codes.md` |
| `filing_dt` | DATE | Application filing date |
| `cfh_status_cd` | INTEGER | Current status — see `status-codes.md` |
| `registration_no` | VARCHAR | Registration number if granted (zero-padded, 7 chars) |
| `registration_dt` | DATE | Date of registration |

### owner — Applicant and owner information
Multiple rows per `serial_no` when ownership transferred.

| Column | Type | Notes |
|---|---|---|
| `serial_no` | VARCHAR | Foreign key to case_file |
| `own_id` | INTEGER | Owner sequence number |
| `own_name` | VARCHAR | Owner name — inconsistently cased; use `UPPER()` for matching |
| `own_entity_cd` | INTEGER | Entity type (01=individual, 02=corporation, etc.) |
| `own_addr_1` | VARCHAR | Street address |
| `own_addr_2` | VARCHAR | City, state — often contains additional descriptive text |

### statement — Goods and services descriptions
| Column | Type | Notes |
|---|---|---|
| `serial_no` | VARCHAR | Foreign key to case_file |
| `statement_type_cd` | VARCHAR | Type of statement |
| `statement_text` | VARCHAR | Full text of goods/services description |

### classification — Classification with first-use dates
| Column | Type | Notes |
|---|---|---|
| `serial_no` | VARCHAR | Foreign key to case_file |
| `class_id` | INTEGER | Key to intl_class and us_class |
| `first_use_any_dt` | DATE | Earliest known use anywhere |
| `first_use_com_dt` | DATE | First use in interstate commerce |

### intl_class — International (Nice) class codes
Joined via `class_id`.

### us_class — US class codes
Joined via `class_id`.

### design_search — Design search codes
Visual element classification for design marks.

| Column | Type | Notes |
|---|---|---|
| `serial_no` | VARCHAR | Foreign key to case_file |
| `design_search_cd` | VARCHAR | 6-digit code; first 2 digits = category |

### mark_images — Trademark drawing images
PNG images fetched from the TSDR API.

| Column | Type | Notes |
|---|---|---|
| `serial_no` | VARCHAR | Primary key, foreign key to case_file |
| `image_data` | BLOB | Raw PNG bytes |
| `image_format` | VARCHAR | MIME type (always `image/png`) |
| `image_size` | INTEGER | Byte length — use this instead of `length()` |
| `fetched_dt` | DATE | Date retrieved from TSDR |

```python
# Read an image
row = conn.execute("SELECT image_data FROM mark_images WHERE serial_no = ?", ["71165547"]).fetchone()
png_bytes = bytes(row[0])
```

---

## Common Query Patterns

### Find a company by owner name
```sql
SELECT cf.serial_no, cf.mark_id_char, cf.filing_dt, cf.cfh_status_cd
FROM case_file cf
JOIN owner o ON cf.serial_no = o.serial_no
WHERE UPPER(o.own_name) LIKE '%COMPANY NAME%'
ORDER BY cf.filing_dt;
```

### Find marks by goods description keyword
```sql
SELECT cf.serial_no, cf.mark_id_char, cf.filing_dt, s.statement_text, o.own_name
FROM case_file cf
JOIN statement s ON cf.serial_no = s.serial_no
JOIN owner o ON cf.serial_no = o.serial_no
WHERE LOWER(s.statement_text) LIKE '%keyword%'
ORDER BY cf.filing_dt;
```

### Get classification details
```sql
SELECT cf.serial_no, cf.mark_id_char, ic.intl_class_cd, uc.us_class_cd,
       c.first_use_any_dt, c.first_use_com_dt
FROM case_file cf
LEFT JOIN classification c USING (serial_no)
LEFT JOIN intl_class ic USING (class_id)
LEFT JOIN us_class uc USING (class_id)
WHERE cf.serial_no = '71165547';
```

### Design marks only, with design search codes
```sql
SELECT cf.serial_no, cf.mark_id_char, cf.mark_draw_cd, ds.design_search_cd,
       cf.filing_dt, o.own_name
FROM case_file cf
JOIN design_search ds ON cf.serial_no = ds.serial_no
JOIN owner o ON cf.serial_no = o.serial_no
WHERE cf.mark_draw_cd LIKE '3%' OR cf.mark_draw_cd LIKE '2%'
ORDER BY cf.filing_dt;
```

### Filing volume by year
```sql
SELECT YEAR(filing_dt) AS year, COUNT(*) AS filings
FROM case_file
GROUP BY year
ORDER BY year;
```

---

## Notes

- `serial_no` is VARCHAR throughout. Cast explicitly if needed.
- Owner names are inconsistently cased in the source data. Always use `UPPER()` or `LOWER()` for string matching.
- The `owner` table has multiple rows per `serial_no` when ownership transferred. A bare `JOIN` can multiply rows. Filter by `own_id = 1` for original applicant only, or aggregate intentionally.
- `mark_id_char` is null for pure design marks — don't filter it to find word marks without also checking `mark_draw_cd`.
- DuckDB does not support `length(BLOB)` — use the `image_size` column in `mark_images` instead.
