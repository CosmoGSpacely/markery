# USPTO TSDR API

Python client and reference for the USPTO Trademark Status and Document Retrieval (TSDR) API.

## Authentication

All requests require a `USPTO-API-KEY` header. Obtain a key at [account.uspto.gov/api-manager](https://account.uspto.gov/api-manager/).

Store the key in a `.env` file:
```
USPTO_API_KEY=your_key_here
```

The client loads it automatically via `python-dotenv`.

## Rate Limits

- 60 requests/minute per key (general)
- 4 requests/minute for PDF, ZIP, and multi-case downloads

## Base URL

```
https://tsdrapi.uspto.gov
```

## Endpoints

### Get case status
```
GET /ts/cd/casestatus/sn{serial}/info
Accept: application/json
```
Returns a large JSON object with status, parties, goods/services, design codes, and prosecution history. Serial number uses the `sn` prefix here.

### Get mark image (PNG)
```
GET /ts/cd/rawImage/{serial}
```
Returns the raw PNG of the trademark drawing. **No `sn` prefix** — just the bare serial number. This is the correct format; `sn{serial}` returns 404.

Response: `image/png` binary, typically 6–8 KB for scanned historical marks. Valid PNG with standard IHDR header.

### Get last update time
```
GET /last-update/info.json?sn={serial}
Accept: application/json
```

### Bulk case status
```
GET /ts/cd/caseMultiStatus/{type}?ids={id1},{id2},...
```
`type` is `sn` (serial) or `rn` (registration). Counts against the 4/min rate limit.

### Download document (PDF/ZIP)
```
GET /ts/cd/casedoc/sn{serial}/{doc_id}/content.{format}
```
`format` is `pdf` or `zip`. `doc_id` comes from the case status response. Counts against the 4/min rate limit.

### Download full case PDF
```
GET /ts/cd/casestatus/sn{serial}/download.pdf
Accept: application/pdf
```
Returns a PDF of the complete case file. Counts against the 4/min rate limit.

## Endpoint Prefix Summary

| Endpoint | Serial prefix |
|---|---|
| Case status | `sn{serial}` |
| Raw image | `{serial}` (bare) |
| Document download | `sn{serial}` |
| Last update | query param `sn={serial}` |

## Python Client

All functions are in `tsdr_client.py`. The module reads the API key from the environment on import.

```python
from tsdr_client import get_case_status, get_trademark_image, download_document

# JSON case status
status = get_case_status("71165547")

# Mark image — returns (bytes, mime_type) or (None, None) on failure
image_data, mime_type = get_trademark_image("71165547")

# PDF document (doc_id from case status response)
pdf = download_document("71165547", "DOC123", format_type="pdf")
```

## What the Case Status Response Includes

The response is `application/json` by default. The Content-Encoding header may say `gzip` even when the body is not compressed — use `response.content.decode('utf-8')` and `json.loads()` directly rather than `response.json()`, which may fail on the encoding mismatch.

Top-level: `{"trademarks": [{...}]}`. The single trademark object has these useful sub-structures:

### `trademarks[0].status`

| Field | Type | Notes |
|---|---|---|
| `serialNumber` | int | Application serial number |
| `filingDate` | str | ISO date, e.g. `"1939-12-14"` |
| `usRegistrationNumber` | str | Registration number (without leading zeros) |
| `usRegistrationDate` | str | ISO date, or null if not registered |
| `status` | int | Numeric status code — 6xx live, 7xx cancelled, 8xx abandoned, 9xx expired |
| `extStatusDesc` | str | Human-readable status description |
| `markDrawingCd` | str | Single digit (`"1"`, `"3"`, `"5"`) — differs from CSV dataset's 4-char codes |
| `markElement` | str | The mark text |
| `currentLoc` | str | Physical file location; `"FILE DESTROYED"` for many pre-1940 marks |

### `trademarks[0].gsList[0]`

| Field | Type | Notes |
|---|---|---|
| `description` | str | Goods/services description |
| `internationalClasses` | list | `[{"code": "016", "description": "..."}]` |
| `usClasses` | list | Same structure, US class codes |
| `firstUseDate` | int | Integer YYYYMMDD — may have `00` for unspecified month or day |
| `firstUseInCommerceDate` | int | Same |

### First-use date encoding

First-use dates are integers (e.g. `19160101`, `19240100`, `18850000`). A `00` in the day or month position means the applicant did not specify that component — this was permitted under USPTO rules of the period. Coercing `00` to `01` introduces false precision; the project stores these as ISO 8601 reduced-precision strings: `"YYYY-MM-DD"`, `"YYYY-MM"`, or `"YYYY"` depending on what was filed.

### `trademarks[0].parties.ownerGroups`

List of ownership records. Each group contains owner name, entity type, and address by party type code. Ownership changed hands for many 1920s–1930s marks through mergers; multiple owner groups represent transfer history.

## Notes

- The TSDR viewer at `tsdr.uspto.gov/img/{serial}/large` returns 403 (requires browser session cookie).
- `tsdrs.uspto.gov` does not resolve publicly.
- Swagger/OpenAPI spec endpoints (`/v1/api-docs`, `/swagger.json`) return 401 even with a valid key.
- The official Swagger UI is at [developer.uspto.gov/swagger/tsdr-api-v1](https://developer.uspto.gov/swagger/tsdr-api-v1) but renders as HTML, not machine-readable JSON.
- Historical marks (pre-1940) often have `"currentLoc": "FILE DESTROYED"` — the paper file is gone but the digital image still exists via `rawImage`.

## Database Schema Notes

### Two-tier TSDR fetch approach

TSDR mark data splits across two tables based on whether the mark has a visual image:

**Design and stylized marks (drawing code 3xxx, 5xxx)** — have scanned drawings in the TSDR `rawImage` store. Fetched into `mark_images`. These are the primary visual research targets.

**Typeset and standard character marks (drawing code 1xxx, 4xxx)** — the `rawImage` endpoint returns 404 because no drawing was ever filed with the application. Full case status (filing dates, goods/services, first-use dates) is fetched from the case status endpoint and stored in `mark_case_status`. Brought in for analysis when they belong to the same entity and class as a primary image mark (e.g., KARDEX, SOUNDEX, FAVORITE).

### mark_images table

```sql
CREATE TABLE mark_images (
    serial_no    VARCHAR PRIMARY KEY,
    image_data   BLOB NOT NULL,
    image_format VARCHAR NOT NULL,   -- MIME type, e.g. 'image/png'
    image_size   INTEGER NOT NULL,   -- byte length
    fetched_dt   DATE NOT NULL DEFAULT CURRENT_DATE
);
```

Images are stored as raw bytes. To read in Python:
```python
row = conn.execute(
    "SELECT image_data FROM mark_images WHERE serial_no = ?", ["71165547"]
).fetchone()
png_bytes = bytes(row[0])
```

Note: DuckDB's `length()` does not accept BLOB. Use the `image_size` column or `octet_length(image_data)` instead.

### mark_case_status table

```sql
CREATE TABLE mark_case_status (
    serial_no           VARCHAR PRIMARY KEY,
    mark_text           VARCHAR,
    filing_dt           DATE,
    registration_no     VARCHAR,
    registration_dt     DATE,
    status_cd           VARCHAR,
    goods_desc          VARCHAR,       -- first goods/services description
    intl_class          VARCHAR,       -- Nice class code(s), comma-separated
    first_use_dt        VARCHAR,       -- ISO 8601 reduced precision (see First-use date encoding)
    first_use_comm_dt   VARCHAR,       -- ISO 8601 reduced precision
    raw_json            VARCHAR,       -- full JSON response
    fetched_dt          DATE NOT NULL DEFAULT CURRENT_DATE
);
```

Fields map from: `trademarks[0].status` → mark_text, filing_dt, registration_no, status_cd; `trademarks[0].gsList[0]` → goods_desc, intl_class, first_use dates.

### Drawing code discrepancy

The CSV dataset and TSDR API use different drawing code formats:

| Source | Format | Example |
|---|---|---|
| CSV dataset (`case_file.mark_draw_cd`) | 4-character | `3000`, `5W23`, `1000` |
| TSDR API (`markDrawingCd`) | Single digit | `3`, `5`, `1` |

The first character of the CSV code matches the API digit. All filter queries use the CSV 4-character format.

### Status code discrepancy

The CSV dataset uses numeric status codes (e.g. `626`, `710`). The TSDR API also returns a `tm5Status` field (0–15, EUIPO-harmonized) with `tm5StatusDesc`. Ignore `tm5Status` for this project — the CSV numeric codes are the ones in `case_file.status_cd`.

### Owner table joins

The `owner` table has multiple rows per `serial_no` when ownership was transferred. Join carefully: use `own_entity_cd` or filter by `own_type_cd` to distinguish original applicant from subsequent owners.

### Known quirks

- Owner names are inconsistently cased (`Guild Products Corporation` vs `GUILD PRODUCTS CORPORATION` for the same entity). Use `UPPER()` for matching.
- `serial_no` is stored as `VARCHAR` throughout, not `INTEGER`.
- Physical prosecution files for many early marks carry `"currentLoc": "FILE DESTROYED"` in TSDR. Mark images (via `rawImage`) are often still available even when the paper file is destroyed.
- Six marks in the 1900–1939 scope show status 626/624 (live) in the 2011 snapshot — these were genuinely long-lived marks.

### Data gaps

`event.csv` (~3 GB, prosecution history) and foreign application data were not loaded. See D004 and D005 in `DEFERRED.md` for reopen triggers.

## References

- [TSDR API Catalog](https://developer.uspto.gov/api-catalog/tsdr-data-api)
- [Swagger UI](https://developer.uspto.gov/swagger/tsdr-api-v1)
- [Bulk Download FAQ](https://developer.uspto.gov/faq/tsdr-api-bulk-download)
- [API Key Manager User Guide](https://developer.uspto.gov/files/tsdr-api-key-manager-user-guide)
- Support: [TEAS@uspto.gov](mailto:TEAS@uspto.gov)
