"""Open Library book-discovery adapter (Phase 30 P4 — keyless).

openlibrary.org/search.json is a free, keyless book search. Each doc carries
title/author/year, ISBNs, and ``ia`` identifiers (Internet Archive scans) when a
digitized copy exists — the hook the book pipeline uses to decide "acquire free
full text" vs "queue for ILL".
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request

_BASE = "https://openlibrary.org/search.json"
_UA = "markery/1.0 (https://github.com/CosmoGSpacely/markery)"


def _get(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def search(query: str, max_results: int = 10) -> list[dict]:
    """Return normalized book candidates for a query (keyless).

    Each: {title, author, year, isbn, ia_ids, key}. ``ia_ids`` non-empty means a
    digitized copy may be acquirable from Internet Archive."""
    fields = "title,author_name,first_publish_year,ia,isbn,key"
    url = (f"{_BASE}?q={urllib.parse.quote(query)}"
           f"&fields={fields}&limit={max_results}")
    data = _get(url)
    out: list[dict] = []
    for doc in data.get("docs", [])[:max_results]:
        authors = doc.get("author_name") or []
        isbns = doc.get("isbn") or []
        out.append({
            "title": doc.get("title", ""),
            "author": authors[0] if authors else "",
            "year": doc.get("first_publish_year"),
            "isbn": isbns[0] if isbns else None,
            "ia_ids": doc.get("ia") or [],
            "key": doc.get("key", ""),
        })
    return out
