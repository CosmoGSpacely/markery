# Instruction Card: Review Candidates

## When to use

After `markery librarian extract` has written passage candidates to `candidates.md`, use `review` to decide which passages to accept into `excerpts.md`. Run this after every extraction pass before indexing.

Two modes are available: interactive (the default) and `--auto-accept`.

## Commands

**Interactive — review one candidate at a time:**
```
markery librarian review <slug>
```
Each pending passage is printed with context. Respond `y` (accept), `n` (reject), or `s` (skip for now). Accepted passages are appended to `excerpts.md` and the candidate is marked `accepted`; rejected candidates are marked `rejected`.

**Non-interactive — accept all pending candidates at once:**
```
markery librarian review <slug> --auto-accept
```
All `pending` candidates are accepted and appended to `excerpts.md` without any prompts. Use this in automated or batch workflows, or when you have already inspected the candidates in a prior session and trust the extraction quality.

## What this produces

- `library/works/<slug>/excerpts.md` — accepted passages appended
- `library/works/<slug>/candidates.md` — status markers updated (`pending` → `accepted` or `rejected`)

## After review

Run `markery librarian index` to rebuild the keyword index with the newly accepted passages. Run `markery librarian index --embed` if semantic search is needed.
