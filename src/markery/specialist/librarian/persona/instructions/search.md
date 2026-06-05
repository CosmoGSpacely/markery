# Instruction Card: Search

## When to use

To retrieve passages from the library by keyword match. Use for targeted lookups when you know a specific term, name, or phrase you are looking for. For broader topical queries, use `markery librarian card --mode semantic` instead.

## Command

```bash
markery librarian search "<query>"
markery librarian search "<query>" --top 10
```

## Output

A ranked list of matching passages from `library/index.jsonl`, showing the work slug, page number, and passage text.

## Notes

- Keyword search matches against the passage text and context field. It is case-insensitive but not stemmed — "advertising" does not match "advertise".
- For semantic/conceptual queries ("animal imagery in commercial branding"), use `markery librarian card "<query>" --mode semantic` instead.
- Results are drawn from indexed passages only. A work must have run through `markery librarian index` before its passages appear in search results.
