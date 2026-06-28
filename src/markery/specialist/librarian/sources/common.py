"""Shared dataclasses and helpers for LIBRARIAN source adapters."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

# Admitted normalized license codes (Phase 24 P2 / Phase 30 policy): public domain
# and the permissive CC tiers only. In strict mode, NC / ND / in-copyright /
# unresolved are rejected; the fair-use tier (see normalize_license fair_use)
# instead tags them honestly and acquires them under non-commercial fair use.
ADMITTED_LICENSES = {"PD", "PD-US-expired", "PD-USGov", "CC0", "CC-BY", "CC-BY-SA"}

# Honest non-admitted tags applied in the fair-use tier. Kept distinct from
# ADMITTED_LICENSES so PD/CC items remain identifiable and the site can show
# accurate rights/attribution (transparency strengthens the fair-use posture).
FAIR_USE_TAGS = {"CC-BY-NC", "CC-BY-ND", "CC-BY-NC-ND", "InC", "rights-restricted",
                 "rights-unknown"}


def _fair_use_tag(text: str) -> str:
    """Honest rights tag for an item that does not resolve to an admitted code.

    `text` is the already-lowercased rights string. We are non-commercial, so
    NC/ND are usable; the tag records the real status rather than mislabelling.
    """
    if not text.strip():
        return "rights-unknown"
    nc = any(x in text for x in ("noncommercial", "no-nc", "/nc", "-nc", "by-nc"))
    nd = any(x in text for x in ("noderiv", "no-nd", "/nd", "-nd", "by-nd"))
    if nc and nd:
        return "CC-BY-NC-ND"
    if nc:
        return "CC-BY-NC"
    if nd:
        return "CC-BY-ND"
    if "/inc" in text or "in copyright" in text or "in-copyright" in text:
        return "InC"
    return "rights-unknown"


_UA = "markery/1.0 (https://github.com/CosmoGSpacely/markery)"


def download(url: str, dest, ua: str = _UA):
    """Download a URL to dest (creating parents). Shared by media adapters."""
    import urllib.request
    from pathlib import Path
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": ua})
    with urllib.request.urlopen(req, timeout=60) as r:
        dest.write_bytes(r.read())
    return dest


@dataclass
class MediaResult:
    """A resolved, admissible media item from any PD/free source adapter.

    Adapters return None instead of a MediaResult when the item's rights do not
    resolve to an ADMITTED_LICENSES code (rejected)."""
    source: str            # 'loc' | 'nara' | 'dpla' | 'ia' | 'commons' | 'chronam'
    source_id: str         # stable id within the source
    title: str
    url: str               # direct downloadable media URL
    license: str           # normalized admitted code
    creator: str
    license_url: str
    rights_statement: str
    attribution_text: str
    source_url: str        # human-facing landing page
    date: Optional[int] = None
    kind: str = "photo"


def normalize_license(raw: str, url: str = "", fair_use: bool = False) -> Optional[str]:
    """Map a free-text rights string / rights URI to a license code.

    Handles the encodings used across LoC, NARA, DPLA (rightsstatements.org),
    Internet Archive, and Commons. In strict mode (default) returns an admitted
    code or None (rejecting NC / ND / in-copyright / unknown). In the fair-use
    tier (``fair_use=True``) it never returns None for the rights decision —
    non-admitted items get an honest FAIR_USE_TAGS code so they are acquired
    under non-commercial fair use while staying distinguishable from PD/CC.
    """
    text = f"{raw or ''} {url or ''}".lower()
    if not text.strip():
        return _fair_use_tag(text) if fair_use else None
    # Hard rejects first.
    if any(t in text for t in ("noncommercial", "no-nc", "/nc", "-nc", "noderiv",
                               "no-nd", "/nd", "-nd")):
        return _fair_use_tag(text) if fair_use else None
    if "rightsstatements.org" in text:
        # Admit only the "no copyright" family; reject InC* (in copyright).
        if "/noc" in text or "/nkc" in text:   # NoC-US, NKC
            return "PD"
        if "/inc" in text:
            return _fair_use_tag(text) if fair_use else None
    if "cc0" in text or "publicdomain/zero" in text:
        return "CC0"
    if "by-sa" in text or "by_sa" in text:
        return "CC-BY-SA"
    if "creativecommons.org/licenses/by" in text or re.search(r"\bcc[ -]by\b", text):
        return "CC-BY"
    if any(t in text for t in (
        "public domain", "publicdomain", "no known restrictions",
        "no known copyright", "unaware of any copyright", "not in copyright",
        "no copyright", "pd-",
    )):
        return "PD"
    if "u.s. government" in text or "usgov" in text or "us government work" in text:
        return "PD-USGov"
    return _fair_use_tag(text) if fair_use else None


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
