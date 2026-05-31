# Instruction Card: Wants Queue (ILL)

## When to use

When a work has been identified as relevant but is not freely available (borrow-only on IA, not on Gutenberg, or not yet digitized). The wants queue tracks pending interlibrary loan requests.

Also used after `discover --wikipedia` with `--add-wants` — NOT FOUND citations are automatically appended.

## Commands

**View the queue:**
```
markery librarian wants
markery librarian wants --status wanted
markery librarian wants --status in-progress
markery librarian wants --status acquired
```

**Update a status:**
```
markery librarian wants-update <title-slug> --status in-progress --note "ILL submitted 2026-06-01"
markery librarian wants-update <title-slug> --status acquired --note "Arrived; excerpts added manually"
```

**Discover and auto-add from Wikipedia:**
```
markery librarian discover --wikipedia "Soundex" --add-wants
```

## Status lifecycle

| Status | Meaning |
|---|---|
| `wanted` | Identified as relevant; not yet acquired or requested |
| `in-progress` | ILL request submitted; waiting for copy |
| `acquired` | Copy received; excerpts added (or pending manual entry) |

When `acquire` succeeds for a work in the queue, the status is automatically set to `acquired`.

## What `wants.jsonl` contains

One JSON record per line:
```json
{
  "title": "Control Through Communication",
  "author": "Yates, JoAnne",
  "year": 1989,
  "isbn": null,
  "source_article": "Soundex",
  "added_at": "2026-05-31T00:00:00Z",
  "status": "wanted",
  "note": null
}
```

## For manually acquired works (ILL arrival)

After receiving a physical copy, register it and add excerpts by hand:
```
markery librarian enter <slug> --title "<title>" --author "<author>" --year <year>
```

Then edit `library/works/<slug>/excerpts.md` directly to add verbatim passages with page references. Run `markery librarian index` (P6) afterward to include the new passages in the keyword index.
