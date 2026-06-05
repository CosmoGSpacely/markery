# Instruction Card: Index

## When to use

After completing `markery librarian extract` and `markery librarian review` (or `extract --auto-accept`) for one or more works. Builds `library/index.jsonl` from all `excerpts.md` files and optionally generates embeddings in `library/index.duckdb` for semantic search.

## Command

```bash
markery librarian index              # keyword index only
markery librarian index --embed      # keyword + semantic embeddings
markery librarian index --rebuild    # force rebuild from scratch
```

## Output

Appends new passage records to `library/index.jsonl`. With `--embed`, also generates sentence-transformer embeddings in `library/index.duckdb`. Reports the number of works indexed and new passages added.

## Excerpt format requirement

`excerpts.md` files must use `###` (H3) headings for passage boundaries. The indexer uses `###` as the delimiter; `##` or `#` headings are not parsed as passage boundaries and produce 0 records with no warning. If a work shows 0 new passages after indexing, check heading levels in its `excerpts.md`.

## Notes

- `--embed` requires `sentence-transformers` installed (`pip install -e ".[librarian]"`).
- Indexing is idempotent by work slug — re-indexing a work that has not changed produces no duplicate records.
- After indexing, verify with `markery librarian search "<topic>"` (keyword) or `markery librarian card "<topic>" --mode semantic`.
