# EPO OPS Reference

The EPO Open Patent Services (OPS) is a REST API providing access to the EPO worldwide patent database. Markery uses it as the primary source for `patents.duckdb`.

Full API reference: `src/markery/specialist/patent/EPO.md`

---

## Rate Limits (free tier)

| Limit | Value |
|---|---|
| Requests per minute | ~30 |
| Daily quota | ~10,000 results |
| Results per page | 100 (RESULTS_PER_PAGE in build.py) |

A 403 Forbidden response means the daily quota is exhausted. Use `--resume` the following day to continue from where the build stopped.

---

## Query Pattern

Markery queries by CPC class and publication date range, filtered to US patents:

```
cpc=<CLASS> AND pd within "<YYYYMMDD>,<YYYYMMDD>" AND pn=US
```

Fetches are broken into 5-year windows to stay within per-query result limits.

---

## Credentials

Stored in `.env`:
```
EPO_CONSUMER_KEY=your_key_here
EPO_CONSUMER_SECRET=your_secret_here
```

The secret value may have a leading space in the EPO developer portal — this is stripped automatically by `common/auth.py`.

Verify: `markery patent verify-credentials`
