# Instruction Card: Acquire a Work

## When to use

When a specific work has been identified (via `search-sources` or `discover`) and its Internet Archive or Gutenberg identifier is known. Fetches metadata and full text; registers the work in `library/works/`.

Only call this for open-access works. If `ia_access` is `borrow` or the work is borrow-only, add it to the wants queue with `wants` and proceed to ILL. Do not attempt to acquire borrow-only works.

## Commands

**Discover first (if identifier unknown):**
```
markery librarian search-sources "<title keywords>" --source ia
markery librarian search-sources "<title keywords>" --source gutenberg
```

**Acquire from Internet Archive:**
```
markery librarian acquire <ia_identifier> --source ia
```

**Acquire from Project Gutenberg:**
```
markery librarian acquire <book_id> --source gutenberg
```

**If the identifier is uncertain** — use `search-sources` to confirm, then probe via the IA metadata API pattern `shorttitle00authorsurname` (first word of title + first six chars of author surname).

## What this produces

- `library/works/<slug>/metadata.json` — structured metadata (source, title, author, year, identifier, access type)
- `library/works/<slug>/raw_text.txt` — full downloaded text (gitignored; re-acquirable)

The slug is derived from title and author via `make_slug` — strips subtitle at `; : —` and comma-phrase openers. After acquire runs, proceed to `extract` to surface relevant passages.

## Request to researcher

**Human-readable:**
> "Please run `markery librarian acquire <identifier> --source ia` to fetch the full text of [Title] and register it in the library."

**Structured (for agentic use):**
```json
{
  "action": "acquire",
  "target": {"identifier": "<ia_identifier>", "source": "ia"},
  "reason": "Fetch full text for passage extraction — open-access confirmed"
}
```

## Expected output

```
Acquired 'galloway-office-management'
  library/works/galloway-office-management/metadata.json written
  library/works/galloway-office-management/raw_text.txt written (1.28 MB)
```

If the work is borrow-only, the command will report `access: borrow` and exit without downloading. Route to `markery librarian wants` instead.

## After acquisition

Run `markery librarian extract <slug> --topics "<topic1>" "<topic2>"` to extract relevant passages.
