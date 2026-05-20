# Instruction Card: Entity Forward

## When to use

When you need to understand whether a project entity continued filing trademarks after the project's primary date window (typically post-1939). Use cases:

- **Brand continuity**: did the entity maintain trademark registrations after the confirmed pairs' era? This contextualizes whether the product line survived.
- **Company survival**: filing activity after 1939 is evidence the company continued operating.
- **Research scope expansion**: identifying post-1939 marks that might be relevant to a wider research question or a future project.

Do **not** use this as a substitute for candidate generation. `entity-forward` shows TSDR-enriched marks only — marks already in `extended_marks`. It does not surface bulk-only marks or marks that have not yet been fetched from TSDR.

## What this produces

```bash
markery trademark entity-forward <entity_name> [--after-year YEAR]
```

Queries `extended_marks` for marks where the entity's known name variants appear as the owner, filed after the specified year. Default cutoff: 1939.

Output: a table of `serial_no`, `filing_dt`, `mark_text`, `status_cd` for each match.

Example:
```bash
markery trademark entity-forward "Remington Rand" --after-year 1939
markery trademark entity-forward "Wilson Jones" --after-year 1945
```

## How matching works

The command joins `entity_name_variant` (from `entities.duckdb`) against `extended_marks` (from `trademarks.duckdb`) via the orchestrator. It matches on owner name variants registered for the entity — the same variants used for candidate generation.

**Prerequisite:** the entity must be registered in `entities.duckdb` with its name variants. Run `markery matchmaker list` to confirm the entity is registered.

## Constraint: extended_marks only

`entity-forward` only surfaces marks that have been fetched via TSDR into `extended_marks`. Marks that exist in the bulk tables (`case_file`) but have not been TSDR-enriched will not appear here, even if they were filed after 1939.

To surface a specific post-1939 mark known from another source, fetch it first:
```bash
markery trademark fetch <serial_no>
```
Then re-run `entity-forward`.

## After running

If post-1939 marks are found that are relevant to the research, their serial numbers can be added to a project's seed records or noted in the research essay as evidence of brand continuity. They are not automatically added to `candidates.jsonl`.
