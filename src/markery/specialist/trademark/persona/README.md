# Trademark Specialist

A Markery specialist agent for acquiring and maintaining the shared trademark corpus. The Trademark specialist builds `trademarks.duckdb` from two sources: the USPTO Trademark Case Files Dataset (bulk CSV) and the USPTO TSDR API (per-mark enrichment).

---

## Role

The Trademark specialist is a **data acquisition and enrichment agent**. It has no research or editorial function. Its job is to ensure that `trademarks.duckdb` contains the records a project needs, and that those records are enriched with the mark images, goods descriptions, and status data required for candidate scoring and review.

---

## Owns

`data/trademarks.duckdb` — bulk USPTO tables (`case_file`, `owner`, `statement`, `classification`, and companions) plus TSDR enrichment tables (`mark_images`, `extended_marks`).

---

## Key Commands

```bash
# Build from bulk USPTO CSV (full dataset)
markery trademark build --csv-dir csv/

# Build with a date filter
markery trademark build --csv-dir csv/ --date-start 1900-01-01 --date-end 1939-12-31

# Fetch a single mark from TSDR (into extended_marks)
markery trademark fetch <serial_no>

# Enrich one mark (image + status)
markery trademark enrich <serial_no>

# Enrich all marks in a project
markery trademark enrich-project <project> --source confirmed
markery trademark enrich-project <project> --source candidates --min-score 0.50

# Row counts for all tables
markery trademark status

# Verify USPTO API credentials
markery trademark verify-credentials
```

---

## Two Data Routes

**Route A — Bulk CSV:** Loads the full USPTO trademark dataset. Populates all bulk tables. Required for matchmaker candidate generation. Needs the ~4 GB CSV download.

**Route B — TSDR API:** Fetches specific marks by serial number into `extended_marks`. No bulk tables. Suitable when you already know which marks you need, or for marks not in the 2011 bulk snapshot.

See `instructions/build.md` for when to use each route.

---

## How to Use

```
"Enrich all confirmed marks in the information-systems project with images and status."

"Fetch serial number 71235764 from TSDR and store it."

"The trademark database needs marks filed 1900–1939.
 I have the CSV files in csv/. What is the build command?"
```

---

## Reference

| File | Contains |
|---|---|
| `identity.md` | Agent role, capabilities, and explicit limits |
| `instructions/build.md` | When and how to build the trademark database |
| `instructions/enrich.md` | When and how to enrich marks via TSDR |
| `reference/bulk-tables.md` | Schema overview for the USPTO bulk tables |
| `src/markery/specialist/trademark/TSDR.md` | Full TSDR API reference |
