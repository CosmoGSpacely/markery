# Instruction Card: Mark Enrichment

## When to use

Before the historian reviews candidates, or before building the site. Enrichment adds mark images and TSDR status data — goods descriptions, first-use dates, registration details — that the review tool displays and the site builder renders.

Enrich after generating candidates, before running `markery review`.

## What this produces

New rows in `mark_images` (image BLOBs) and `extended_marks` (status, goods, dates). Existing rows are skipped unless `--force` is passed.

## Commands

**One mark:**
```bash
markery trademark enrich <serial_no>
markery trademark enrich <serial_no> --force   # re-fetch even if stored
```

**All marks in a project:**
```bash
# From confirmed pairs
markery trademark enrich-project <project> --source confirmed

# From candidates above a score threshold
markery trademark enrich-project <project> --source candidates --min-score 0.40
```

## Notes

- Enrichment is idempotent by default. Re-running skips already-stored marks.
- The `--force` flag re-fetches and overwrites existing records.
- For marks where TSDR returns no image (older or destroyed files), `mark_images` will have no row. The review tool handles this gracefully.
- USPTO API rate limits apply. Large enrich-project runs may take several minutes.
