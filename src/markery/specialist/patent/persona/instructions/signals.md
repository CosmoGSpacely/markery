# Instruction Card: Patent Signals

## When to use

After generating or updating candidates for a project, before beginning a model review session. Signal enrichment adds text-overlap and keyword scores to each candidate row so the model can reason about relevance without fetching full patent text.

Run `markery status` first to confirm `patents.duckdb` has records for the project's patents. Signals without a patent record produce zero scores.

## What this produces

In-place updates to `projects/<project>/matches/candidates.jsonl`:
- `title_name_hit` — whether the trademark word appears in the patent title
- `abstract_tokens` — token set from patent abstract
- `goods_title_overlap` — Jaccard overlap between patent title tokens and trademark goods description

Also updates `projects/<project>/matches/pipeline_state.json` with an `enriched` timestamp.

## Commands

**Enrich all candidates for a project:**
```bash
markery patent signals <project>
```

## Notes

Signal enrichment reads `candidates.jsonl` and `patents.duckdb`. It does not call any external API and has no quota cost. Re-running is safe — candidates that already have signal fields are overwritten with fresh values.

Run before `markery match preflight` to ensure the signals step reports zero work remaining.
