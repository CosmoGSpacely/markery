# Patent Specialist

A Markery specialist agent for acquiring and maintaining the shared patent corpus. The Patent specialist fetches records from the EPO Open Patent Services API, stores them in `patents.duckdb`, and provides programmatic access to patent data for other specialists.

---

## Role

The Patent specialist is a **data acquisition agent**. It has no research or editorial function. Its job is to ensure that `patents.duckdb` contains the records a project needs, that those records are correctly stored, and that the fetch process can be resumed after interruptions.

---

## Owns

`data/patents.duckdb` — bibliographic records, CPC classifications, inventors, drawing figures.

`data/patents_fetch_log.json` — resume state tracking which CPC class / year-window combinations have been fetched.

---

## Key Commands

```bash
# Bulk fetch by CPC class and year range
markery patent build --classes B42F B42D --year-start 1900 --year-end 1939

# Resume an interrupted fetch
markery patent build --classes B42F B42D --year-start 1900 --year-end 1939 --resume

# Load seed patents from a project file (no API call)
markery patent build --seed-only --seed-path projects/<project>/seed_patents.json

# Fetch a single patent by number
markery patent pull <patent_no>

# Fetch backward citations for a patent
markery patent citations <patent_no>

# Fetch drawing figure for a patent
markery patent figures <patent_no>

# Verify EPO OPS credentials
markery patent verify-credentials
```

---

## Data Source

**EPO Open Patent Services (OPS)** — REST API providing access to the EPO worldwide patent database. Queries use CQL (Contextual Query Language) to filter by CPC class and publication date range.

Rate limits apply: the EPO OPS free tier has a daily quota. Large class sweeps (10,000+ patents) may require multiple sessions with `--resume` between them.

See `reference/epo-ops.md` for rate limit details and quota management.

---

## How to Use

Drop this folder into a Claude project with access to the Markery repository. The specialist can then plan and execute patent builds, advise on CPC class selection, and interpret fetch log state.

```
"The information-systems project needs G06C patents from 1900 to 1939.
 The last fetch hit the daily quota at G06C 1930. What is the resume command?"

"Which CPC classes cover mechanical calculators and tabulating machines?"

"Fetch US1261167A and add it to the patent database."
```

---

## Reference

| File | Contains |
|---|---|
| `identity.md` | Agent role, capabilities, and explicit limits |
| `instructions/build.md` | When and how to run a patent build |
| `reference/epo-ops.md` | EPO OPS rate limits, quota, and CQL syntax |
| `src/markery/specialist/patent/EPO.md` | Full EPO OPS API reference |
