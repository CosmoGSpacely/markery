# Patent Bulk Import — Design

This document records the source evaluation and implementation design for `markery patent bulk-import`. The command does not yet exist; see DEFERRED D007 for the implementation entry.

**Problem:** The EPO OPS API imposes a daily query quota on the free tier (~2,000 results per window, ~8 windows per day). For projects sweeping many CPC classes over multiple decades, hitting the full scope incrementally takes days or weeks. A bulk import route would populate `patents.duckdb` from a pre-packaged offline source in a single download-and-load operation.

---

## Source Evaluation

### PatentsView ✅ Recommended

- **Maintained by:** RAND Corporation under USPTO contract
- **Format:** Tab-separated (.tsv.gz), annual releases
- **Coverage:** US patents from 1836 to present
- **No API key required.** Direct download.
- **CPC coverage:** Full CPC classifications via retroactive mapping (same basis as EPO OPS)
- **Assignee disambiguation:** PatentsView provides disambiguated organization names — a substantial advantage over EPO OPS which returns raw assignee strings

**Files needed:**

| File | Contents | Approx. size (full) |
|---|---|---|
| `g_patent.tsv.gz` | patent_id, number, country, date, abstract, title, kind | ~2.5 GB |
| `g_assignee_disambiguated.tsv.gz` | patent_id, disambig_assignee_organization, location_id | ~400 MB |
| `g_cpc_current.tsv.gz` | patent_id, section, ipc_class, subclass, symbol_position, symbol | ~300 MB |
| `g_inventor_disambiguated.tsv.gz` | patent_id, disambig_inventor_name_last, disambig_inventor_name_first | ~600 MB |
| `g_location_disambiguated.tsv.gz` | location_id, city, state, country | ~10 MB |

For a project scoped to 1900–1939, the relevant rows are a small fraction of each file. DuckDB can filter during load without loading the full file into memory.

**Limitations:**
- Full downloads are multi-gigabyte; a project-scoped subset requires reading and discarding most rows during load
- Assignee disambiguation quality degrades for pre-1940 patents (sparse coverage)
- `kind` field mapping requires care: pre-1940 utility grants use kind `A`, not `B1` (post-1976 convention)

---

### Google Patents Public Data ❌ Not recommended

- Requires a BigQuery project and GCP credentials
- Data must be exported from BigQuery to GCS then downloaded — no direct bulk download
- No offline use
- Adds a cloud billing dependency

---

### USPTO Bulk XML ❌ Not recommended

- Weekly releases available at bulk.uspto.gov
- Requires custom XML parser against a complex DTD
- No single-file download for a filtered date range
- High implementation complexity for marginal benefit over PatentsView

---

## Schema Mapping

`patents.duckdb` schema → PatentsView source columns:

### `patents` table

| Markery column | PatentsView source | Notes |
|---|---|---|
| `patent_no` | `g_patent.number` + `g_patent.kind` | Construct as `US{number}{kind}` — e.g., number=`1630977`, kind=`A` → `US1630977A`. Pre-1940 utility grants: kind is always `A`. |
| `title` | `g_patent.title` | Direct |
| `app_dt` | Not available in PatentsView main file | PatentsView does not expose application date. Leave NULL for bulk-imported rows. |
| `grant_dt` | `g_patent.date` | ISO date string, direct |
| `abstract` | `g_patent.abstract` | Direct; may be NULL for early patents |
| `assignee_name` | `g_assignee_disambiguated.disambig_assignee_organization` | Disambiguated name — may differ from EPO OPS raw string. Variant records in `entities.duckdb` must match whichever source populated a patent's `assignee_name`. |
| `assignee_city` | `g_location_disambiguated.city` | Via `location_id` join on `g_assignee_disambiguated` |
| `assignee_state` | `g_location_disambiguated.state` | Via `location_id` join |

### `patent_classes` table

| Markery column | PatentsView source | Notes |
|---|---|---|
| `patent_no` | Constructed from `g_patent` (same rule as above) | |
| `cpc_class` | First 4 chars of `g_cpc_current.symbol` (e.g., `B42F`) | PatentsView `symbol` is the full CPC code like `B42F1/04`; truncate to subclass |
| `cpc_full` | `g_cpc_current.symbol` | Full code, direct |

### `patent_inventors` table

| Markery column | PatentsView source | Notes |
|---|---|---|
| `patent_no` | Constructed | |
| `inventor_name` | `disambig_inventor_name_first` + `disambig_inventor_name_last` concatenated | |

### `patent_figures` table

Not populated by bulk import. Figures require a separate fetch step (`markery patent figures <patent_no>`).

---

## patent_no Format and Matching Concern

The current EPO OPS route produces patent numbers in EPODOC format: `US1630977A`. PatentsView produces bare numbers: `1630977` with a separate `kind` field (`A`, `A1`, `B1`, `B2`, etc.).

The construction rule `US{number}{kind}` produces the same format for pre-1940 utility patents (kind=`A`). For post-1976 patents, kind may be `B1` or `B2`, giving `US1234567B1` — which is also the EPODOC format returned by EPO OPS for modern grants.

**Mixed-source projects:** If a project's `patents.duckdb` contains rows from both EPO OPS and bulk import, patent numbers must be constructed consistently. The bulk importer must apply the same `US{number}{kind}` rule and validate against existing rows (insert-if-not-exists, same as EPO OPS).

**Assignee name mismatch:** EPO OPS returns raw assignee strings from the filing record; PatentsView returns disambiguated names. A company might appear as "WILSON JONES CO" in EPO OPS and "Wilson Jones Company" in PatentsView. Entity name variants in `entities.duckdb` must cover both forms if patents from both sources exist in the same project.

---

## Planned Command Signature

```bash
markery patent bulk-import \
    --tsv-dir <path>          # Directory containing PatentsView .tsv.gz files
    --year-start <YEAR>       # Filter: load patents granted on/after this year
    --year-end   <YEAR>       # Filter: load patents granted on/before this year
    --classes    <CPC> [...]  # Filter: load only patents with these CPC subclasses
    [--dry-run]               # Report row counts without writing to patents.duckdb
    [--force]                 # Re-insert patents already in patents.duckdb (default: skip)
```

**Filtering behavior:** Apply both `--year-start`/`--year-end` and `--classes` during the DuckDB load step, not after. DuckDB's TSV reader supports predicate pushdown via SQL; filtering at read time avoids loading gigabytes of out-of-scope rows.

**Idempotent by default:** Skip patents already present in `patents.duckdb` (matching on `patent_no`). Append-only unless `--force` is set.

**No fetch-log entry:** The bulk route bypasses the EPO OPS fetch log. Patent rows loaded via bulk import are indistinguishable from EPO OPS rows at the data level — they share the same tables and `patent_no` format.

**Post-import step:** After bulk import, run `markery patent signals <project>` and `markery match <project> --force` to regenerate candidates with the new patent data.

---

## Implementation Notes

- DuckDB can read `.tsv.gz` files natively via `read_csv()` with `delim='\t'` and `compression='gzip'`
- A date filter on a multi-GB file requires scanning the full file but is fast in DuckDB (columnar read)
- CPC filtering requires a join between `g_patent` and `g_cpc_current` at load time
- The `g_assignee_disambiguated` file has one row per (patent, assignee) — multi-assignee patents have multiple rows; take the first or concatenate
- Figures are not included in any PatentsView file — always a separate fetch step

---

## Download Source

PatentsView bulk data download: `https://patentsview.org/download/data-download-tables`

Files are updated annually (typically Q1 release for the prior year). For pre-1940 projects, the annual release does not change the historical data — any release year is equivalent.
