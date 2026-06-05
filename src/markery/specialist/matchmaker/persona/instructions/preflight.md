# Instruction Card: Match Preflight

## When to use

Before a review session, to pre-fetch all available enrichment data so the session runs from a fully-enriched candidate set. Preflight runs three steps: signals enrichment, TSDR enrichment for uncertainty-band candidates, and mark image fetch for confirmed pairs.

## Command

```bash
markery match preflight <project>
```

## Steps

1. **Signals enrichment** — enriches all candidates above `--min-score` (default 0.40) with text-match signals: title/name hit, goods/abstract Jaccard overlap. Skips candidates already enriched.
2. **TSDR enrichment** — fetches extended mark data (goods, status, first-use dates) for candidates in the uncertainty band (default 0.40–0.60). Stops on TSDR quota hit.
3. **Mark image fetch** — fetches mark images for all confirmed pairs. Skips serials already in `mark_images`.

A `preflight.json` report is written to `projects/<project>/matches/`.

## Notes

- Preflight is idempotent — re-running skips already-enriched items.
- TSDR quota hits are expected; preflight reports how many were attempted and how many succeeded.
- Running preflight before `markery historian digest` ensures the digest context includes signals for uncertainty-band candidates.
