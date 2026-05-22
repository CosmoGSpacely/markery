# Instruction Card: Trademark Enrich Project

## When to use

Before a model review session, to pre-fetch TSDR data (mark images, status codes) for all candidates or confirmed pairs in a project that lack enrichment. Run after `markery match preflight` identifies gaps, or proactively before beginning a review.

Check credential access first:
```bash
markery trademark verify-credentials
```

## What this produces

For each enriched serial number:
- Mark image stored in `mark_images` table in `trademarks.duckdb`
- Status code stored in `mark_status` or `extended_marks`

Reports counts: `N image(s) stored, M status record(s) stored`.

## Commands

**Enrich from confirmed pairs (default):**
```bash
markery trademark enrich-project <project>
```

**Enrich from candidates above a score threshold:**
```bash
markery trademark enrich-project <project> --source candidates --min-score 0.5
```

**Force re-fetch even if already stored:**
```bash
markery trademark enrich-project <project> --force
```

## Rate limit handling

USPTO TSDR enforces per-key rate limits. If a request fails, the command logs the failure and continues. Check the output for skipped serials and re-run to pick them up after the rate limit window resets.

## After enriching

Mark images become available to `markery historian card` and the publisher automatically. Run `markery trademark status` to confirm storage counts.
