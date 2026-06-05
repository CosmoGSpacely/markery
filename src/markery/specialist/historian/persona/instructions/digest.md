# Instruction Card: Historian Digest

## When to use

At the start of a review session, after running `prepare` and before reviewing individual candidates. `digest` produces a compact project state summary (~800–1,200 prompt tokens) suitable for loading as context into a historian session.

## Command

```bash
markery historian digest <project>
```

With token logging:
```bash
MARKERY_TOKEN_LOG=tests/benchmarks/<project>.jsonl \
  markery historian digest <project> --tokens
```

## Output

A structured text document covering:
- Project scope (entities, confirmed pairs, unreviewed candidates)
- Top unreviewed candidates by score with date gaps and CPC classes
- Outstanding gaps (missing signals, missing figures, uncertainty-band pairs)

The output is designed to fit within small-context models. It does not duplicate content from individual candidate cards — use `markery historian card` for per-candidate detail.

## Notes

- Run after `markery match` has generated candidates and `markery match preflight` has enriched signals.
- Token counts for digest are benchmarked in `tests/benchmarks/README.md`. Counts >20% above baseline indicate context growth that should be investigated.
- `MARKERY_CONTEXT_BUDGET` (env var, integer) limits output size. Default 4000 tokens.
