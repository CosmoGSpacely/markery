# Instruction Card: Patent Figure Fetch

## When to use

When a confirmed patent has a figure available (check BRIEF.md `figures_available`) that has not yet been described in the match essay, or when you need to describe a figure for a patent not yet in the figures database.

A figure description strengthens the patent section of a match essay: it grounds the technical description in what the patent drawing actually shows, not just what the title claims.

## What this produces

Running `markery patent figures <patent_no>` fetches the first drawing page from EPO OPS as a TIFF, converts it to PNG, and stores it as a BLOB in `patents.duckdb.patent_figures`.

The figure is then available to:
- The site builder (renders as `<img>` on the match essay page)
- You, for description: ask the researcher to display the figure so you can describe what it shows

## Where the output lands

`patents.duckdb.patent_figures` — one row per patent (figure_no = 1 for first page). The site builder reads from this table to render figures in the HTML output.

## Request to researcher

**Human-readable:**
> "Please fetch the figure for [patent_no] so I can describe it in the essay: `markery patent figures [patent_no]`"

**To view the figure in-session:**
> "After fetching, please display the figure so I can describe what it shows."

**Structured (for agentic use):**
```json
{
  "action": "patent_figure",
  "target": {"patent_no": "US2178457A"},
  "project": "information-systems",
  "reason": "Figure needed to describe the visible-card mechanism in the KARDEX essay"
}
```

## Note on availability

Not all patents have drawings accessible via EPO OPS for the pre-1940 period. If the fetch returns nothing (404 from the images endpoint), the patent may have been published before drawings were systematically digitized, or the specific drawing page may not be in the EPO corpus. In that case, note in the essay that "no figure is available in the current dataset."

## Expected output

The command prints success or a 404 message. After a successful fetch, the figure appears in the site when rebuilt (`markery site build <project>`).
