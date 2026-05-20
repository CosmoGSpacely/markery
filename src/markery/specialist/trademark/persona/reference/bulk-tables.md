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

| Table | Created by |
|---|---|
| `events` | `markery trademark load-events --csv-dir csv/` |
| `foreign_app` | `markery trademark load-foreign --csv-dir csv/` |

These tables do not exist in the schema until explicitly loaded.
