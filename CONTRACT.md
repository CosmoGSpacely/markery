# Markery Data Contract

Version: 1.0  
Authoritative interface between **Markery-ICM** (this repo) and **Markery-LangGraph** (consumer).

Any breaking change to a field listed here requires incrementing `contract_version` in `MANIFEST.json` and updating this document. Non-breaking additions (new optional fields, new tables) require an update here but not a version bump.

---

## Schema stability conventions

- **guaranteed-present**: field is always written; a consuming node may rely on it without a null check.
- **optional**: field may be absent or null; consumer must handle the missing case.
- **nullable**: field is present in the record but its value may be null.

---

## 1. patents.duckdb

File: `data/patents.duckdb`  
DDL authority: `src/markery/specialist/patent/build.py`

### Table: patents

Primary table. One row per patent. The `patent_no` key appears as-is in all downstream JSONL and frontmatter.

| Column | Type | Nullable | Contract status | Notes |
|---|---|---|---|---|
| `patent_no` | VARCHAR | NOT NULL | guaranteed-present | USPTO/EPO OPS number, e.g. `US1261167A`. Primary key. |
| `title` | VARCHAR | nullable | guaranteed-present | Patent title as returned by EPO OPS. |
| `app_dt` | DATE | nullable | optional | Application date. May be absent for pre-1920 patents. |
| `grant_dt` | DATE | nullable | guaranteed-present | Grant date. Used as the primary scoring date. |
| `abstract` | VARCHAR | nullable | optional | Abstract text. Populated by `markery patent signals`. |
| `assignee_name` | VARCHAR | nullable | optional | Assignee name at grant time, uppercase. May not match `entity.canonical_name` directly. |
| `assignee_city` | VARCHAR | nullable | optional | |
| `assignee_state` | VARCHAR | nullable | optional | |

### Table: patent_classes

One row per CPC class assignment per patent.

| Column | Type | Nullable | Contract status | Notes |
|---|---|---|---|---|
| `patent_no` | VARCHAR | NOT NULL | guaranteed-present | FK to patents. |
| `cpc_class` | VARCHAR | nullable | optional | 4-character CPC class prefix, e.g. `B42F`. |
| `cpc_full` | VARCHAR | nullable | optional | Full CPC symbol. |

### Table: patent_inventors

One row per inventor per patent.

| Column | Type | Nullable | Contract status | Notes |
|---|---|---|---|---|
| `patent_no` | VARCHAR | NOT NULL | guaranteed-present | FK to patents. |
| `inventor_name` | VARCHAR | nullable | optional | |

### Table: patent_figures

One row per drawing figure per patent.

| Column | Type | Nullable | Contract status | Notes |
|---|---|---|---|---|
| `patent_no` | VARCHAR | NOT NULL | guaranteed-present | FK to patents. |
| `figure_no` | INTEGER | NOT NULL | guaranteed-present | 1-based figure number. |
| `figure_data` | BLOB | nullable | optional | PNG image bytes. NULL until `markery patent figures` is run. |
| `figure_format` | VARCHAR | nullable | optional | Default `'PNG'`. |
| `fetched_dt` | DATE | nullable | optional | |

---

## 2. trademarks.duckdb

File: `data/trademarks.duckdb`  
DDL authority: `src/markery/specialist/trademark/build.py`

This database contains two distinct layers with **different `serial_no` types**:

- **Bulk tables** (CSV-sourced from USPTO 2011 dataset): `serial_no` is `BIGINT`.
- **Enrichment tables** (TSDR API): `serial_no` is `VARCHAR`.

Cross-table joins must cast: `CAST(bulk_table.serial_no AS VARCHAR)`.

### Table: case_file (bulk)

Core trademark registry. One row per mark filing. Schema is as-delivered by the USPTO CSV source (`read_csv_auto`); not under Markery control.

| Column | Type | Contract status | Notes |
|---|---|---|---|
| `serial_no` | BIGINT | guaranteed-present | Primary key. Cross-reference to enrichment tables requires VARCHAR cast. |
| `filing_dt` | DATE | optional | Filing date. Used in scoring. |
| `registration_dt` | DATE | optional | Registration date. |
| `registration_no` | VARCHAR | optional | USPTO registration number. |
| `cfh_status_cd` | BIGINT | optional | Case status code: 700 = registered, 800 = expired, 900 = cancelled/dead. Compare as integer or cast. |
| `mark_draw_cd` | VARCHAR | optional | `'1'` = typed word mark; `'2'` = design only (figurative); `'3'`/`'4'` = design+word. |

All other case_file columns are from the USPTO source and are outside the LangGraph contract scope.

### Table: owner (bulk)

One row per owner record per serial number. A serial may have multiple owner rows (original + subsequent).

| Column | Contract status | Notes |
|---|---|---|
| `serial_no` BIGINT | guaranteed-present | FK to case_file. |
| `own_name` | optional | Owner name string. |
| `own_seq` | optional | Sequence number; higher values are later. |

### Table: classification (bulk)

One row per goods/services class per serial number.

| Column | Contract status | Notes |
|---|---|---|
| `serial_no` BIGINT | guaranteed-present | |
| `first_use_any_dt` DATE | optional | First use in commerce anywhere. |
| `first_use_com_dt` DATE | optional | First use in US commerce. |
| `class_primary_cd` VARCHAR | optional | Primary US class code. |

### Table: intl_class (bulk)

| Column | Contract status | Notes |
|---|---|---|
| `serial_no` BIGINT | guaranteed-present | |
| `intl_class_cd` VARCHAR | optional | International (Nice) class code, e.g. `'016'`. |

### Table: design_search (bulk)

| Column | Contract status | Notes |
|---|---|---|
| `serial_no` BIGINT | guaranteed-present | |
| `design_search_cd` VARCHAR | optional | USPTO design search code, e.g. `'03.01.07'` (bulldog). |

### Table: statement (bulk)

Goods and services descriptions. One row per statement per serial.

| Column | Contract status | Notes |
|---|---|---|
| `serial_no` BIGINT | guaranteed-present | |
| `statement_type_cd` VARCHAR | optional | Code indicating statement type; `'GS'` is goods/services. |
| `statement_text` VARCHAR | optional | Free text goods/services description. |

### Table: extended_marks (enrichment)

TSDR API-sourced structured fields. Populated by `markery trademark enrich` followed by `markery trademark reparse`.

| Column | Type | Nullable | Contract status | Notes |
|---|---|---|---|---|
| `serial_no` | VARCHAR | NOT NULL | guaranteed-present | Primary key. Cast from BIGINT bulk serial numbers when joining. |
| `mark_text` | VARCHAR | nullable | optional | Verbal element of the mark. NULL for purely figurative (design-only) marks. |
| `filing_dt` | DATE | nullable | optional | |
| `registration_no` | VARCHAR | nullable | optional | |
| `registration_dt` | DATE | nullable | optional | |
| `status_cd` | VARCHAR | nullable | optional | String version of status code, e.g. `'700'`, `'900'`. |
| `goods_desc` | VARCHAR | nullable | optional | First goods/services description, truncated at 500 chars. |
| `intl_class` | VARCHAR | nullable | optional | International class code from TSDR. |
| `owner_name` | VARCHAR | nullable | optional | Most recent owner from TSDR. NULL for rows populated via bulk enrichment. |
| `first_use_dt` | VARCHAR | nullable | optional | First use anywhere date string. |
| `first_use_comm_dt` | VARCHAR | nullable | optional | First use in commerce date string. |
| `raw_json` | VARCHAR | nullable | optional | Full TSDR JSON response. Present for all enriched rows. |
| `fetched_dt` | DATE | nullable | optional | Date fetched from TSDR. |

### Table: mark_images (enrichment)

| Column | Type | Nullable | Contract status | Notes |
|---|---|---|---|---|
| `serial_no` | VARCHAR | NOT NULL | guaranteed-present | PK. |
| `image_data` | BLOB | nullable | optional | Raw PNG bytes. NULL until `markery trademark images` is run. |
| `image_format` | VARCHAR | nullable | optional | Default `'PNG'`. |
| `image_size` | INTEGER | nullable | optional | Byte count. |
| `fetched_dt` | DATE | nullable | optional | |

---

## 3. entities.duckdb

File: `data/entities.duckdb`  
DDL authority: `src/markery/specialist/matchmaker/entities.py`

### Table: company_entity

| Column | Type | Nullable | Contract status | Notes |
|---|---|---|---|---|
| `entity_id` | INTEGER | NOT NULL | guaranteed-present | Primary key. Stable within a project session. |
| `canonical_name` | VARCHAR | NOT NULL | guaranteed-present | Human-readable entity name, e.g. `'Remington Rand'`. |
| `entity_type` | VARCHAR | nullable | optional | |
| `industry` | VARCHAR | nullable | optional | |

### Table: entity_name_variant

| Column | Type | Nullable | Contract status | Notes |
|---|---|---|---|---|
| `variant_id` | INTEGER | NOT NULL | guaranteed-present | PK. |
| `entity_id` | INTEGER | NOT NULL | guaranteed-present | FK to company_entity. |
| `variant_name` | VARCHAR | NOT NULL | guaranteed-present | Name string used in patent assignee or trademark owner searches. Uppercase. |
| `source` | VARCHAR | NOT NULL | guaranteed-present | One of: `patent_assignee`, `trademark_owner`, `trademark_search`. |

---

## 4. candidates.jsonl

File: `projects/<name>/matches/candidates.jsonl`  
One JSON object per line. Generated by `markery match <project>`.

| Field | Type | Nullable | Contract status | Notes |
|---|---|---|---|---|
| `entity_id` | int | no | guaranteed-present | FK to entities.duckdb company_entity. |
| `entity` | str | no | guaranteed-present | Canonical entity name. |
| `patent_no` | str | no | guaranteed-present | e.g. `"US2152606A"`. |
| `patent_title` | str | yes | optional | May be null if abstract not yet fetched. |
| `patent_grant_dt` | str | yes | optional | ISO8601 date string, e.g. `"1939-03-28"`. |
| `patent_assignee` | str | yes | optional | Assignee name from patents table. |
| `cpc_classes` | str[] | no | guaranteed-present | List of 4-character CPC prefix strings. May be empty list `[]`. |
| `trademark_serial` | int | no | guaranteed-present | Integer serial number. Cast to VARCHAR when joining to trademarks.duckdb enrichment tables. |
| `trademark` | str | yes | nullable | Verbal mark text. **null for purely figurative (design-only) marks.** |
| `tm_filing_dt` | str | yes | optional | ISO8601 date string. |
| `tm_reg_no` | str | yes | optional | USPTO registration number. |
| `tm_owner` | str | yes | optional | |
| `score` | float | no | guaranteed-present | See §8 Score semantics. |
| `title_name_hit` | bool | no | guaranteed-present | Mark name found in patent title. |
| `abstract_name_hit` | bool | no | guaranteed-present | Mark name found in patent abstract. |
| `goods_title_overlap` | float | no | guaranteed-present | Jaccard overlap of goods tokens with title tokens. |
| `goods_abstract_overlap` | float | no | guaranteed-present | Jaccard overlap of goods tokens with abstract tokens. |

---

## 5. confirmed.jsonl

File: `projects/<name>/matches/confirmed.jsonl`  
One JSON object per line. Written manually or via `markery match confirm` (D029 — not yet implemented).

| Field | Type | Nullable | Contract status | Notes |
|---|---|---|---|---|
| `patent_no` | str | no | guaranteed-present | |
| `trademark_serial` | int | no | guaranteed-present | Integer serial number. |
| `trademark` | str | yes | nullable | null for figurative marks. |
| `entity_id` | int | no | guaranteed-present | |
| `entity` | str | no | guaranteed-present | |
| `type` | str | no | guaranteed-present | Relationship type. Value: `"product"` (only value used to date; enum open for extension). |
| `note` | str | no | guaranteed-present | Researcher annotation. May be empty string `""`. |

---

## 6. rejected.jsonl

File: `projects/<name>/matches/rejected.jsonl`  
One JSON object per line. Written by `markery match auto-disposition`.

| Field | Type | Nullable | Contract status | Notes |
|---|---|---|---|---|
| `patent_no` | str | no | guaranteed-present | |
| `trademark_serial` | int | no | guaranteed-present | |
| `trademark` | str | yes | nullable | null for figurative marks. |
| `entity_id` | int | no | guaranteed-present | |
| `entity` | str | no | guaranteed-present | |
| `rejection_note` | str | no | guaranteed-present | Human annotation. Empty string `""` for auto-rejections. |
| `auto_rejected` | bool | no | guaranteed-present | `true` for machine-generated rejections, `false` for manual. |
| `rejection_reasons` | str[] | no | guaranteed-present | List of reason strings, e.g. `["score 0.320 < threshold 0.40"]`. Empty list for manual rejections. |

---

## 7. Essay frontmatter

File: `projects/<name>/content/<slug>.md`  
Frontmatter is YAML between `---` delimiters at the start of the file.

**Slug convention:** `{trademark_slug}-{patent_no_lower}` where `trademark_slug` is `re.sub(r'[^a-z0-9]+', '-', (trademark or 'figurative').lower()).strip('-')`. Example: `double-eagle-us1645089a`.

### Required keys (enforced by `historian validate`)

| Key | Type | Notes |
|---|---|---|
| `trademark_serial` | int | Must resolve in trademarks.duckdb case_file. |
| `patent_no` | str | Must resolve in patents.duckdb. |
| `patent_grant_dt` | str | Must match patents.grant_dt (YYYY-MM-DD). |
| `tm_filing_dt` | str | Must appear in essay body (year-month minimum). |
| `entity` | str | Must match company_entity.canonical_name or entity_name_variant.variant_name. |

### Additional keys (written by scaffold; not yet enforced by validate — P2 gap)

| Key | Type | Notes |
|---|---|---|
| `title` | str | Human-readable title: `"{trademark} — {patent_no}"`. |
| `trademark` | str | Verbal mark text. May be `"(figurative)"` for design marks. |
| `tm_reg_no` | str | USPTO registration number. |
| `tm_owner` | str | Owner name at registration. |
| `patent_assignee` | str | Assignee name from patents table. |
| `date_gap` | str | Human-readable gap string, e.g. `"9.0 years"`. |

**Known gap (P2):** `historian validate` does not enforce `title` or `trademark`. A valid essay could pass validate with both absent.

---

## 8. library/index.jsonl

File: `library/index.jsonl`  
Global passage index. One JSON object per line. Written by `markery librarian index`.

| Field | Type | Nullable | Contract status | Notes |
|---|---|---|---|---|
| `work_slug` | str | no | guaranteed-present | Identifies the source work, e.g. `"archer-big-business-and-radio"`. |
| `author` | str | yes | optional | Author string from library catalog. |
| `title` | str | yes | optional | Work title. |
| `year` | int | yes | nullable | Publication year. **May be null** when not recorded in the catalog. |
| `section` | str | no | guaranteed-present | Section or passage heading from `excerpts.md`. Must be `###`-headed. |
| `passage` | str | no | guaranteed-present | Extracted passage text. |
| `page` | str | yes | optional | Page reference string, e.g. `"pp. 4–5"`. May be empty string. |
| `context` | str | no | guaranteed-present | Additional context string. May be empty string `""`. |
| `indexed_at` | str | no | guaranteed-present | ISO8601 timestamp with timezone, e.g. `"2026-06-04T17:45:13.991959+00:00"`. |

---

## 9. library/index.duckdb — passage_embeddings

File: `library/index.duckdb`  
DDL authority: `src/markery/specialist/librarian/index.py`

Populated by `markery librarian index --embed`. Requires `sentence-transformers`.

### Table: passage_embeddings

| Column | Type | Contract status | Notes |
|---|---|---|---|
| `work_slug` | TEXT | guaranteed-present | Joins to index.jsonl on `work_slug`. |
| `passage_id` | INTEGER | guaranteed-present | 0-based index position in index.jsonl. Stable until `--rebuild`. |
| `section` | TEXT | guaranteed-present | Section heading. May be empty string. |
| `passage` | TEXT | guaranteed-present | Passage text. |
| `embedding` | FLOAT[] | guaranteed-present | Sentence embedding vector. Model: `all-MiniLM-L6-v2` (384 dimensions). |

---

## 10. Score semantics

The `score` field in `candidates.jsonl` is a float computed by `total_score()` in `src/markery/specialist/matchmaker/score.py`.

```
score = date_score(grant_dt, filing_dt)
      + class_score(cpc_classes, class_hints)
      + min(0.25, semantic_score(...))
```

### Component ranges

| Component | Range | Conditions |
|---|---|---|
| `date_score` | [-0.4, 0.5] | 0.5 for same-year; decays over 20 years; negative when trademark predates patent grant. |
| `class_score` | 0.0 or 0.3 | 0.3 if any CPC class prefix is in the project's `class_hints` set (from `project.json`); falls back to hardcoded `PRODUCT_CLASSES = {"B42F","B42D","B41J","B41L","G06C","G06K","G09F"}` if `class_hints` absent. |
| `semantic_score` | [0.0, 0.25] | Capped at `SEMANTIC_CAP=0.25`; signals: title_name_hit (+0.20), abstract_name_hit (+0.10), goods_title_overlap (+0.10), goods_abstract_overlap (+0.05). |

**Theoretical maximum:** 0.5 + 0.3 + 0.25 = 1.05. Strong confirmed pairs in practice score 0.70–0.85.

**Interpretation guidance for consumers:** Score ordering is meaningful within a single project and domain, but not across projects with different `class_hints`. A score above 0.70 with `title_name_hit=true` is a strong signal; a score above 0.70 driven entirely by `class_score + date_score` requires researcher review.

---

## 11. Documented gaps (P1 findings)

These gaps exist at the time of this audit (2026-06-06). Each is tracked in DEFERRED.md.

| Gap | Impact | DEFERRED entry |
|---|---|---|
| `case_file` column set not explicitly declared in DDL (CSV-inferred) | Columns outside those listed in §2 are not guaranteed stable across USPTO dataset rebuilds | — (informational; bulk schema is external) |
| `serial_no` BIGINT/VARCHAR split undocumented in user-facing docs | Cross-table joins silently fail if type is not cast | — (documented here) |
| `historian validate` does not enforce `title` or `trademark` frontmatter keys | Essays missing these keys pass validate | P2 |
| `tm_filing_dt` check in validate matches only year-month in body, not full date | Weak enforcement — any occurrence of `YYYY-MM` passes | P2 |
| `confirmed.jsonl` `type` field values not enumerated | Only `"product"` observed; other values undocumented | — |
| `library/wants.jsonl` shape undocumented | Not a LangGraph contract surface; informational only | — |
