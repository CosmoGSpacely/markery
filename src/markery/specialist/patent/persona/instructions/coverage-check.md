# Instruction Card: Patent Coverage Check

## When to use

Before running a full EPO OPS class sweep, to verify that the API has records for the requested class and year range without committing to a full fetch. Prevents wasted quota on classes that return zero results.

## Command

```bash
markery patent coverage-check --classes B42F --year-start 1900 --year-end 1939
```

Multiple classes:
```bash
markery patent coverage-check --classes H04B H01J H03F --year-start 1918 --year-end 1940
```

## Output

A dry-run report showing the expected record count per class/year-window without inserting any records. Classes with zero expected records are flagged.

## Notes

- Zero coverage for a pre-1940 patent class does not necessarily mean no patents exist — it may mean EPO OPS has not reclassified those patents into the CPC system. This is a known limitation for pre-1940 records.
- If coverage-check returns zero for all classes, consider targeted `markery patent pull <patent_no>` for specific known patents instead of a broad sweep.
- Quota impact: coverage-check uses the EPO OPS estimation endpoint, not the full fetch. Impact is minimal but not zero — do not run repeatedly for the same class/window.
