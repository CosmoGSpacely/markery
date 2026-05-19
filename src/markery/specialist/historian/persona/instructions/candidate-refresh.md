# Instruction Card: Candidate Refresh

## When to use

When the candidate list is stale — for example, after a new entity has been added to the project, after the scoring model has been updated, or when the historian believes relevant pairs may have been missed because entity name variants are incomplete.

Do **not** request a refresh if only signal enrichment is needed. Signal enrichment runs on existing candidates via `markery patent signals <project>`. A full refresh (re-generation) overwrites `candidates.jsonl` and, if enrichment has been run, will lose signal fields unless `--force` is passed explicitly.

## What this produces

Running `markery match <project>` regenerates `candidates.jsonl` from the current state of all three databases: patents, trademarks, and entities. Every patent-trademark pair for every project entity is scored and written out above the minimum-score threshold.

Running with `--force` overwrites an enriched candidate file. Running without `--force` when enrichment exists will warn and stop.

## Where the output lands

`projects/<project>/matches/candidates.jsonl` — overwritten on each run.

`projects/<project>/matches/pipeline_state.json` — updated to reflect the new generation timestamp. `enriched_at` and `rescored_at` are cleared.

## Request to researcher

**Human-readable:**
> "The candidate list may be missing pairs for [entity name]. Please add the missing name variants to entities.duckdb and then run: `markery match information-systems`"

**If enrichment has already been run:**
> "Note: running this will clear the signal enrichment. Either run `markery match rescore` instead (if only rescoring is needed), or run `markery match information-systems --force` to accept the loss of enrichment and regenerate."

**Structured (for agentic use):**
```json
{
  "action": "candidate_refresh",
  "target": {"project": "information-systems"},
  "project": "information-systems",
  "reason": "<state why a refresh is needed — new entity, missing variants, etc.>"
}
```

## Expected output

The command prints candidate counts per entity and a total. After a refresh, regenerate BRIEF.md to update candidate counts and unreviewed highlights.
