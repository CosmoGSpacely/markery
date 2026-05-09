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

Key fields under `trademarks[0].status`:
- `serialNumber`, `filingDate`, `usRegistrationNumber`, `usRegistrationDate`
- `status` — numeric status code (6xx live, 7xx cancelled, 8xx abandoned, 9xx expired)
- `extStatusDesc` — human-readable status
- `markDrawingCd` — drawing type code (single digit in this API; differs from CSV dataset's 4-char codes)
- `markDrawDesc` — text description of drawing type
- `markElement` — the mark text
- `currentLoc` — physical file location (e.g. `FILE DESTROYED` for old records)
- `designSearchList` — design search codes

Under `trademarks[0].parties.ownerGroups`: owner name, entity type, address by party type code.

Under `trademarks[0].gsList`: goods/services with US and international class codes, first-use dates, and description text.

## Notes

- The TSDR viewer at `tsdr.uspto.gov/img/{serial}/large` returns 403 (requires browser session cookie).
- `tsdrs.uspto.gov` does not resolve publicly.
- Swagger/OpenAPI spec endpoints (`/v1/api-docs`, `/swagger.json`) return 401 even with a valid key.
- The official Swagger UI is at [developer.uspto.gov/swagger/tsdr-api-v1](https://developer.uspto.gov/swagger/tsdr-api-v1) but renders as HTML, not machine-readable JSON.
- Historical marks (pre-1940) often have `"currentLoc": "FILE DESTROYED"` — the paper file is gone but the digital image still exists via `rawImage`.

## References

- [TSDR API Catalog](https://developer.uspto.gov/api-catalog/tsdr-data-api)
- [Swagger UI](https://developer.uspto.gov/swagger/tsdr-api-v1)
- [Bulk Download FAQ](https://developer.uspto.gov/faq/tsdr-api-bulk-download)
- [API Key Manager User Guide](https://developer.uspto.gov/files/tsdr-api-key-manager-user-guide)
- Support: [TEAS@uspto.gov](mailto:TEAS@uspto.gov)
