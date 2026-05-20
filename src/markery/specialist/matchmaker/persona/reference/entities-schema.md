# Reference: Entity CSV Schema

Entity and variant data is defined in per-project CSV files. These files are the authoritative source; `entities.duckdb` is populated from them by `markery matchmaker build`.

---

## `entities.csv`

One row per canonical company entity.

| Column | Type | Required | Notes |
|---|---|---|---|
| `entity_id` | integer | yes | Unique across all projects. Assign sequentially. Do not reuse IDs. |
| `canonical_name` | string | yes | The single canonical company name. Used as the display name everywhere. Avoid abbreviations — use the full formal name. |
| `entity_type` | string | no | `manufacturer`, `publisher`, `retailer`, or similar. Used for display only. |
| `industry` | string | no | Industry description. Used for display only. |

**Example:**
```csv
entity_id,canonical_name,entity_type,industry
1,Wilson Jones Company,manufacturer,office machinery
2,Remington Rand,manufacturer,office machinery
3,Kardex Systems,manufacturer,filing systems
```

---

## `variants.csv`

One row per name form, per database source. An entity typically has multiple variants.

| Column | Type | Required | Notes |
|---|---|---|---|
| `entity_id` | integer | yes | Must match an `entity_id` in `entities.csv`. |
| `variant_name` | string | yes | Exact string as it appears in the source database. No normalization is applied — must match exactly. |
| `source` | string | yes | `patent_assignee` or `trademark_owner`. Determines which database column is searched. |

**`source` values:**

| Value | Searches |
|---|---|
| `patent_assignee` | `patents.assignee_name` in `patents.duckdb` |
| `trademark_owner` | `owner.own_name` in `trademarks.duckdb` |

**Example:**
```csv
entity_id,variant_name,source
1,Wilson Jones Company,patent_assignee
1,Wilson Jones Co,patent_assignee
1,WILSON JONES COMPANY,trademark_owner
1,WILSON JONES CO,trademark_owner
2,Remington Rand,patent_assignee
2,Remington Rand Inc,patent_assignee
2,REMINGTON RAND,trademark_owner
```

---

## Finding variant strings

Before adding a variant, verify the exact string as it appears in the source database.

**Check patent assignee values:**
```sql
SELECT DISTINCT assignee_name
FROM patents
WHERE assignee_name ILIKE '%wilson jones%'
ORDER BY assignee_name;
```

**Check trademark owner values:**
```sql
SELECT DISTINCT own_name
FROM owner
WHERE own_name ILIKE '%wilson jones%'
ORDER BY own_name;
```

Matching is exact (`=`), not fuzzy. Every distinct string that should match the entity needs its own variant row.

---

## Build and verify

After editing the CSV files:

```bash
# Insert new rows (idempotent — skips existing)
markery matchmaker build --data-dir projects/<project>

# Confirm entities loaded
markery matchmaker list

# Confirm variant counts
markery matchmaker status
```

---

## Shared registry note

`entities.duckdb` is shared across all projects. Entity IDs must be globally unique, not just unique within one project's CSV. When starting a new project, check existing entity IDs with `markery matchmaker list` before assigning new ones.

---

## `entities.txt` — project scope file

Each project also has `projects/<project>/entities.txt` — a plain text file listing which entity IDs are in scope for that project:

```
# information-systems project
1    # Wilson Jones Company
2    # Remington Rand
3    # Kardex Systems
```

Lines starting with `#` and inline `#` comments are ignored. Only entity IDs listed here are included when `markery match <project>` runs. Entities in `entities.duckdb` but not in `entities.txt` are excluded from candidate generation for that project.
