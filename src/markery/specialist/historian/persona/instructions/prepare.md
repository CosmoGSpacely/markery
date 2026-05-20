# Instruction Card: Session Prepare

## When to use

At the start of every research session, before reviewing candidates, writing essays, or making any requests to other specialists. `prepare` reads the current project state and writes `BRIEF.md` — the working document the historian reads to orient each session.

## What this produces

Running `markery historian prepare <project>` generates `projects/<project>/matches/BRIEF.md` with:

| Section | Contents |
|---|---|
| `confirmed_count` | Number of confirmed patent-trademark pairs |
| `candidate_count_unreviewed` | Candidates not yet reviewed (Y or N) |
| `signals_available` | Patent numbers with abstract text available for signal enrichment |
| `figures_available` | Patent numbers with drawing figures stored in `patents.duckdb` |
| `enriched_trademarks` | Serial numbers with TSDR enrichment in `extended_marks` |
| Project state prose | Summary of confirmed pairs with notes |

## Where the output lands

`projects/<project>/matches/BRIEF.md` — overwritten on each run. Not committed to version control; regenerate at the start of each session.

## Request to researcher

**Human-readable:**
> "Please run `markery historian prepare <project>` so I can read the current project state before we begin."

**Structured (for agentic use):**
```json
{
  "action": "prepare",
  "target": {"project": "information-systems"},
  "project": "information-systems",
  "reason": "Session start — need current project state before reviewing"
}
```

## How to use BRIEF.md

After `prepare` runs, read `BRIEF.md` before taking any action:

- **`signals_available`** — if this list is non-empty and signal enrichment has not been run, consider requesting `markery patent signals <project>` before reviewing
- **`enriched_trademarks`** — check this before requesting trademark enrichment; marks already listed do not need re-fetching
- **`figures_available`** — check this before requesting `markery patent figures <patent_no>`; already fetched figures do not need re-fetching
- **`candidate_count_unreviewed`** — if this is large relative to session time, consider using `--min-score` to focus review on the strongest candidates

## Expected output

The command prints a one-line confirmation and the path to the generated file. If the project directory or `candidates.jsonl` does not exist, it will print an error — verify the project name matches a directory under `projects/`.
