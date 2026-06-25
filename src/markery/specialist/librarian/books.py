"""Book discovery + routing pipeline (Phase 30 P4 — keyless).

Discovers pre-1931 (and other) books via Open Library, then **routes** each:

- digitized (an Internet Archive scan exists) → acquire the free full text with
  the existing ``markery librarian acquire <ia_id>`` (the loop runs it);
- not digitized → queue to ``wants.jsonl`` with a **prepared ILL request** and a
  WorldCat **deep-link** for the human to check holdings and submit the ILL.

Markery never submits an ILL itself (the user requests ILL access and submits the
request). A key-gated OCLC client is intentionally absent here — discovery is
keyless; WorldCat is a human deep-link only.
"""

from __future__ import annotations

import urllib.parse

from markery.specialist.librarian.sources import openlibrary


def worldcat_url(title: str, author: str = "") -> str:
    """A search.worldcat.org deep-link for the human to check holdings."""
    q = f"{title} {author}".strip()
    return f"https://search.worldcat.org/search?q={urllib.parse.quote(q)}"


def prepare_ill(candidate: dict) -> str:
    """Format an ILL request the human can submit through their library."""
    title = candidate.get("title", "")
    author = candidate.get("author", "")
    year = candidate.get("year")
    isbn = candidate.get("isbn")
    lines = [
        "ILL REQUEST",
        f"  Title:  {title}",
        f"  Author: {author or '—'}",
        f"  Year:   {year or '—'}",
        f"  ISBN:   {isbn or '—'}",
        f"  Holdings: {worldcat_url(title, author)}",
        "  → Submit via your library's interlibrary-loan service.",
    ]
    return "\n".join(lines)


def find_books(query: str, max_results: int = 10) -> list[dict]:
    """Discover book candidates via Open Library (keyless)."""
    return openlibrary.search(query, max_results=max_results)


def route(candidate: dict) -> dict:
    """Decide how to obtain a candidate.

    Returns {action, ia_id, worldcat_url, ill_request}. action is 'acquire' when a
    digitized IA copy exists (free full text), else 'ill' (human-submitted)."""
    ia_ids = candidate.get("ia_ids") or []
    if ia_ids:
        return {
            "action": "acquire",
            "ia_id": ia_ids[0],
            "worldcat_url": worldcat_url(candidate.get("title", ""), candidate.get("author", "")),
            "ill_request": "",
        }
    return {
        "action": "ill",
        "ia_id": None,
        "worldcat_url": worldcat_url(candidate.get("title", ""), candidate.get("author", "")),
        "ill_request": prepare_ill(candidate),
    }
