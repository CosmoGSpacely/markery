# Instruction Card: Pull Single Patent

## When to use

When a specific patent number is known and needs to be in `patents.duckdb` — for example:

- A confirmed pair's patent is not yet in the database (manually identified during research)
- A patent number appears in a trademark filing's goods description or prosecution history
- A historian session identifies a patent by number through historical sources
- A backward citation chain (`markery patent citations`) returns a number not yet stored

Do **not** use `pull` to build a class corpus. For systematic coverage of a CPC class and year range, use `markery patent build --classes ... --year-start ... --year-end ...`.

## What this produces

One row added to each of `patents`, `patent_classes`, `patent_inventors` in `patents.duckdb`. The record is upserted — running pull on an already-stored patent is safe and produces no duplicates.

Figures are **not** fetched by pull. Use `markery patent figures <patent_no>` separately if a drawing figure is needed.

## Command

```bash
markery patent pull <patent_no>
```

Example:
```bash
markery patent pull US1261167A
```

The patent number must be a full EPO-format number: country code + number + kind code (e.g., `US1261167A`, `US2178457A`). The command queries EPO OPS, parses the bibliographic record, and inserts it.

## After pulling

If the patent is relevant to a project's candidates, regenerate candidates to score it:

```bash
markery match <project> --force
```

If the patent is being added as a seed record for a project:

```bash
markery patent build --seed-only --seed-path projects/<project>/seed_patents.json
```

Add the record to `seed_patents.json` first, then run `--seed-only` to load it without an API call.

## Pull as a discovery path

`pull` + `markery patent citations` is the standard pattern for organic corpus growth from a confirmed pair:

1. Confirm a pair — you now have a specific patent number
2. Pull it if it wasn't fetched during the class sweep: `markery patent pull <patent_no>`
3. Fetch its backward citations: `markery patent citations <patent_no>`
4. Review the cited patents — any that the same entity held become new candidate seeds

See `instructions/citations.md` for the full citation expansion workflow.
