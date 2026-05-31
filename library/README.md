# Library

Shared secondary literature for all Markery research projects. Works live here
once; each project's `references/` directory holds a pointer (`see:`) to the
relevant slug rather than a copy of the content.

---

## Directory layout

```
library/
├── README.md              This document
├── wants.jsonl            ILL/acquisition queue (one JSON record per line)
└── works/
    └── <slug>/
        ├── metadata.json  Bibliographic record + acquisition provenance
        ├── raw_text.txt   Full acquired text (gitignored; re-acquirable)
        ├── excerpts.md    Curated passages with page refs and context notes
        └── index.md       One-line topic index (one line per passage heading)
```

---

## metadata.json schema

| Field | Type | Notes |
|---|---|---|
| `source` | `"ia"` \| `"gutenberg"` \| `"manual"` | Acquisition route |
| `slug` | string | Matches directory name |
| `title` | string | Full title from source |
| `author` | string | `Surname, First` format |
| `year` | integer \| null | Publication year |
| `isbn` | string \| null | ISBN-13 preferred |
| `ia_identifier` | string \| null | IA item slug (`archive.org/details/<id>`) |
| `ia_access` | `"open"` \| `"borrow"` \| null | IA access level |
| `gutenberg_id` | string \| null | Gutenberg book ID |
| `acquired_at` | ISO-8601 string \| null | Timestamp of acquisition |

---

## excerpts.md format

```markdown
# Excerpts — [Title]

*[Author], [Year]. [Publisher].*

## Overview

One paragraph on what the work argues and why it is relevant.

## Passages

### [Topic heading]

> "Verbatim quotation." (p. N)

Context note: how this passage bears on the project.

### [Another topic]

> "Another quotation." (p. N)

Context note.
```

---

## wants.jsonl schema

One JSON object per line:

| Field | Type | Notes |
|---|---|---|
| `title` | string | Work title |
| `author` | string | Author name |
| `year` | integer \| null | Publication year |
| `isbn` | string \| null | |
| `source_article` | string \| null | Wikipedia article or project that surfaced this want |
| `added_at` | ISO-8601 string | When added |
| `status` | `"wanted"` \| `"in-progress"` \| `"acquired"` | |
| `note` | string \| null | Optional free-text note (e.g. ILL request date) |

---

## Per-project reference pointers

Each project's `references/<slug>.md` is a one-line pointer:

```
see: library/works/<slug>
```

This replaces the per-project excerpt files that existed before Phase 15 P3.
To add a work to a project's scope, create `references/<slug>.md` with
`see: library/works/<slug>`. The historian loads the actual excerpts.md from
`library/works/<slug>/` during sessions.

---

## Sourcing guidelines

- Prefer Internet Archive for open-access public domain works (pre-1928 US).
  Use `markery librarian acquire <ia_identifier>` to fetch and register.
- Project Gutenberg for canonical literary/scientific texts; use
  `markery librarian acquire <gutenberg_id>`.
- For borrow-only or physically acquired works, add to `wants.jsonl` via
  `markery librarian wants-update` or enter manually via `markery librarian enter`.
- `raw_text.txt` files are gitignored (can be multi-MB) and re-acquirable
  on demand. Only `metadata.json` and `excerpts.md` are committed.
- Passages must be verbatim with page numbers. Paraphrase only when quotation
  is impractical; label paraphrases as such.
- Organize passages by topic, not page order.
