# Instruction Card: Candidate Generation

## When to use

When starting a project, after adding new entities or name variants, or after the patent or trademark databases have been extended to cover new scope.

Do **not** regenerate if only rescoring is needed. If signal enrichment has already been run, regenerating will clear those fields. Use `markery match rescore <project>` instead.

## What this produces

`projects/<project>/matches/candidates.jsonl` — one JSON line per scored patent-trademark pair, sorted by score descending.

`projects/<project>/matches/pipeline_state.json` — records the generation timestamp, candidate count, and score percentiles.

## Commands

**Basic generation — structural scores only:**
```bash
markery match <project>
```

**Generate + enrich with text signals + rescore in one step (recommended before first review):**
```bash
markery match <project> --full
```

`--full` runs all three passes: generate → `markery patent signals` enrichment → rescore. Use this at the start of a new project or after extending the database scope. Equivalent to running the three commands separately.

**Force regeneration when candidates have already been enriched:**
```bash
markery match <project> --force
```

Required when `candidates.jsonl` has been enriched. Without `--force`, the CLI blocks to prevent discarding signal data. `--force` discards enrichment and regenerates from scratch.

**After generation, check uncertainty band and missing data:**
```bash
markery match <project> --resolve
```

Reports how many pairs fall in the 0.40–0.60 uncertainty band, which patents are missing abstracts, and which marks are missing goods descriptions. Identifies pairs that can be resolved from existing database data without additional API calls.

**Set a minimum score threshold (default: 0.10):**
```bash
markery match <project> --min-score 0.30
```

Pairs scoring below this threshold are excluded from `candidates.jsonl`. Raising the threshold reduces file size and speeds up review at the cost of possibly excluding weak-but-valid pairs. The default (0.10) includes most pairs; 0.30 focuses on pairs with at least some temporal alignment.

**Rescore existing candidates after manual signal enrichment:**
```bash
markery match rescore <project>
```

See `instructions/rescore.md` for when to rescore vs regenerate.

## Prerequisite checks

Before generating:
1. Entity registry is populated: `markery matchmaker list`
2. Project's `entities.txt` contains the correct entity IDs
3. Patent and trademark databases cover the project's date and class scope: `markery status`

## After generation

Review pipeline state:
```bash
markery match status <project>
```

Then enrich marks before reviewing:
```bash
markery trademark enrich-project <project> --source candidates --min-score 0.40
```

Then review:
```bash
markery review <project>
```
