# Instruction Card: Match Auto-Disposition

## When to use

Before a review session, to batch-reject candidates that fail deterministic criteria without model involvement. This reduces the review queue to pairs that genuinely warrant human judgment.

## Command

```bash
markery match auto-disposition <project> --reject-below 0.25
```

Dry run (report only, no writes):
```bash
markery match auto-disposition <project> --reject-below 0.25 --dry-run
```

With a date-gap ceiling:
```bash
markery match auto-disposition <project> --reject-below 0.25 --max-gap-years 20
```

## Criteria applied

A candidate is auto-rejected if **any** of these is true:
- Score below `--reject-below` threshold (default: 0.25)
- Date gap between patent grant and trademark filing exceeds `--max-gap-years` (default: 20)
- No CPC class in the project's product signal set
- Mark is the entity's company name (already excluded by generator, but double-checked here)

## Output

A table of candidates that would be (or were) rejected, with the reasons. Rejected pairs are written to `rejected.jsonl` and excluded from future `markery match` runs.

## Notes

- `--dry-run` before `--reject-below` to calibrate the threshold without committing rejections.
- Auto-disposition is deterministic — no model, no judgment. It rejects pairs that would be rejected by any reasonable reviewer. Borderline pairs remain in the queue for human review.
- Configuration can also be stored in `projects/<project>/matches/auto_disposition.json` for repeatability.
