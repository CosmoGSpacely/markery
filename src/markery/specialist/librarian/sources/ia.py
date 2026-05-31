"""Internet Archive source adapter.

Key learnings from P1 manual work (see ACQUISITION_NOTES.md):
- Identifiers follow shorttitle00authorsurname pattern but must be verified.
- Open-access items have access-restricted-item absent/empty in metadata.
- Text is in <identifier>_djvu.txt; follows a 302 redirect to CDN.
- The IA search API is unreliable for old books; prefer direct identifier lookup.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Optional

from .common import IAResult, SourceResult, make_slug, normalize_metadata, _parse_year

_META_BASE = "https://archive.org/metadata"
_SEARCH_BASE = "https://archive.org/advancedsearch.php"
_DL_BASE = "https://archive.org/download"


def search(query: str, max_results: int = 10) -> list[IAResult]:
    """Search IA full-text index. Results are unreliable for pre-1928 books;
    use fetch_metadata with a known identifier when possible."""
    qs = "&".join(f"fl[]={urllib.parse.quote(f)}"
                  for f in ["identifier", "title", "creator", "date",
                             "access-restricted-item"])
    url = (f"{_SEARCH_BASE}?q={urllib.parse.quote(query)}"
           f"&{qs}&output=json&rows={max_results}&sort=date+asc")
    with urllib.request.urlopen(url, timeout=15) as r:
        data = json.load(r)
    results = []
    for doc in data.get("response", {}).get("docs", []):
        creator = doc.get("creator", "") or ""
        if isinstance(creator, list):
            creator = creator[0] if creator else ""
        restricted = doc.get("access-restricted-item", "")
        results.append(IAResult(
            identifier=doc.get("identifier", ""),
            title=doc.get("title", ""),
            author=creator,
            year=_parse_year(str(doc.get("date", ""))),
            access="borrow" if restricted else "open",
        ))
    return results


def fetch_metadata(identifier: str) -> dict:
    """Fetch full metadata JSON for an IA identifier. Returns {} if not found."""
    url = f"{_META_BASE}/{identifier}"
    with urllib.request.urlopen(url, timeout=15) as r:
        return json.load(r)


def is_open_access(meta: dict) -> bool:
    restricted = meta.get("metadata", {}).get("access-restricted-item", "")
    return not restricted


def find_text_filename(identifier: str, meta: Optional[dict] = None) -> Optional[str]:
    """Return the _djvu.txt filename from metadata files list, or None."""
    if meta is None:
        meta = fetch_metadata(identifier)
    files = meta.get("files", [])
    # Canonical name first
    canonical = f"{identifier}_djvu.txt"
    for f in files:
        if f.get("name") == canonical:
            return canonical
    # Any _djvu.txt
    for f in files:
        name = f.get("name", "")
        if name.endswith("_djvu.txt"):
            return name
    return None


def download_text(identifier: str, out_dir: Path) -> Path:
    """Download OCR text for an open-access IA item.

    Raises FileNotFoundError if no text file is available (borrow-only or no OCR).
    """
    meta = fetch_metadata(identifier)
    if not is_open_access(meta):
        raise PermissionError(
            f"IA item '{identifier}' is borrow-only. "
            "Add to library/wants.jsonl via 'markery librarian wants-update'."
        )
    txt_name = find_text_filename(identifier, meta)
    if not txt_name:
        raise FileNotFoundError(
            f"No OCR text file found for IA item '{identifier}'."
        )

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{identifier}.txt"

    url = f"{_DL_BASE}/{identifier}/{txt_name}"
    req = urllib.request.Request(url, headers={"User-Agent": "markery/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        out_path.write_bytes(r.read())
    return out_path


def to_source_result(result: IAResult) -> SourceResult:
    return SourceResult(
        source="ia",
        identifier=result.identifier,
        title=result.title,
        author=result.author,
        year=result.year,
        slug=make_slug(result.title, result.author),
        access=result.access,
    )


def guess_identifiers(title: str, author: str) -> list[str]:
    """Generate candidate IA identifiers to probe when search fails.

    Pattern: shorttitlewords00authorsurname  (see ACQUISITION_NOTES.md)
    Returns up to 4 candidates.
    """
    import re
    # Surname
    if "," in author:
        surname = author.split(",")[0].strip().lower()
    else:
        parts = author.strip().split()
        surname = parts[-1].lower() if parts else ""
    surname = re.sub(r"[^a-z]", "", surname)

    # Title words (drop articles, stop-ish words under 3 chars)
    words = re.findall(r"[a-z]+", title.lower())
    words = [w for w in words if w not in {"the", "a", "an", "of", "in",
                                            "and", "for", "to", "its"}]

    candidates = []
    for n_words in (2, 3, 4):
        prefix = "".join(words[:n_words])[:15]
        if prefix and surname:
            candidates.append(f"{prefix}00{surname}")
    # Also try with first two chars of surname variants
    if len(candidates) < 4 and words and surname:
        prefix = "".join(words[:2])[:12]
        candidates.append(f"{prefix}0{surname[:4]}")

    return list(dict.fromkeys(candidates))  # deduplicate preserving order
