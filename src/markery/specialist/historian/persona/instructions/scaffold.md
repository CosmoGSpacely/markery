# Instruction Card: Historian Scaffold

## When to use

After confirming a pair (writing it to `confirmed.jsonl`), to generate an essay skeleton with all factual fields pre-filled from the database. The scaffold is the starting point for every research essay; it is never submitted without historian expansion and validation.

## Command

```bash
markery historian scaffold <project> <slug>
```

The slug matches the confirmed pair's slug as computed by the historian (e.g. `double-eagle-us1645089a`).

## Output

A Markdown file written to `projects/<project>/content/<slug>.md` with:
- Required frontmatter keys: `title`, `trademark_serial`, `trademark`, `tm_filing_dt`, `patent_no`, `patent_grant_dt`, `entity`
- Structured sections with factual data pre-filled (dates, goods descriptions, CPC classes, assignee names)
- Empty narrative sections for the historian to complete

## Essay slug convention

The scaffold file is named `{tm_slug}-{patent_no}.md` where:
- `tm_slug = re.sub(r'[^a-z0-9]+', '-', (trademark or "figurative").lower()).strip('-')`
- `patent_no` is the lowercased patent number (e.g. `us979019a`)

The publisher computes essay paths using the same formula. Using any other naming breaks essay discovery.

## Notes

- Run `markery historian validate <project> <slug>` after completing the essay to check all required fields against the database.
- Scaffold output is deterministic from the confirmed pair record. Re-running scaffold will overwrite the file — do not run it on a completed essay.
