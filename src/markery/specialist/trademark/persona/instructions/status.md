# Instruction Card: Trademark Status

## When to use

To inspect row counts for all tables in `trademarks.duckdb`. Use to confirm that a build, enrich, or fetch command stored records as expected, or to check overall database health before starting a review session.

## What this produces

A table printed to stdout showing each DuckDB table name and its current row count.

## Command

```bash
markery trademark status
```

Example output:
```
trademarks.duckdb:
  case_file                        142,318
  extended_marks                     3,241
  intl_class                       412,900
  mark_images                          208
  mark_status                        3,241
  owner                            139,874
  statement                        389,211
```

## Notes

`extended_marks` grows as you enrich projects. `mark_images` grows as you fetch images. `case_file`, `owner`, `statement`, and `intl_class` are populated by `markery trademark build` from the USPTO bulk CSV and do not change between builds.

If `extended_marks` is 0, run `markery trademark enrich-project <project>` before attempting a model review.
