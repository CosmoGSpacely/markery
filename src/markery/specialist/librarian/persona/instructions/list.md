# Instruction Card: List Library Works

## When to use

When you need an inventory of what is in the library — to check whether a specific work has been acquired before running `acquire`, to see passage counts across all works, or to audit the library before a session that depends on secondary literature coverage.

## Commands

**Compact listing (slug, author, year, excerpt count, raw-text flag):**
```
markery librarian list
```

**Verbose listing (includes full title and source):**
```
markery librarian list --verbose
```

## What this produces

Stdout table. Columns: `SLUG`, `AUTHOR`, `YEAR`, `EXC` (excerpt count), `RAW` (✓ if `raw_text.txt` is present, `-` if absent). The excerpt count is the number of passages already in `excerpts.md` — not the number of candidates in `candidates.md`.

If no works exist: prints `No works in library.`

## After listing

If the excerpt count for a work is 0 and `raw_text.txt` is present, the work has been acquired but not extracted. Run `markery librarian extract <slug> --topics "<topic1>" "<topic2>"` to surface relevant passages.
