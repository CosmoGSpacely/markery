# Instruction Card: Trademark Enrichment

## When to use

When a confirmed trademark lacks goods/services description text that would strengthen the correspondence analysis. The G&S description is the primary evidence for what was sold under a mark — without it, the correspondence rests on title and date only.

Check BRIEF.md `enriched_trademarks` first. If the serial number is already listed there, the goods text is in the database and no fetch is needed.

## What this produces

Running `markery trademark enrich-project <project>` fetches case status records from the USPTO TSDR API for confirmed pairs and candidates in the uncertainty band. For each successfully fetched record, `extended_marks.goods_desc` is populated in `trademarks.duckdb`.

For confirmed trademarks, this also populates: `mark_text`, `registration_no`, `registration_dt`, `status_cd`, `intl_class`, `first_use_dt`, `first_use_comm_dt`.

## Where the output lands

`trademarks.duckdb.extended_marks` — one row per serial number. Queryable via:

```sql
SELECT goods_desc FROM extended_marks WHERE serial_no = '71246709'
```

## Request to researcher

**Human-readable:**
> "I need the goods/services description for trademark [serial_no]. Please run: `markery trademark enrich-project information-systems`"

**For a single mark:**
> "Please run: `markery trademark fetch [serial_no]` to fetch the TSDR case status for this mark."

**Structured (for agentic use):**
```json
{
  "action": "trademark_enrich",
  "target": {"project": "information-systems"},
  "project": "information-systems",
  "reason": "<state which mark needs G&S text and why>"
}
```

## Rate limit note

TSDR allows 60 requests per minute. A project with many candidates in the uncertainty band may take several minutes to enrich. The command handles rate limiting automatically.

## Expected output

The command prints counts of images and case statuses stored. After it runs, regenerate BRIEF.md to update `enriched_trademarks`.
