# Instruction Card: Search Sources

## When to use

When looking for secondary literature on a topic without a specific author or title in mind. Searches Internet Archive and/or Project Gutenberg and returns a list of candidate works with suggested acquisition slugs.

## Command

```bash
markery librarian search-sources "<query>" --source ia
markery librarian search-sources "<query>" --source gutenberg
markery librarian search-sources "<query>"   # searches both
```

## Output

A ranked list of works with: title, author, publication year, Internet Archive identifier, and a suggested acquisition slug. The suggested slug is a friendly string for reference; `markery librarian acquire` requires the **raw IA identifier**, not the suggested slug.

## Notes

- **Slug mismatch (D044):** `search-sources` prints a friendly suggested slug (e.g. `presbrey-history-and-development-of-advertising`). `markery librarian acquire` requires the raw IA identifier (e.g. `historydevelopme0000fran`). Use the IA identifier from the search-sources output line, not the suggested slug.
- IA full-text search ranks by metadata relevance, not historical scholarship quality. Abstract queries ("trademark history") often return irrelevant results. Author-targeted queries ("Presbrey advertising history") work better.
- Works already in `library/works/` are not filtered from results — check `markery librarian list` to avoid re-acquiring.
