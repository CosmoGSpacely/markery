# Instruction Card: Citation Chain Expansion

## When to use

After confirming a patent-trademark pair, use citation chain expansion to discover related patents the same entity held — patents that cited the confirmed patent, or patents that the confirmed patent cited. These backward-cited records are candidates for additional confirmed pairs.

This is the standard organic corpus growth pattern: each confirmed pair seeds further research rather than requiring a new class sweep.

## What this produces

```bash
markery patent citations <patent_no>
```

Fetches the backward citation list for `<patent_no>` from EPO OPS. For each cited patent number not already in `patents.duckdb`, the full bibliographic record is fetched and inserted. Prints a count of new patents added.

Example:
```bash
markery patent citations US1261167A
```

## After running

Check what was added:
```bash
markery status
```

Review the new records against the project's entity list to identify potential additional pairs. If a cited patent was assigned to the same entity, pull it and add it to `seed_patents.json`:

```bash
markery patent pull US<new_number>A
```

Then regenerate candidates to score the new records:
```bash
markery match <project> --force
```

## Scope and limits

**Citation depth:** `markery patent citations` fetches one level of backward citations (patents cited *by* the target patent). It does not recurse into the citations of citations. If deeper exploration is needed, run it again on each newly added patent.

**Pre-1940 coverage:** Citation records for early 20th-century patents are incomplete. Many filings from this period cite few or no prior patents. A result of "0 new patents added" is common and does not indicate an error.

**Cross-entity citations:** Cited patents may belong to competitors or unrelated entities. Check the assignee field of each newly added patent before treating it as a candidate for the project's entities. Use `markery matchmaker list` to see which entity IDs are in scope.

## Pattern: confirm → pull → cite → match

```
1. markery review <project>        # confirm a pair
2. markery patent pull <patent_no> # ensure the patent is stored (if not already)
3. markery patent citations <patent_no>  # expand to cited patents
4. markery status                  # check what was added
5. markery match <project> --force # rescore with new records
6. markery review <project>        # review any new candidates
```
