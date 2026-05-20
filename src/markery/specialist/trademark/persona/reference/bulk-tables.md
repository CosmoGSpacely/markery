# Trademark Bulk Tables Reference

`trademarks.duckdb` contains two layers: bulk tables loaded from the USPTO CSV source, and enrichment tables populated via the TSDR API.

Full schema details: `src/markery/specialist/trademark/TSDR.md`

---

## Bulk Tables (from USPTO CSV)

| Table | Key columns | Notes |
|---|---|---|
| `case_file` | `serial_no` (BIGINT), `mark_id_char`, `filing_dt`, `mark_draw_cd`, `cfh_status_cd` | One row per application. Primary key for the bulk layer. |
| `owner` | `serial_no`, `own_name`, `own_state` | Applicant and subsequent owners. Multiple rows per serial when ownership transfers. |
| `statement` | `serial_no`, `statement_text` | Goods and services description as filed. |
| `classification` | `serial_no`, `intl_code_total_no`, `first_use_any_dt`, `first_use_com_dt` | International classification and first-use dates. |
| `intl_class` | `serial_no`, `intl_class` | International class code(s). |
| `us_class` | `serial_no`, `us_class` | US class code(s). |
| `design_search` | `serial_no`, `design_search_code` | Design search codes for figurative marks. |
| `owner_name_change` | `serial_no`, `own_name` | Name changes on the same owner record. |
| `prior_mark` | `serial_no`, `other_mark` | Claims to earlier marks. |

`serial_no` in bulk tables is **BIGINT** (as delivered by the CSV source).

---

## Enrichment Tables (from TSDR API)

| Table | Key columns | Notes |
|---|---|---|
| `extended_marks` | `serial_no` (VARCHAR), `mark_text`, `filing_dt`, `goods_desc`, `status_cd`, `first_use_dt` | TSDR-fetched records. Covers both bulk marks (enriched status) and standalone TSDR fetches. `owner_name` is NULL for bulk-enrichment rows. |
| `mark_images` | `serial_no` (VARCHAR), `image_data` (BLOB), `image_format`, `image_size` | Mark drawing images fetched from TSDR. |

`serial_no` in enrichment tables is **VARCHAR** (as returned by the TSDR API). Cross-layer joins require casting: `CAST(cf.serial_no AS VARCHAR)`.

---

## On-demand Tables (created only when loaded)

These tables do not exist in `trademarks.duckdb` until explicitly loaded. A query against either before loading will error.

| Table | Created by | Contains |
|---|---|---|
| `events` | `markery trademark load-events --csv-dir csv/` | USPTO prosecution history: office actions, responses, publication, registration, maintenance |
| `foreign_app` | `markery trademark load-foreign --csv-dir csv/` | Madrid Protocol foreign application records: country, filing date, registration |

### `events` columns

| Column | Type | Notes |
|---|---|---|
| `serial_no` | BIGINT | Foreign key to `case_file.serial_no` |
| `event_dt` | DATE | Date the event occurred |
| `event_cd` | VARCHAR | Code (e.g. `NDOA` = new application, `PUBT` = published, `REGS` = registered) |
| `event_desc_t` | VARCHAR | Full text description |
| `party_cd` | VARCHAR | Party responsible (`AP` = applicant, `OA` = examiner office action) |

### `foreign_app` columns

| Column | Type | Notes |
|---|---|---|
| `serial_no` | BIGINT | Foreign key to `case_file.serial_no` |
| `foreign_appl_no` | VARCHAR | Foreign application number |
| `foreign_country_cd` | VARCHAR | ISO country code (`GB`, `DE`, `FR`, etc.) |
| `foreign_filing_dt` | DATE | Date of foreign filing |
| `foreign_reg_no` | VARCHAR | Foreign registration number (nullable) |
| `foreign_reg_dt` | DATE | Date of foreign registration (nullable) |

See `instructions/load-supplemental.md` for when and how to load these tables.

---

## The `serial_no` Type Split

`serial_no` is **BIGINT** in all bulk and on-demand tables (as delivered by the USPTO CSV source) and **VARCHAR** in the TSDR enrichment tables (`extended_marks`, `mark_images`) as returned by the TSDR API. This split is the most common source of silent query errors in cross-layer joins.

### Rule

Any join that crosses the bulk/TSDR boundary requires an explicit cast:

```sql
CAST(cf.serial_no AS VARCHAR)   -- when joining bulk → enrichment
```

### Cross-layer query patterns

**Mark with image and goods description:**
```sql
SELECT
    cf.mark_id_char,
    cf.filing_dt,
    em.goods_desc,
    em.first_use_dt,
    mi.image_size
FROM case_file cf
LEFT JOIN extended_marks em ON CAST(cf.serial_no AS VARCHAR) = em.serial_no
LEFT JOIN mark_images    mi ON CAST(cf.serial_no AS VARCHAR) = mi.serial_no
WHERE cf.serial_no = 71246709;
```

**Owner name joined to TSDR status:**
```sql
SELECT o.own_name, em.status_cd, em.registration_dt
FROM owner o
JOIN extended_marks em ON CAST(o.serial_no AS VARCHAR) = em.serial_no
WHERE o.own_id = 1
  AND UPPER(o.own_name) LIKE '%WILSON JONES%';
```

**Prosecution timeline for a mark:**
```sql
SELECT event_dt, event_cd, event_desc_t
FROM events
WHERE serial_no = 71246709
ORDER BY event_dt;
```
*(No cast needed — `events.serial_no` is also BIGINT, same layer as `case_file`.)*

**Foreign priority claim:**
```sql
SELECT cf.mark_id_char, cf.filing_dt, fa.foreign_country_cd, fa.foreign_filing_dt
FROM case_file cf
JOIN foreign_app fa ON cf.serial_no = fa.serial_no
WHERE cf.serial_no = 71246709;
```
*(No cast needed — both are BIGINT.)*
