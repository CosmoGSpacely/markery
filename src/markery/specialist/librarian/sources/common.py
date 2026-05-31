"""Shared dataclasses and helpers for LIBRARIAN source adapters."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class IAResult:
    identifier: str
    title: str
    author: str
    year: Optional[int]
    access: str  # "open" or "borrow"


@dataclass
class GutenbergResult:
    book_id: str
    title: str
    author: str
    year: Optional[int]


@dataclass
class SourceResult:
    """Normalised result returned by resolve_to_source and used by acquire."""
    source: str            # "ia" or "gutenberg"
    identifier: str        # IA identifier or Gutenberg book ID as str
    title: str
    author: str
    year: Optional[int]
    slug: str              # library/works/<slug>
    access: Optional[str] = None   # "open" | "borrow" | None (Gutenberg)


@dataclass
class WikiCitation:
    title: str
    author: str
    year: Optional[int]
    isbn: Optional[str]
    url: Optional[str]
    template_type: str     # "cite book" or "cite journal"


@dataclass
class WantsEntry:
    title: str
    author: str
    year: Optional[int]
    isbn: Optional[str]
    source_article: Optional[str]
    added_at: str          # ISO-8601 datetime string
    status: str            # "wanted" | "in-progress" | "acquired"
    note: Optional[str] = None


# ---------------------------------------------------------------------------
# Slug helpers
# ---------------------------------------------------------------------------

def make_slug(title: str, author: str) -> str:
    """Return a filesystem-safe slug: surname-title-words.

    Matches the naming convention of existing reference files
    (galloway-office-management, leffingwell-scientific-office-management).
    Subtitles (after :, ;, or —) are stripped before slugging so that a work
    registered via 'enter' and one acquired from IA (which returns full titles)
    produce the same slug.
    """
    # Strip subtitle at first :, ;, em-dash, or comma-phrase opener
    # ("Office management, its principles and practice" -> "Office management")
    main_title = re.split(
        r"[;:]|\s+[—–]\s+|,\s+(?:its|or|being|comprising|including|with)\s+",
        title, maxsplit=1
    )[0].strip()

    # Extract surname: "Galloway, Lee" -> "galloway", "Lee Galloway" -> "galloway"
    if "," in author:
        surname = author.split(",")[0].strip()
    else:
        parts = author.strip().split()
        surname = parts[-1] if parts else author
    surname = re.sub(r"[^a-z0-9]+", "-", surname.lower()).strip("-")

    title_slug = re.sub(r"[^a-z0-9]+", "-", main_title.lower()).strip("-")
    # Remove leading article
    title_slug = re.sub(r"^(a|an|the)-", "", title_slug)
    # Truncate so the full slug stays under ~50 chars
    max_title = 48 - len(surname) - 1
    if len(title_slug) > max_title:
        truncated = title_slug[:max_title]
        last_dash = truncated.rfind("-")
        if last_dash > 8:
            truncated = truncated[:last_dash]
        title_slug = truncated

    return f"{surname}-{title_slug}".strip("-")


# ---------------------------------------------------------------------------
# Metadata normalisation
# ---------------------------------------------------------------------------

def normalize_metadata(source_data: dict, source: str, slug: str) -> dict:
    """Map source-specific metadata to the library/works/<slug>/metadata.json schema."""
    if source == "ia":
        meta = source_data.get("metadata", {})
        restricted = meta.get("access-restricted-item", "")
        access = "borrow" if restricted else "open"
        creator = meta.get("creator", "") or ""
        if isinstance(creator, list):
            creator = creator[0] if creator else ""
        return {
            "source": "ia",
            "slug": slug,
            "title": meta.get("title", ""),
            "author": creator,
            "year": _parse_year(str(meta.get("date", ""))),
            "ia_identifier": meta.get("identifier", ""),
            "ia_access": access,
            "gutenberg_id": None,
            "isbn": None,
        }
    elif source == "gutenberg":
        authors = source_data.get("authors", [])
        author = authors[0].get("name", "") if authors else ""
        return {
            "source": "gutenberg",
            "slug": slug,
            "title": source_data.get("title", ""),
            "author": author,
            "year": source_data.get("copyright_year") or None,
            "gutenberg_id": str(source_data.get("id", "")),
            "ia_identifier": None,
            "ia_access": None,
            "isbn": None,
        }
    else:
        raise ValueError(f"Unknown source: {source!r}")


def _parse_year(s: str) -> Optional[int]:
    m = re.search(r"\b(1[0-9]{3}|20[0-9]{2})\b", s)
    return int(m.group(1)) if m else None
