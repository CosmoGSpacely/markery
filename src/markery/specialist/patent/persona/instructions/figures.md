# Instruction Card: Patent Figures

## When to use

When a match essay needs to describe what a patent drawing shows, or when the site builder needs figure assets to render on essay pages.

Check `BRIEF.md figures_available` first. If the patent number is already listed there, the figure is stored in `patents.duckdb` and no fetch is needed.

Not all pre-1940 patents have digitized figures accessible via EPO OPS. If a fetch returns nothing, see the "No figure available" section below.

## Two commands

**Single patent — for a specific patent identified during research:**
```bash
markery patent figures <patent_no>
```
Example:
```bash
markery patent figures US1261167A
```
Fetches the first drawing page from EPO OPS, converts it to PNG, and stores it as a BLOB in `patents.duckdb` (`patent_figures` table, `figure_no = 1`).

**Project batch — for all confirmed pairs in a project:**
```bash
markery patent fetch <project> --confirmed
```
Iterates over every patent in `confirmed.jsonl` and fetches figures for any not already stored. Prints a per-patent stored/skipped summary.

**High-scoring candidates (before review):**
```bash
markery patent fetch <project> --min-score 0.70
```
Fetches figures for candidates above the score threshold. Useful when preparing for a review session — figures display automatically in the reviewer when available.

## What this produces

A BLOB row in `patents.duckdb.patent_figures`:

| Column | Contents |
|---|---|
| `patent_no` | Full patent number, e.g. `US1261167A` |
| `figure_no` | Always 1 (first drawing page) |
| `image_data` | Raw PNG bytes |
| `fetched_dt` | Date retrieved |

The site builder reads from this table to render `<figure class="patent-figure">` elements. The interactive reviewer (`markery review`) opens available figures automatically via `xdg-open`.

## After fetching

Regenerate BRIEF.md to update `figures_available`:
```bash
markery historian prepare <project>
```

Rebuild the site to include the figures:
```bash
markery site build <project>
```

## No figure available

If the fetch prints "skipped (already stored or no figure available)" and the patent is not already stored, the figure is not accessible via EPO OPS. This happens for patents published before drawing digitization was systematic, or where EPO's corpus has a gap.

In the essay, note: *"No drawing figure is available in the current dataset for this patent."* This is not a research gap — the bibliographic record (title, abstract, CPC class, inventors, assignee) is still in `patents.duckdb` and fully usable.
