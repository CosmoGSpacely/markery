# Instruction Card: Trademark Build

## When to use

When starting a new project or when the trademark database does not yet cover the marks your project needs.

Choose a route based on what you have available:

| | Route A: Bulk CSV | Route B: TSDR API |
|---|---|---|
| Requires | ~4 GB USPTO CSV download | USPTO API key only |
| Populates | All bulk tables + enrichment tables | `extended_marks` only |
| Matchmaker support | Full candidate generation | Manual/seed-based only |
| Best for | Discovery projects | Targeted or post-2011 marks |

## Route A: Bulk CSV

Download the USPTO Trademark Case Files Dataset and extract to `csv/`:
> https://www.uspto.gov/ip-policy/economic-research/research-datasets/trademark-case-files-dataset

```bash
# Full dataset
markery trademark build --csv-dir csv/

# Filtered to a date window
markery trademark build --csv-dir csv/ --date-start 1900-01-01 --date-end 1939-12-31
```

Build time: 2–5 minutes. The resulting database is ~150 MB for the 1900–1939 window.

## Route B: TSDR fetch

```bash
# Fetch a specific mark
markery trademark fetch <serial_no>

# Enrich all marks in a project (after generating candidates)
markery trademark enrich-project <project> --source candidates --min-score 0.40
markery trademark enrich-project <project> --source confirmed
```

## After the build

Confirm row counts:
```bash
markery trademark status
markery status
```
