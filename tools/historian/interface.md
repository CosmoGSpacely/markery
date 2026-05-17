# Tool Interface

Defines the data contract between the historian and the retrieval backend. The historian calls these tools to gather evidence; any backend that implements this schema works. The current implementation is Markery (DuckDB).

---

## Abstract Interface

### `trademarks.for_entity(entity_name, date_range=None)`

Returns all trademark records for an entity.

| Field | Type | Description |
|---|---|---|
| `serial_no` | string | USPTO serial number (8 digits) |
| `mark_name` | string | Mark text (`mark_id_char`); null for pure design marks |
| `filing_dt` | date | Application filing date |
| `first_use_dt` | date | First use in commerce (`first_use_com_dt`) |
| `draw_cd` | string | Drawing code (4-char in this dataset) |
| `goods` | string | Goods/services description (`statement_text`) |
| `status_cd` | integer | Current status code |
| `image_available` | bool | Whether a PNG is in `mark_images` |
| `owner_name` | string | Applicant name at filing |
| `registration_no` | string | Registration number if granted |

### `trademarks.for_project(project)`

Returns all trademark records for all entities in a project, annotated with `entity_id` and `entity_name`.

### `patents.for_entity(entity_name, date_range=None, cpc_classes=None)`

Returns all patent records for an entity.

| Field | Type | Description |
|---|---|---|
| `patent_no` | string | USPTO publication number (e.g., `US1261167A`) |
| `title` | string | Patent title |
| `grant_dt` | date | Grant date |
| `application_dt` | date | Application date |
| `assignee_name` | string | Assignee at grant |
| `cpc_classes` | list[string] | CPC classification codes |
| `inventors` | list[string] | Named inventors |
| `figure_available` | bool | Whether a figure PNG is in `patent_figures` |

### `entities.get(entity_id)`

Returns one entity record.

| Field | Type | Description |
|---|---|---|
| `entity_id` | integer | Internal ID |
| `canonical_name` | string | Preferred name |
| `entity_type` | string | `manufacturer`, `publisher`, `individual`, etc. |
| `industry` | string | e.g., `office-systems`, `blank-books` |
| `notes` | string | Free text notes |
| `name_variants` | list[{name, source}] | All known spellings by source |

### `entities.for_project(project)`

Returns all entity records for a project (reads `projects/<project>/entities.txt`).

### `matches.for_project(project)`

Returns all confirmed patent-trademark pairs for a project.

| Field | Type | Description |
|---|---|---|
| `patent_no` | string | Patent number |
| `trademark_serial` | string | Trademark serial number |
| `trademark` | string | Mark text |
| `entity_id` | integer | Entity ID |
| `entity` | string | Canonical entity name |
| `type` | string | `product` or `brand` |
| `note` | string | Curation note |
| `essay_path` | string \| null | Path to essay Markdown file if it exists |

---

## Markery Implementation

In Markery, these tools are implemented as DuckDB queries against three databases: `data/trademarks.duckdb`, `data/patents.duckdb`, `data/entities.duckdb`. Connect with:

```python
conn = duckdb.connect("data/entities.duckdb", read_only=True)
conn.execute("ATTACH 'data/patents.duckdb'    AS pat (READ_ONLY)")
conn.execute("ATTACH 'data/trademarks.duckdb' AS tm  (READ_ONLY)")
```

### `trademarks.for_entity` → DuckDB

```sql
SELECT cf.serial_no::VARCHAR,
       cf.mark_id_char,
       cf.filing_dt,
       c.first_use_com_dt,
       cf.mark_draw_cd,
       s.statement_text,
       cf.cfh_status_cd,
       cf.registration_no,
       o.own_name,
       mi.serial_no IS NOT NULL AS image_available
FROM tm.case_file cf
LEFT JOIN tm.owner o         ON cf.serial_no = o.serial_no AND o.own_id = 1
LEFT JOIN tm.statement s     ON cf.serial_no = s.serial_no AND s.statement_type_cd LIKE 'GS%'
LEFT JOIN tm.classification c ON cf.serial_no = c.serial_no
LEFT JOIN tm.mark_images mi  ON cf.serial_no = mi.serial_no
JOIN entity_name_variant v   ON UPPER(o.own_name) = UPPER(v.variant_name)
                             AND v.source = 'trademark_owner'
JOIN company_entity e        ON v.entity_id = e.entity_id
WHERE e.canonical_name = ?
ORDER BY cf.filing_dt;
```

### `patents.for_entity` → DuckDB

```sql
SELECT p.patent_no,
       p.title,
       p.grant_dt,
       p.application_dt,
       p.assignee_name,
       LIST(pc.cpc_class) AS cpc_classes,
       LIST(pi.inventor_name) AS inventors,
       pf.patent_no IS NOT NULL AS figure_available
FROM pat.patents p
LEFT JOIN pat.patent_classes pc ON p.patent_no = pc.patent_no
LEFT JOIN pat.patent_inventors pi ON p.patent_no = pi.patent_no
LEFT JOIN pat.patent_figures pf  ON p.patent_no = pf.patent_no
JOIN entity_name_variant v ON UPPER(p.assignee_name) = UPPER(v.variant_name)
                           AND v.source = 'patent_assignee'
JOIN company_entity e      ON v.entity_id = e.entity_id
WHERE e.canonical_name = ?
GROUP BY p.patent_no, p.title, p.grant_dt, p.application_dt, p.assignee_name,
         pf.patent_no
ORDER BY p.grant_dt;
```

### `matches.for_project` → confirmed.jsonl

```python
import json
from pathlib import Path

def matches_for_project(project: str) -> list[dict]:
    path = Path(f"projects/{project}/matches/confirmed.jsonl")
    matches = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
    for m in matches:
        essay = Path(f"projects/{project}/content/{m['trademark'].lower()}.md")
        m["essay_path"] = str(essay) if essay.exists() else None
    return matches
```

---

## Portability Note

This interface is intentionally backend-agnostic. If Markery is replaced by an API service, a CSV dataset, or a different database engine, the historian works unchanged as long as the new backend returns records conforming to the field schemas above.

When briefing the historian for a non-Markery backend, replace the Markery Implementation section with queries/calls appropriate to that system. The abstract interface and content schemas remain unchanged.
