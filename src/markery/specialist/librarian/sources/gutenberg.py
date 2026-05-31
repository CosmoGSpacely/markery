"""Project Gutenberg source adapter via Gutendex API.

Gutendex (gutendex.com/books) is the correct search interface.
Do not query gutenberg.org directly for search.
Plain-text URLs from the formats dict follow a 302 redirect; urllib follows it.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Optional

from .common import GutenbergResult, SourceResult, make_slug, normalize_metadata

_GUTENDEX = "https://gutendex.com/books/"


def search(query: str, max_results: int = 10) -> list[GutenbergResult]:
    url = f"{_GUTENDEX}?search={urllib.parse.quote(query)}&languages=en"
    with urllib.request.urlopen(url, timeout=15) as r:
        data = json.load(r)
    results = []
    for book in data.get("results", [])[:max_results]:
        authors = book.get("authors", [])
        author = authors[0].get("name", "") if authors else ""
        results.append(GutenbergResult(
            book_id=str(book["id"]),
            title=book.get("title", ""),
            author=author,
            year=book.get("copyright_year") or None,
        ))
    return results


def fetch_metadata(book_id: int | str) -> dict:
    url = f"{_GUTENDEX}{book_id}/"
    with urllib.request.urlopen(url, timeout=15) as r:
        return json.load(r)


def get_text_url(book: dict) -> Optional[str]:
    formats = book.get("formats", {})
    for mime in ("text/plain; charset=utf-8", "text/plain"):
        if mime in formats:
            return formats[mime]
    return None


def download_text(book_id: int | str, out_dir: Path) -> Path:
    """Download plain text for a Gutenberg book. Follows redirect automatically."""
    book = fetch_metadata(book_id)
    text_url = get_text_url(book)
    if not text_url:
        raise FileNotFoundError(
            f"No plain text format for Gutenberg book {book_id}."
        )
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "raw_text.txt"
    req = urllib.request.Request(text_url, headers={"User-Agent": "markery/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        out_path.write_bytes(r.read())
    return out_path


def to_source_result(result: GutenbergResult) -> SourceResult:
    return SourceResult(
        source="gutenberg",
        identifier=result.book_id,
        title=result.title,
        author=result.author,
        year=result.year,
        slug=make_slug(result.title, result.author),
        access=None,
    )
