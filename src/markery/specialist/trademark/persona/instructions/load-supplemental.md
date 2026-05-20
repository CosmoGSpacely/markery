# Instruction Card: Load Supplemental Tables

The USPTO Trademark Case Files Dataset includes two tables that are not loaded during the standard bulk build: `events` (prosecution history) and `foreign_app` (Madrid Protocol foreign applications). These are on-demand — they do not exist in `trademarks.duckdb` until explicitly loaded.

---

## `events` — Prosecution history

### When to use

When the timeline of prosecution matters for the correspondence argument. The events table records every step in a mark's prosecution: filing, office actions, applicant responses, publication for opposition, registration, cancellation, and post-registration maintenance actions.

Useful when:
- A mark's filing date and registration date are far apart and you need to understand why (office actions, abandonment and revival, opposition proceedings)
- A mark's status code is "abandoned" and you want to know at what stage
- You are tracing the full lifecycle of a confirmed mark for the essay's evidence section

### Command

```bash
markery trademark load-events --csv-dir csv/
```

Requires `event.csv` in the CSV directory. Drops and recreates the `events` table from the CSV each run (not incremental — safe to re-run). Filtered to serial numbers present in `case_file`.

### Schema

| Column | Notes |
|---|---|
| `serial_no` | BIGINT — foreign key to `case_file.serial_no` |
| `event_dt` | Date the event occurred |
| `event_cd` | Event code (e.g., `NDOA` = new application, `PUBT` = published for opposition, `REGS` = registered) |
| `event_desc_t` | Full text description of the event |
| `party_cd` | Party responsible (e.g., `AP` = applicant, `OA` = office action from examiner) |

### Query pattern

```sql
SELECT event_dt, event_cd, event_desc_t
FROM events
WHERE serial_no = 71246709
ORDER BY event_dt;
```

---

## `foreign_app` — Madrid Protocol foreign applications

### When to use

When a mark's prosecution includes a claim to foreign priority — a prior filing in another country that the US application claims as its priority date. This is relevant when:

- A mark's effective priority date predates its US filing date (foreign priority claim)
- You need to determine whether a company was registering the same brand internationally
- A confirmed pair's trademark has a foreign counterpart that predates the patent

### Command

```bash
markery trademark load-foreign --csv-dir csv/
```

Requires `foreign_application.csv` in the CSV directory. Drops and recreates the `foreign_app` table from the CSV each run. Filtered to serial numbers present in `case_file`.

### Schema

| Column | Notes |
|---|---|
| `serial_no` | BIGINT — foreign key to `case_file.serial_no` |
| `foreign_appl_no` | Foreign application number |
| `foreign_country_cd` | ISO country code of the foreign filing (e.g., `GB`, `DE`, `FR`) |
| `foreign_filing_dt` | Date of the foreign application |
| `foreign_reg_no` | Foreign registration number (nullable — not all foreign applications result in registration) |
| `foreign_reg_dt` | Date of foreign registration (nullable) |

### Query pattern

```sql
SELECT foreign_country_cd, foreign_filing_dt, foreign_reg_no
FROM foreign_app
WHERE serial_no = 71246709
ORDER BY foreign_filing_dt;
```

---

## Notes on both tables

- **Not part of the standard build.** Neither table exists in `trademarks.duckdb` until explicitly loaded. A query against `events` or `foreign_app` before loading will error.
- **Recreated on each load.** Both loaders DROP and recreate the table — there is no incremental update. Re-loading after new CSV data is safe.
- **Filtered to `case_file`.** Only rows with a `serial_no` present in `case_file` are loaded. Serial numbers outside the project's date window are excluded automatically.
- **Volume.** For a 1900–1939 window, `events` typically has 5–10 rows per mark (filing, any office actions, publication, registration). `foreign_app` has sparse coverage for pre-1940 marks — foreign priority claims were less common before the Madrid Protocol became widely used.
