# Instruction Card: Extract Passages

## When to use

After a work has been acquired (`raw_text.txt` exists). Chunks the full text, calls Claude Haiku to identify verbatim passages relevant to specified topics, deduplicates candidates, and writes a staging file for review.

Do not run extraction without topics — unfocused extraction wastes tokens and produces noisy candidates. Provide 2–4 specific research terms.

## Command

```
markery librarian extract <slug> --topics "<topic1>" "<topic2>" [--max-passages N] [--tokens]
```

**Examples:**
```
markery librarian extract galloway-office-management --topics "card index" "filing system" "Remington Rand"
markery librarian extract leffingwell-scientific-office-management --topics "vertical filing" "correspondence" "office equipment" --max-passages 8
```

**`--max-passages N`** — caps deduplicated output (default: 10). Use a lower cap for focused topics.  
**`--tokens`** — prints token usage to stderr after the run.  
**`--auto-accept`** — writes directly to `excerpts.md`, skipping interactive review. Use only for re-runs on a work where extraction quality is already established.

## What this produces

`library/works/<slug>/candidates.md` — staging file (gitignored). Contains up to `--max-passages` passages in `pending` status, each with:
- Verbatim quoted text
- Estimated page reference
- One-sentence context note explaining relevance
- `<!-- status: pending -->` marker

## Token cost

A 1.3 MB text (~40 chunks) costs approximately **86,000 prompt / 2,600 completion tokens** at Haiku rates. Use `--max-passages` and focused topics to stop early once enough candidates are found.

## After extraction

Review the candidates interactively:
```
markery librarian review <slug>
```

Keys: `[a]ccept  [r]eject  [s]kip  [q]uit`

Accepted passages are appended to `library/works/<slug>/excerpts.md` with heading and context note. `candidates.md` is updated with `accepted`/`rejected` status markers.

## Request to researcher

**Human-readable:**
> "Please run `markery librarian extract <slug> --topics "<topic1>" "<topic2>"` to extract relevant passages from the acquired text."

**Structured (for agentic use):**
```json
{
  "action": "extract",
  "target": {"slug": "<slug>", "topics": ["<topic1>", "<topic2>"]},
  "reason": "Surface verbatim passages relevant to current research topics"
}
```

## Expected output

```
Extracting from 'galloway-office-management' (40 chunks, topics: card index, filing system, Remington Rand)
  chunk 40/40…
  15 raw candidates from 40 chunks
  5 after deduplication
  candidates written to library/works/galloway-office-management/candidates.md
  Run: markery librarian review galloway-office-management
```
