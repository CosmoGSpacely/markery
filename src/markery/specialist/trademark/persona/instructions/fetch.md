# Instruction Card: Trademark Fetch

## When to use

To fetch and store a single trademark record from the USPTO TSDR API by serial number. Use when reviewing a specific candidate and `extended_marks` lacks its record, or when `markery trademark enrich-project` skipped a serial you need now.

Verify the serial number format (5–9 digits) and credential access before fetching:
```bash
markery trademark verify-credentials
```

## What this produces

One row upserted into `extended_marks` in `trademarks.duckdb`, containing: mark text, goods/services description, filing date, registration number, status code, and owner name.

## Command

```bash
markery trademark fetch <serial_no>
```

**Re-fetch even if already stored:**
```bash
markery trademark fetch <serial_no> --force
```

## Notes

TSDR occasionally returns empty records for very old marks (pre-1900 filing). If the command reports "not found on TSDR", the mark predates TSDR coverage or the serial number is incorrect. Verify the serial using the USPTO TESS search.

Run `markery trademark status` after fetching to confirm the row count increased.
