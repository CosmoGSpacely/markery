"""Wikimedia Commons media source adapter (Phase 24 P2).

Search the File namespace, read each file's rights from the MediaWiki
``extmetadata`` block, and resolve it to an admitted license per the project
policy: admit PD / CC0 / CC-BY / CC-BY-SA; reject NC, ND, all-rights-reserved,
or any file carrying non-empty ``Restrictions`` (trademark / personality / etc.).
"""

from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

_API = "https://commons.wikimedia.org/w/api.php"
_UA = "markery/1.0 (https://github.com/CosmoGSpacely/markery)"

# Admitted normalized license codes (per Phase 24 P2 policy decision).
_ADMITTED = {"PD", "PD-US-expired", "PD-USGov", "CC0", "CC-BY", "CC-BY-SA"}


@dataclass
class CommonsResult:
    title: str          # "File:Example.jpg"
    url: str            # direct media URL
    license: str        # normalized code, or "" if unresolved
    creator: str
    license_url: str
    rights_statement: str
    attribution_text: str


def _api_get(params: dict) -> dict:
    """GET the Commons API as JSON. Isolated so tests can monkeypatch it."""
    qs = urllib.parse.urlencode({**params, "format": "json"})
    req = urllib.request.Request(f"{_API}?{qs}", headers={"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def search(query: str, max_results: int = 10) -> list[str]:
    """Return File-namespace titles matching the query (no rights resolution)."""
    data = _api_get({
        "action": "query", "list": "search", "srsearch": query,
        "srnamespace": 6, "srlimit": max_results,
    })
    return [hit["title"] for hit in data.get("query", {}).get("search", [])]


def _strip_html(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s or "")).strip()


def _ext(extmeta: dict, key: str) -> str:
    return (extmeta.get(key) or {}).get("value", "") or ""


def resolve_license(extmeta: dict) -> Optional[dict]:
    """Map a file's extmetadata to an admitted license, or None to reject.

    Returns {license, license_url, creator, rights_statement, attribution_text}.
    """
    if _ext(extmeta, "Restrictions").strip():
        return None  # trademark / personality / other non-copyright restriction

    raw = _ext(extmeta, "License").strip().lower()
    short = _ext(extmeta, "LicenseShortName").strip()
    short_l = short.lower()

    if "nc" in raw or "nd" in raw or "noncommercial" in short_l or "noderiv" in short_l:
        return None

    code = ""
    if "cc0" in raw or "cc0" in short_l:
        code = "CC0"
    elif raw.startswith("pd") or "public domain" in short_l:
        code = "PD"
    elif raw.startswith("cc-by-sa") or "by-sa" in short_l:
        code = "CC-BY-SA"
    elif raw.startswith("cc-by") or short_l.startswith("cc by"):
        code = "CC-BY"

    if code not in _ADMITTED:
        return None

    creator = _strip_html(_ext(extmeta, "Artist")) or "Unknown"
    license_url = _ext(extmeta, "LicenseUrl").strip()
    rights = short or _ext(extmeta, "UsageTerms") or code
    if code in ("PD", "CC0"):
        attribution = f"{creator} · {rights}" if creator != "Unknown" else rights
    else:
        attribution = f"{creator} / {rights}"
    return {
        "license": code,
        "license_url": license_url,
        "creator": creator,
        "rights_statement": _strip_html(rights),
        "attribution_text": attribution,
    }


def fetch(file_title: str) -> Optional[CommonsResult]:
    """Fetch imageinfo for a File: title and resolve its license. None if rejected."""
    data = _api_get({
        "action": "query", "prop": "imageinfo",
        "iiprop": "url|extmetadata", "titles": file_title,
    })
    pages = data.get("query", {}).get("pages", {})
    for page in pages.values():
        info = (page.get("imageinfo") or [{}])[0]
        if not info:
            return None
        resolved = resolve_license(info.get("extmetadata", {}))
        if resolved is None:
            return None
        return CommonsResult(
            title=file_title,
            url=info.get("url", ""),
            license=resolved["license"],
            creator=resolved["creator"],
            license_url=resolved["license_url"],
            rights_statement=resolved["rights_statement"],
            attribution_text=resolved["attribution_text"],
        )
    return None


def download(url: str, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        dest.write_bytes(r.read())
    return dest
