# Instruction Card: Historian Card

## When to use

During a review session, to get a compact view of a specific candidate pair. `card` generates a ~250-token context document for a single candidate, suitable for loading as focused context before making a confirm/reject decision.

## Command

```bash
markery historian card <project> <slug>
```

The slug is the candidate's `patent_no` lowercased with non-alphanumeric chars replaced by hyphens, e.g. `us1261167a`.

With token logging:
```bash
MARKERY_TOKEN_LOG=tests/benchmarks/<project>.jsonl \
  markery historian card <project> <slug> --tokens
```

## Output

A structured block covering:
- Trademark: serial number, mark text, filing date, goods description
- Patent: number, title, grant date, CPC classes, assignee
- Score breakdown: date score, class score, total
- Entity: canonical name, entity type

## Notes

- Use `markery historian digest` first to identify which slugs are worth reviewing.
- Card output is model-agnostic: all factual fields are pre-populated from the database; no knowledge of the records is required beyond what the card provides.
- Token counts for card are benchmarked in `tests/benchmarks/README.md`.
