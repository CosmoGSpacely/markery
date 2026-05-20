# Instruction Card: Candidate Generation

## When to use

When starting a project, after adding new entities or name variants, or after the patent or trademark databases have been extended to cover new scope.

Do **not** regenerate if only rescoring is needed. If signal enrichment has already been run, regenerating will clear those fields. Use `markery match rescore <project>` instead.

## What this produces

`projects/<project>/matches/candidates.jsonl` — one JSON line per scored patent-trademark pair, sorted by score descending.

`projects/<project>/matches/pipeline_state.json` — records the generation timestamp, candidate count, and score percentiles.

## Commands

**Basic generation:**
```bash
markery match <project>
```

**Generate + enrich with text signals + rescore (recommended before review):**
```bash
markery match <project> --full
```

**Force regeneration when candidates have already been enriched:**
```bash
markery match <project> --force
```

**After generation, check uncertainty band and missing data:**
```bash
markery match <project> --resolve
```

**Rescore existing candidates after manual signal enrichment:**
```bash
markery match rescore <project>
```

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
