# Markery Data Contract

Version: 1.0  
Authoritative interface between **Markery-ICM** (this repo) and **Markery-LangGraph** (consumer).  
See `MANIFEST.json` for the machine-readable `contract_version` field.

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

One row per patent. `patent_no` is the join key in all downstream JSONL and frontmatter.

| Column | Type | Contract status | Example | Purpose for consumer |
|---|---|---|---|---|
| `patent_no` | VARCHAR NOT NULL | guaranteed-present | `"US1261167A"` | Primary key; joins to candidates/confirmed/essay frontmatter. |
| `title` | VARCHAR nullable | guaranteed-present | `"Phonetic indexing system"` | Display label in digest and site pages. |
| `app_dt` | DATE nullable | optional | `1917-10-25` | Application date; may be absent for pre-1920 records. |
| `grant_dt` | DATE nullable | guaranteed-present | `1918-04-02` | Primary scoring date; `date_score` is computed from this. |
| `abstract` | VARCHAR nullable | optional | `"Encodes surnames by consonant sound..."` | Context text for historian card and semantic overlap scoring. Populated by `markery patent signals`. |
| `assignee_name` | VARCHAR nullable | optional | `"REMINGTON TYPEWRITER COMPANY"` | Uppercase; used for entity matching. May differ from `entity.canonical_name`. |
| `assignee_city` | VARCHAR nullable | optional | `"New York"` | Not used in scoring; available for display. |
| `assignee_state` | VARCHAR nullable | optional | `"NY"` | Not used in scoring; available for display. |

### Table: patent_classes

One row per CPC class per patent. A patent typically has 1–5 classes.

| Column | Type | Contract status | Example | Purpose for consumer |
|---|---|---|---|---|
| `patent_no` | VARCHAR NOT NULL | guaranteed-present | `"US1261167A"` | FK to patents. |
| `cpc_class` | VARCHAR nullable | optional | `"G06K"` | 4-character prefix; used in `class_score` and project `class_hints` matching. |
| `cpc_full` | VARCHAR nullable | optional | `"G06K 9/00"` | Full symbol; available for display only. |

### Table: patent_inventors

One row per inventor per patent.

| Column | Type | Contract status | Example | Purpose for consumer |
|---|---|---|---|---|
| `patent_no` | VARCHAR NOT NULL | guaranteed-present | `"US1261167A"` | FK to patents. |
| `inventor_name` | VARCHAR nullable | optional | `"Robert C. Russell"` | Display use only; not used in matching or scoring. |

### Table: patent_figures

One row per drawing figure per patent. BLOBs are NULL until `markery patent figures` is run.

| Column | Type | Contract status | Example | Purpose for consumer |
|---|---|---|---|---|
| `patent_no` | VARCHAR NOT NULL | guaranteed-present | `"US1261167A"` | FK to patents. |
| `figure_no` | INTEGER NOT NULL | guaranteed-present | `1` | 1-based figure index. |
| `figure_data` | BLOB nullable | optional | _(PNG bytes)_ | Raw image for site rendering. NULL if not yet fetched. |
| `figure_format` | VARCHAR nullable | optional | `"PNG"` | Always `"PNG"` currently. |
| `fetched_dt` | DATE nullable | optional | `2026-05-30` | Staleness check. |

---

## 2. trademarks.duckdb

File: `data/trademarks.duckdb`  
DDL authority: `src/markery/specialist/trademark/build.py`

**Critical:** this database has two layers with **different `serial_no` types**.  
Bulk tables (CSV-sourced): `serial_no` is `BIGINT`.  
Enrichment tables (TSDR): `serial_no` is `VARCHAR`.  
Cross-layer joins require `CAST(bulk_table.serial_no AS VARCHAR)`.

### Table: case_file (bulk)

Core trademark registry. One row per filing. Schema is delivered by the USPTO 2011 bulk CSV dataset; columns outside the table below are not under Markery control and are outside the LangGraph contract scope.

| Column | Type | Contract status | Example | Purpose for consumer |
|---|---|---|---|---|
| `serial_no` | BIGINT | guaranteed-present | `71246709` | Primary key. Cast to VARCHAR when joining to enrichment tables. |
| `filing_dt` | DATE optional | optional | `1927-03-31` | Filing date used in `date_score` computation. |
| `registration_dt` | DATE optional | optional | `1927-08-09` | Registration date; display use. |
| `registration_no` | VARCHAR optional | optional | `"0230958"` | USPTO registration number; display use. |
| `cfh_status_cd` | BIGINT optional | optional | `900` | Live/dead status: 700 = registered, 800 = expired, 900 = cancelled/dead. Compare as integer. |
| `mark_draw_cd` | VARCHAR optional | optional | `"1"` | `'1'` typed word; `'2'` design only (figurative, no text); `'3'`/`'4'` design+word. |

### Table: owner (bulk)

One row per owner record per serial. A serial may have multiple rows (original owner, subsequent assignees). Higher `own_seq` is more recent.

| Column | Type | Contract status | Example | Purpose for consumer |
|---|---|---|---|---|
| `serial_no` | BIGINT | guaranteed-present | `71246709` | FK to case_file. |
| `own_name` | VARCHAR optional | optional | `"RAND KARDEX BUREAU, INC."` | Owner name; use `own_seq` to select most recent. |
| `own_seq` | BIGINT optional | optional | `2` | Sequence; higher = later owner. |

### Table: classification (bulk)

One row per goods/services class per serial.

| Column | Type | Contract status | Example | Purpose for consumer |
|---|---|---|---|---|
| `serial_no` | BIGINT | guaranteed-present | `71246709` | FK to case_file. |
| `first_use_any_dt` | DATE optional | optional | `1926-01-01` | First use anywhere; dating the commercial product launch. |
| `first_use_com_dt` | DATE optional | optional | `1926-06-01` | First use in US commerce. |
| `class_primary_cd` | VARCHAR optional | optional | `"16"` | Primary US class code. |

### Table: intl_class (bulk)

| Column | Type | Contract status | Example | Purpose for consumer |
|---|---|---|---|---|
| `serial_no` | BIGINT | guaranteed-present | `71246709` | FK to case_file. |
| `intl_class_cd` | VARCHAR optional | optional | `"016"` | International (Nice) class; matches EPO CPC-to-class mappings. |

### Table: design_search (bulk)

| Column | Type | Contract status | Example | Purpose for consumer |
|---|---|---|---|---|
| `serial_no` | BIGINT | guaranteed-present | `71273140` | FK to case_file. |
| `design_search_cd` | VARCHAR optional | optional | `"03.01.07"` | USPTO design search code (animal category = `03.*`). Used for mark discovery by image type. |

### Table: statement (bulk)

Free-text goods and services descriptions. One row per statement per serial.

| Column | Type | Contract status | Example | Purpose for consumer |
|---|---|---|---|---|
| `serial_no` | BIGINT | guaranteed-present | `71246709` | FK to case_file. |
| `statement_type_cd` | VARCHAR optional | optional | `"GS"` | `'GS'` = goods/services; filter on this for semantic overlap computation. |
| `statement_text` | VARCHAR optional | optional | `"BLANK AND PARTIALLY-PRINTED CARDS AND FORMS FOR INDEXES..."` | Goods text for semantic overlap scoring and historian display. |

### Table: extended_marks (enrichment)

Structured fields parsed from TSDR API responses. Populated by `markery trademark enrich` + `markery trademark reparse`. Preferred over bulk tables for structured field access.

| Column | Type | Contract status | Example | Purpose for consumer |
|---|---|---|---|---|
| `serial_no` | VARCHAR NOT NULL | guaranteed-present | `"71246709"` | PK. Cast from BIGINT when joining to bulk tables. |
| `mark_text` | VARCHAR nullable | optional | `"SOUNDEX"` | Verbal element of the mark. **NULL for purely figurative (design-only) marks** — consumer must handle null. |
| `filing_dt` | DATE nullable | optional | `1927-03-31` | Filing date from TSDR; more reliable than bulk `case_file.filing_dt` for enriched rows. |
| `registration_no` | VARCHAR nullable | optional | `"0230958"` | USPTO registration number. |
| `registration_dt` | DATE nullable | optional | `1927-08-09` | Registration date. |
| `status_cd` | VARCHAR nullable | optional | `"900"` | String status code: `'700'` registered, `'800'` expired, `'900'` cancelled/dead. |
| `goods_desc` | VARCHAR nullable | optional | `"BLANK AND PARTIALLY-PRINTED CARDS AND FORMS FOR INDEXES"` | First goods/services description, truncated at 500 chars. |
| `intl_class` | VARCHAR nullable | optional | `"016"` | International class from TSDR. |
| `owner_name` | VARCHAR nullable | optional | `"RAND KARDEX BUREAU, INC."` | Most recent owner from TSDR. NULL for rows populated via bulk-only enrichment path. |
| `first_use_dt` | VARCHAR nullable | optional | `"1926-01-01"` | First use anywhere; string not DATE. |
| `first_use_comm_dt` | VARCHAR nullable | optional | `"1926-06-01"` | First use in US commerce; string not DATE. |
| `raw_json` | VARCHAR nullable | optional | _(JSON string)_ | Full TSDR response; present for all enriched rows. Source for re-parsing if structured columns are stale. |
| `fetched_dt` | DATE nullable | optional | `2026-06-04` | Fetch date for staleness detection. |

### Table: mark_images (enrichment)

| Column | Type | Contract status | Example | Purpose for consumer |
|---|---|---|---|---|
| `serial_no` | VARCHAR NOT NULL | guaranteed-present | `"71246709"` | PK. |
| `image_data` | BLOB nullable | optional | _(PNG bytes)_ | Mark drawing image for site rendering. NULL until `markery trademark images` is run. |
| `image_format` | VARCHAR nullable | optional | `"PNG"` | Always `"PNG"` currently. |
| `image_size` | INTEGER nullable | optional | `4096` | Byte count; sanity check. |
| `fetched_dt` | DATE nullable | optional | `2026-05-30` | Fetch date. |

---

## 3. entities.duckdb

File: `data/entities.duckdb`  
DDL authority: `src/markery/specialist/matchmaker/entities.py`

### Table: company_entity

| Column | Type | Contract status | Example | Purpose for consumer |
|---|---|---|---|---|
| `entity_id` | INTEGER NOT NULL | guaranteed-present | `1` | Primary key; stable join target from JSONL `entity_id`. |
| `canonical_name` | VARCHAR NOT NULL | guaranteed-present | `"Remington Rand"` | Human-readable entity label used in essay frontmatter `entity` key and display. |
| `entity_type` | VARCHAR nullable | optional | `"corporation"` | Classification; not used in scoring. |
| `industry` | VARCHAR nullable | optional | `"information systems"` | Domain label; not used in scoring. |

### Table: entity_name_variant

| Column | Type | Contract status | Example | Purpose for consumer |
|---|---|---|---|---|
| `variant_id` | INTEGER NOT NULL | guaranteed-present | `3` | PK. |
| `entity_id` | INTEGER NOT NULL | guaranteed-present | `1` | FK to company_entity. |
| `variant_name` | VARCHAR NOT NULL | guaranteed-present | `"REMINGTON RAND INC"` | Uppercase assignee/owner string as it appears in patent or trademark records. Used for fuzzy entity resolution. |
| `source` | VARCHAR NOT NULL | guaranteed-present | `"patent_assignee"` | One of: `patent_assignee` \| `trademark_owner` \| `trademark_search`. Tells a consumer which DB the variant came from. |

---

## 4. candidates.jsonl

File: `projects/<name>/matches/candidates.jsonl`  
One JSON object per line. Generated by `markery match <project>`. One record per patent–trademark pair.

| Field | Type | Contract status | Example | Purpose for consumer |
|---|---|---|---|---|
| `entity_id` | int | guaranteed-present | `1` | FK to entities.duckdb `company_entity.entity_id`. |
| `entity` | str | guaranteed-present | `"Remington Rand"` | Canonical entity name; display and grouping. |
| `patent_no` | str | guaranteed-present | `"US2152606A"` | Joins to `patents.patent_no`. |
| `patent_title` | str nullable | optional | `"Card Index"` | Display label; null if signals not yet run. |
| `patent_grant_dt` | str nullable | optional | `"1939-03-28"` | ISO8601. Used for `date_score`; also copied to essay frontmatter. |
| `patent_assignee` | str nullable | optional | `"REMINGTON RAND INC"` | Uppercase; display and cross-check against entity variants. |
| `cpc_classes` | str[] | guaranteed-present | `["B42F"]` | 4-char CPC prefixes; input to `class_score`. May be `[]`. |
| `trademark_serial` | int | guaranteed-present | `71417978` | Integer serial. Cast to VARCHAR when joining to trademarks.duckdb enrichment tables. |
| `trademark` | str nullable | nullable | `"VARIADEX"` | Verbal mark text. **null for purely figurative marks** — consumer must handle null. |
| `tm_filing_dt` | str nullable | optional | `"1939-04-07"` | ISO8601; copied to essay frontmatter. |
| `tm_reg_no` | str nullable | optional | `"0371824"` | USPTO registration number; display use. |
| `tm_owner` | str nullable | optional | `"KARDEX SYSTEMS, INC."` | Owner at time of scoring; display use. |
| `score` | float | guaranteed-present | `0.7993` | Composite score; see §10 Score semantics. |
| `title_name_hit` | bool | guaranteed-present | `false` | True if mark text appears in patent title. |
| `abstract_name_hit` | bool | guaranteed-present | `false` | True if mark text appears in patent abstract. |
| `goods_title_overlap` | float | guaranteed-present | `0.2` | Jaccard overlap of goods tokens with title tokens. |
| `goods_abstract_overlap` | float | guaranteed-present | `0.0` | Jaccard overlap of goods tokens with abstract tokens. |

**Full example record:**
```json
{
  "entity_id": 1,
  "entity": "Remington Rand",
  "patent_no": "US2152606A",
  "patent_title": "Card Index",
  "patent_grant_dt": "1939-03-28",
  "patent_assignee": "REMINGTON RAND INC",
  "cpc_classes": ["B42F"],
  "trademark_serial": 71417978,
  "trademark": "VARIADEX",
  "tm_filing_dt": "1939-04-07",
  "tm_reg_no": "0371824",
  "tm_owner": "KARDEX SYSTEMS, INC.",
  "score": 0.7993,
  "title_name_hit": false,
  "abstract_name_hit": false,
  "goods_title_overlap": 0.2,
  "goods_abstract_overlap": 0.0
}
```

---

## 5. confirmed.jsonl

File: `projects/<name>/matches/confirmed.jsonl`  
One JSON object per line. Written by the researcher (or `markery match confirm` — D029, not yet implemented).

| Field | Type | Contract status | Example | Purpose for consumer |
|---|---|---|---|---|
| `patent_no` | str | guaranteed-present | `"US1261167A"` | Joins to `patents.patent_no`. |
| `trademark_serial` | int | guaranteed-present | `71246709` | Integer serial. Cast to VARCHAR for enrichment table joins. |
| `trademark` | str nullable | nullable | `"SOUNDEX"` | Verbal mark. null for figurative marks. |
| `entity_id` | int | guaranteed-present | `1` | FK to `company_entity.entity_id`. |
| `entity` | str | guaranteed-present | `"Remington Rand"` | Canonical entity name. |
| `type` | str | guaranteed-present | `"product"` | Relationship category. Currently always `"product"`; enum open for extension. |
| `note` | str | guaranteed-present | `"Russell Soundex patent assigned to Remington Typewriter..."` | Researcher annotation. May be `""`. |

**Full example record:**
```json
{
  "patent_no": "US1261167A",
  "trademark_serial": 71246709,
  "trademark": "SOUNDEX",
  "entity_id": 1,
  "entity": "Remington Rand",
  "type": "product",
  "note": "Russell Soundex patent (1918) assigned to Remington Typewriter Company; commercialized as SOUNDEX by successor Rand Kardex Bureau (filed 1927)."
}
```

---

## 6. rejected.jsonl

File: `projects/<name>/matches/rejected.jsonl`  
One JSON object per line. Written by `markery match auto-disposition`.

| Field | Type | Contract status | Example | Purpose for consumer |
|---|---|---|---|---|
| `patent_no` | str | guaranteed-present | `"US1234567A"` | Joins to `patents.patent_no`. |
| `trademark_serial` | int | guaranteed-present | `71000001` | Integer serial. |
| `trademark` | str nullable | nullable | `"ACME"` | null for figurative marks. |
| `entity_id` | int | guaranteed-present | `2` | FK to `company_entity.entity_id`. |
| `entity` | str | guaranteed-present | `"Acme Corp"` | Canonical entity name. |
| `rejection_note` | str | guaranteed-present | `""` | Human annotation. Empty string `""` for auto-rejections. |
| `auto_rejected` | bool | guaranteed-present | `true` | `true` = machine-generated; `false` = manual researcher rejection. |
| `rejection_reasons` | str[] | guaranteed-present | `["score 0.320 < threshold 0.40"]` | Reason strings from auto-disposition logic. Empty list `[]` for manual rejections. |

**Full example record:**
```json
{
  "patent_no": "US1234567A",
  "trademark_serial": 71000001,
  "trademark": "ACME",
  "entity_id": 2,
  "entity": "Acme Corp",
  "rejection_note": "",
  "auto_rejected": true,
  "rejection_reasons": ["score 0.320 < threshold 0.40", "date gap 22.1y > ceiling 20y"]
}
```

---

## 7. Essay frontmatter

File: `projects/<name>/content/<slug>.md`  
Frontmatter is YAML between `---` delimiters at the start of the file.

**Slug convention:** `{trademark_slug}-{patent_no_lower}` where `trademark_slug = re.sub(r'[^a-z0-9]+', '-', (trademark or 'figurative').lower()).strip('-')`.  
Example: `double-eagle-us1645089a`, `figurative-us1710083a`.

### All frontmatter keys

All keys below are written by `markery historian scaffold`. Keys marked **enforced** are checked by `markery historian validate`; essays failing these checks exit non-zero.

| Key | Type | Enforced | Example | Purpose for consumer |
|---|---|---|---|---|
| `title` | str | yes | `"SOUNDEX — US1261167A"` | Display title for site pages and digest output. |
| `trademark_serial` | int | yes — must resolve in `case_file` | `71246709` | Primary trademark join key. Cast to VARCHAR for enrichment table queries. |
| `trademark` | str | yes | `"SOUNDEX"` | Verbal mark text. `"(figurative)"` for design-only marks — consumer must handle this sentinel. |
| `tm_filing_dt` | str YYYY-MM-DD | yes — must appear in essay body | `"1927-03-31"` | Trademark filing date; used in date display and validate body check. |
| `patent_no` | str | yes — must resolve in `patents` | `"US1261167A"` | Primary patent join key. |
| `patent_grant_dt` | str YYYY-MM-DD | yes — must match `patents.grant_dt` | `"1918-04-02"` | Grant date; cross-validated against DB on every validate run. |
| `entity` | str | yes — must match `company_entity` or variant | `"Remington Rand"` | Entity label; used to group essays and look up `entity_id`. |
| `tm_reg_no` | str | no | `"0230958"` | USPTO registration number; display use. |
| `tm_owner` | str | no | `"RAND KARDEX BUREAU, INC."` | Owner at registration; display use. |
| `patent_assignee` | str | no | `"Remington Typewriter Company"` | Assignee at grant; display and cross-check. |
| `date_gap` | str | no | `"9.0 years"` | Human-readable gap between grant and filing; display use. |

**Full frontmatter example:**
```yaml
---
title: "SOUNDEX — US1261167A"
trademark_serial: 71246709
trademark: "SOUNDEX"
tm_filing_dt: "1927-03-31"
tm_reg_no: "0230958"
tm_owner: "RAND KARDEX BUREAU, INC."
patent_no: "US1261167A"
patent_grant_dt: "1918-04-02"
patent_assignee: "Remington Typewriter Company"
entity: "Remington Rand"
date_gap: "9.0 years"
---
```

---

## 8. library/index.jsonl

File: `library/index.jsonl`  
Global passage index shared across all projects. One JSON object per line. Written by `markery librarian index`. Each record is one extracted passage from a secondary source work.

| Field | Type | Contract status | Example | Purpose for consumer |
|---|---|---|---|---|
| `work_slug` | str | guaranteed-present | `"archer-big-business-and-radio"` | Source work identifier; joins to `library/works/<slug>/`. |
| `author` | str nullable | optional | `"Archer, Gleason Leonard, 1880-"` | Author string from library catalog; display use. |
| `title` | str nullable | optional | `"Big business and radio"` | Work title; display use. |
| `year` | int nullable | nullable | `1938` | Publication year. **May be null** when not recorded in catalog. |
| `section` | str | guaranteed-present | `"RCA's governmental origins (1919)"` | Passage heading from `excerpts.md` (`###` level). Used as retrieval key. |
| `passage` | str | guaranteed-present | `"the Radio Corporation of America originated in 1919..."` | Extracted passage text; primary content for historian context cards. |
| `page` | str nullable | optional | `"pp. 4–5"` | Page reference; display and citation use. May be empty string. |
| `context` | str | guaranteed-present | `""` | Additional editorial context. May be empty string. |
| `indexed_at` | str | guaranteed-present | `"2026-06-04T17:45:13.991959+00:00"` | ISO8601 timestamp with timezone; staleness detection. |

**Full example record:**
```json
{
  "work_slug": "archer-big-business-and-radio",
  "author": "Archer, Gleason Leonard, 1880-",
  "title": "Big business and radio",
  "year": null,
  "section": "RCA's governmental origins (1919)",
  "passage": "the Radio Corporation of America originated in 1919 at the suggestion of certain officials of the United States Government during the hectic days of international reconstruction following the World War.",
  "page": "pp. 4–5",
  "context": "",
  "indexed_at": "2026-06-04T17:45:13.991959+00:00"
}
```

---

## 9. library/index.duckdb — passage_embeddings

File: `library/index.duckdb`  
DDL authority: `src/markery/specialist/librarian/index.py`  
Populated by `markery librarian index --embed`. Requires `sentence-transformers` (`pip install 'markery[librarian]'`).

### Table: passage_embeddings

| Column | Type | Contract status | Example | Purpose for consumer |
|---|---|---|---|---|
| `work_slug` | TEXT | guaranteed-present | `"archer-big-business-and-radio"` | Joins to `index.jsonl` on `work_slug + section` to retrieve full passage text. |
| `passage_id` | INTEGER | guaranteed-present | `0` | 0-based position in `index.jsonl`. Stable until `markery librarian index --rebuild`. |
| `section` | TEXT | guaranteed-present | `"RCA's governmental origins (1919)"` | Section heading; secondary join/display key. |
| `passage` | TEXT | guaranteed-present | `"the Radio Corporation of America..."` | Passage text stored inline for vector search without requiring a second read of index.jsonl. |
| `embedding` | FLOAT[] | guaranteed-present | _(384-element float array)_ | Sentence embedding. Model: `all-MiniLM-L6-v2` (384 dimensions). Used for cosine similarity ranking. |

---

## 10. Score semantics

The `score` field in `candidates.jsonl` is a float produced by `total_score()` in `src/markery/specialist/matchmaker/score.py`:

```
score = date_score(grant_dt, filing_dt)
      + class_score(cpc_classes, class_hints)
      + min(0.25, semantic_score(...))
```

### Component ranges

| Component | Range | Signal description |
|---|---|---|
| `date_score` | [-0.4, 0.5] | 0.5 for same-year grant/filing; decays linearly over 20 years; negative when trademark predates patent grant (not disqualifying). |
| `class_score` | 0.0 or 0.3 | 0.3 if any CPC class prefix appears in the project's `class_hints` (from `project.json`). Falls back to hardcoded `PRODUCT_CLASSES = {"B42F","B42D","B41J","B41L","G06C","G06K","G09F"}` if `class_hints` is absent. |
| `semantic_score` | [0.0, 0.25] | Capped at 0.25. Components: `title_name_hit` (+0.20), `abstract_name_hit` (+0.10), `goods_title_overlap` > 0.05 (+0.10), `goods_abstract_overlap` > 0.05 (+0.05). |

**Theoretical maximum:** 1.05. Strong confirmed pairs score 0.70–0.85 in practice.

**Consumer interpretation:** Score ordering is meaningful within a single project but not across projects with different `class_hints`. A score above 0.70 with `title_name_hit=true` is a strong confirm signal. A score above 0.70 driven by `class_score + date_score` alone (both signal fields false, both overlap fields near zero) requires researcher review — it likely reflects temporal coincidence rather than a product relationship.

---

## 11. Documented gaps and status

| Gap | Impact | Status |
|---|---|---|
| `case_file` full column set not explicitly declared in Markery DDL (CSV-inferred schema) | Columns outside §2 are not stable across USPTO dataset rebuilds | Informational; bulk schema is externally controlled. Contract scope limited to the 6 columns in §2. |
| `serial_no` BIGINT/VARCHAR split between bulk and enrichment layers | Cross-layer joins fail silently if not cast | Documented here; DDL comment in `trademark/build.py`. |
| `confirmed.jsonl` `type` field values not fully enumerated | Only `"product"` used to date | Documented here; open for extension without a version bump. |
| `library/wants.jsonl` shape | Not a LangGraph contract surface | Informational only; excluded from contract scope. |
