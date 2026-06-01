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
├── index.jsonl            Flat keyword index — one record per passage
├── index.duckdb           Embedding index — passage_embeddings table (optional, P7)
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

## Keyword and semantic search index

### index.jsonl

Built by `markery librarian index`. One JSON record per passage with fields:

| Field | Type | Notes |
|---|---|---|
| `work_slug` | string | Directory name in `library/works/` |
| `author` | string | From `metadata.json` |
| `title` | string | From `metadata.json` |
| `year` | integer \| null | From `metadata.json` |
| `section` | string | `### heading` from `excerpts.md` |
| `passage` | string | Verbatim passage text |
| `page` | string | Page reference (e.g. `p. 146`, `pp. 153–154`) |
| `context` | string | Context note collapsed to one line |
| `indexed_at` | ISO-8601 string | Timestamp of last indexing |

Incremental by default: only re-parses works whose `excerpts.md` is newer than the stored `indexed_at`. Use `--rebuild` to force a full reparse.

### index.duckdb — embedding index

Built by `markery librarian index --embed` (requires `pip install 'markery[librarian]'`).

**Embedding model:** `sentence-transformers/all-MiniLM-L6-v2`
- Local inference, no API key required
- ~80 MB model weight, 384-dimension vectors
- Fits the model-agnosticism principle: runs fully offline
- Speed: ~7 passages in under 1 second on CPU

**Why this model:** MiniLM-L6-v2 is well-calibrated for short semantic similarity tasks at very low latency. For historical prose retrieval the 384-dimension space is sufficient; a larger model (e.g. `all-mpnet-base-v2`, 768 dimensions) would not materially improve recall for a corpus this size.

**Substituting an API-based provider:** Replace `_get_model()` and `index_embeddings()` in `src/markery/specialist/librarian/index.py`. The embedding vectors are stored as `FLOAT[]` in DuckDB; as long as the query vector and stored vectors use the same dimensionality, `search_semantic()` requires no other changes.

**DuckDB schema:**

```sql
CREATE TABLE passage_embeddings (
    work_slug TEXT,
    passage_id INTEGER,   -- row index in index.jsonl (0-based)
    section   TEXT,
    passage   TEXT,
    embedding FLOAT[]     -- 384-dimension MiniLM-L6-v2 vector
);
```

Incremental: re-run `index --embed` after adding new passages; already-embedded `passage_id` values are skipped. Use `index --embed --rebuild` to recompute all vectors (required after changing models).

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
