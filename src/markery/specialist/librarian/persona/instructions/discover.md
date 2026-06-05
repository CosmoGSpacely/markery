# Instruction Card: Discover

## When to use

To surface secondary literature cited by a Wikipedia article — works that the editorial community considers authoritative for a research domain. Use before `search-sources` when the domain has a well-developed Wikipedia article with a References section.

## Command

```bash
markery librarian discover --wikipedia "<Article Name>" --add-wants
```

`--add-wants` adds any unacquirable works (borrow-only, not on IA) to `library/wants.jsonl`.

## Output

A list of citations parsed from the Wikipedia article's `{{cite book}}` and `{{cite journal}}` templates, with acquisition status for each (available on IA, borrow-only, not found).

## Notes

- Wikipedia prose is never used as a research source — only its citations. `discover` extracts what Wikipedia editors have cited, not what Wikipedia says.
- The effectiveness of `discover` depends on how densely cited the target article is. Niche research domains (specific industrial sub-sectors, narrow trademark categories) often have thin Wikipedia coverage and sparse citation graphs. For niche domains, use `search-sources` with an author-targeted query instead.
- `--add-wants` requires the ILL queue at `library/wants.jsonl`. Borrow-only IA works are routed there with `wanted` status.
