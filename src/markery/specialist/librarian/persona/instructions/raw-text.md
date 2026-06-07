# Instruction Card: Raw Text Path

## When to use

When you need the filesystem path to a work's downloaded full text — for example, to inspect the raw text directly, diagnose extraction issues, or determine why `extract` is producing no candidates. The raw text file is gitignored and may be absent if the work was registered without downloading (borrow-only IA works, manually entered ILL works).

## Command

```
markery librarian raw-text <slug>
```

Prints the absolute path to `library/works/<slug>/raw_text.txt`. Exits 1 if the slug is not registered or if `raw_text.txt` does not exist, with a hint to run `acquire`.

## What this produces

Stdout: the path. Nothing is written or modified.

## If raw_text.txt is absent

The work was registered without full-text download (borrow-only, ILL, or manual entry). Options:
- Re-run `markery librarian acquire <ia_identifier>` with the original IA identifier (not the slug) to fetch the text
- For ILL or physical copies, the text must be transcribed or scanned manually
