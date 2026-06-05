# Instruction Card: Historian Validate

## When to use

After completing an essay — whether written by hand, expanded from a scaffold, or drafted by a model — to verify that all factual fields match the database records. Validation is required before any essay can be considered complete.

## Command

```bash
markery historian validate <project> <slug>
```

## What it checks

- All seven required frontmatter keys are present and non-empty: `title`, `trademark_serial`, `trademark`, `tm_filing_dt`, `patent_no`, `patent_grant_dt`, `entity`
- `trademark_serial` resolves against `trademarks.duckdb`
- `patent_no` resolves against `patents.duckdb`
- `tm_filing_dt` matches the record in `case_file`
- `patent_grant_dt` matches the record in `patents`
- `entity` matches the confirmed pair's entity name

## Output

- `PASS` — all checks passed; the essay's factual fields are correct
- `FAIL` — one or more checks failed; specific failures are listed with the expected vs. actual values

## Notes

- A PASS result means the essay's factual skeleton is correct. It does not validate narrative quality or historical interpretation.
- Essays that do not pass validate should not be used as site content.
- Figurative marks (no `mark_id_char` in `case_file`) have `trademark: null` in `confirmed.jsonl`; the scaffold and validator handle this by using `"figurative"` as the slug component.
