# LIBRARIAN Acquisition Notes

Findings from Phase 15 P1 manual acquisition work. These notes directly inform
the P2 source adapter implementations — treat them as integration test results
that preceded the code.

---

## Internet Archive

### Identifier pattern

IA identifiers for pre-1928 books typically follow `shorttitlewords00authorsurname`
(e.g. `officemanagement00gall`, `scientificoffice00leff`). This pattern is not
guaranteed — many guesses return empty `{}` from the metadata API. When guessing
fails, the metadata API is more reliable than the search API for discovery (see
below).

### Checking access type

```
GET https://archive.org/metadata/<identifier>
```

Returns JSON. Key fields:
- `metadata.title`, `metadata.creator`, `metadata.date` — bibliographic
- `metadata.access-restricted-item` — `true` means borrow-only (requires IA
  login and a borrowable copy). Absent or empty string means open access.
- `files[]` — list all available formats; look for `<identifier>_djvu.txt`

Open-access items confirmed working in P1:
- `officemanagement00gall` — Galloway, *Office Management* (1918)
- `scientificoffice00leff` — Leffingwell, *Scientific Office Management* (1917)

Borrow-only items confirmed in P1 (in-copyright or restricted reprints):
- `controlthroughcom00yate` — Yates (1989)
- `beforecomputeribm00cort` — Cortada (1993)
- `hermanhollerithf00aust` — Austrian (1982)

### Downloading text

Open-access items with a `_djvu.txt` file:
```
GET https://archive.org/download/<identifier>/<identifier>_djvu.txt
```
This returns a 302 redirect to a CDN URL (e.g. `dn790009.ca.archive.org`).
Follow the redirect (`curl -sL`). File size is typically 500 KB – 2 MB for a
full book.

### djvu.txt format

OCR output with page numbers embedded in two ways:
1. As a standalone number on its own line: `\n145\n`
2. In running headers: `164  METHODIZING  MEANS  OF  COMMUNICATION`

Pages are not uniformly marked. The most reliable extraction strategy:
- `grep -n "search term"` to find line numbers
- `sed -n 'start,endp'` to pull surrounding context
- Identify the nearest page number by scanning backward from the grep hit

OCR quality is good for 1910s–1920s books but not perfect. Extra spaces within
words are common (e.g. `sys  tematic`). Normalize with `tr -s ' '` or regex
before passage extraction.

### Search API

`archive.org/advancedsearch.php?q=...&fl[]=identifier&fl[]=title&output=json`
returns JSON but is unreliable for discovering pre-1928 books. The full-text
search returns modern items first; keyword queries for book topics often return
CIA reading room documents or playing card collections. **Do not rely on the
search API for discovery** — use known identifiers from prior research, or the
`gutendex` API for Gutenberg items.

---

## Project Gutenberg via Gutendex

The Gutendex API (`gutendex.com/books/`) is the correct interface — do not
hit `gutenberg.org` directly for search.

### Search

```
GET https://gutendex.com/books/?search=<query>
```

Returns JSON with `results[]`. Each result has:
- `id` — Gutenberg book ID
- `title`, `authors[]`
- `formats{}` — keys are MIME types; look for `text/plain; charset=utf-8`

### Downloading text

```python
url = book['formats']['text/plain; charset=utf-8']
# e.g. https://www.gutenberg.org/ebooks/6435.txt.utf-8
# This redirects to: https://www.gutenberg.org/cache/epub/<id>/pg<id>.txt
```

Follow the redirect. Text is clean UTF-8 with standard line endings. No OCR
artifacts. Better quality than IA djvu.txt for the same title when both exist.

Gutenberg collection skews toward literary texts. Business and management
literature from the 1910s–1920s is mostly absent. Confirmed absent in P1:
- Claude Hopkins, *Scientific Advertising* (1923) — not on Gutenberg
- Thorstein Veblen, *Theory of Business Enterprise* (1904) — not on Gutenberg

---

## Sources confirmed not viable

**HathiTrust**: Data API retired July 2024. No programmatic full-text access.
Do not implement an adapter.

**Google Books**: API returns metadata and snippets only — cannot return full
text programmatically for any item. Use only for discovery (finding IA or
Gutenberg copies of known titles), never as a text source.

---

## Public domain threshold

In the US, works published **before 1928** are in the public domain and may be
freely reproduced. Works published 1928–1977 may still be under copyright
depending on registration and renewal. US government publications (USPTO,
Census Bureau, Department of Commerce) are always public domain regardless of
date.

Practical consequence for the P2 adapter: always check `metadata.date` before
downloading. Flag works dated 1928 or later for human review before storing
text — they may be borrow-only for a reason even if the metadata API returns
no `access-restricted-item`.

---

## Recommended discovery workflow (P2 design input)

1. Try Gutendex search first — cleaner text, simpler API.
2. If not on Gutenberg, guess IA identifier from `shorttitle00surname` pattern
   and check metadata API.
3. If identifier guess fails, the IA search API is a last resort — expect noise.
4. For government documents (USPTO, Census, Commerce), search IA with the
   issuing agency name + year; identifiers are less predictable.
5. For in-copyright works that exist only as borrow copies, add to
   `library/wants.jsonl` with `status: wanted` rather than attempting download.
