# Historical Trademark Design Mark Database

Research database of USPTO trademark applications filed 1900–1939, focused on design marks, stylized marks, and all non-word marks.

## Data Sources

### Primary: USPTO Trademark Case Files Dataset (2011 snapshot)
Downloaded from the USPTO Economic Research page:
`https://www.uspto.gov/ip-policy/economic-research/research-datasets/trademark-case-files-dataset`

This is a cumulative snapshot covering all trademark applications from October 1870 through 2011, distributed as a set of relational CSV files. The files used are in the `/csv` directory.

### Supplemental: USPTO Trademark Daily XML
`apc260504.xml` — a daily update file from May 4, 2026 in the TSDR XML format. Contains 4,888 records with full nested structure including design search codes, owners, classifications, and prosecution events. Retained for reference and format documentation.

## Database

**File:** `trademarks.duckdb`  
**Built by:** `build_db.py`  
**Scope:** Applications with `filing_dt` between `1900-01-01` and `1939-12-31`

### Tables

| Table | Rows | Description |
|---|---|---|
| `case_file` | 25,473 | Core application record — mark name, drawing code, dates, status |
| `owner` | 38,349 | Applicant and owner information |
| `owner_name_change` | 8,600 | Recorded name changes for owners |
| `classification` | 25,497 | Classification records with first-use dates |
| `intl_class` | 28,119 | International (Nice) class codes |
| `us_class` | 26,188 | US class codes |
| `design_search` | 18,790 | Design search codes (visual element classification) |
| `prior_mark` | 11,329 | Prior mark references |
| `statement` | 35,077 | Goods and services descriptions |

### Key Fields

**`case_file.mark_draw_cd`** — drawing code indicating mark type:
- `1xxx` — Typeset word mark (historical)
- `2xxx` — Design/illustration with color
- `3xxx` — Design/illustration, black & white
- `4xxx` — Standard character (word mark, modern)
- `5xxx` — Stylized mark (words + design elements)

Filter to non-word marks: `WHERE mark_draw_cd LIKE '2%' OR mark_draw_cd LIKE '3%' OR mark_draw_cd LIKE '5%'`

**`case_file.cfh_status_cd`** — current status:
- `6xx` — Live (registered)
- `7xx` — Dead (cancelled)
- `8xx` — Dead (abandoned)
- `9xx` — Dead (expired/lapsed)

Live/dead flag: `CASE WHEN CAST(cfh_status_cd AS VARCHAR) LIKE '6%' THEN 'LIVE' ELSE 'DEAD' END`

### Joining Tables

All tables join to `case_file` on `serial_no`. The `classification`, `intl_class`, and `us_class` tables have an intermediate `class_id` key:

```sql
SELECT cf.serial_no, cf.mark_id_char, ic.intl_class_cd, uc.us_class_cd
FROM case_file cf
LEFT JOIN classification c USING (serial_no)
LEFT JOIN intl_class ic USING (class_id)
LEFT JOIN us_class   uc USING (class_id)
```

## Rebuilding the Database

```bash
source .venv/bin/activate
python build_db.py
```

The script removes any existing `trademarks.duckdb` and rebuilds from scratch. To change the date scope, edit `START_DATE` and `END_DATE` in `build_db.py`.

## Image Retrieval

Mark images are not included in the CSV dataset. Planned retrieval via the USPTO TSDR API using the `rawImage` endpoint:

```
GET https://tsdrapi.uspto.gov/ts/cd/rawImage/{serial_number}
```

Requires a USPTO API key. See `TSDR.md` for API client setup.

## Notes

- The 2011 dataset was chosen for smaller file sizes while retaining full historical coverage. Pre-1940 records are effectively unchanged between the 2011 and 2024 snapshots.
- The `statement.csv` file (1.7 GB) was added to the database separately after the initial build via a direct `ALTER`-style append rather than a full rebuild.
- Six marks in the 1900–1939 scope show status 626/624 (live) as of the 2011 snapshot. Physical prosecution files for many early marks are marked `FILE DESTROYED`.
- The daily XML file (`apc260504.xml`) uses a different drawing code format (single digit: 1–6) than the CSV dataset (4-character codes: `3000`, `5U07`, etc.).
