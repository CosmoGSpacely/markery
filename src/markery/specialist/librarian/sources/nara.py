"""National Archives (NARA) media source adapter (Phase 30 P1 — closes D069).

catalog.archives.gov exposes a JSON API. Records carry a ``useRestriction``
(status "Unrestricted" for PD-eligible federal records) and digital objects with
file URLs. Federal records that are unrestricted are U.S. Government public domain.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Optional

from .common import MediaResult, download as _download

_BASE = "https://catalog.archives.gov/api/v2"
_UA = "markery/1.0 (https://github.com/CosmoGSpacely/markery)"


def _api_get(path: str, params: dict) -> dict:
    qs = urllib.parse.urlencode(params)
    req = urllib.request.Request(f"{_BASE}{path}?{qs}", headers={"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def search(query: str, max_results: int = 10) -> list[str]:
    """Return NARA naIds (National Archives Identifiers) matching the query."""
    data = _api_get("/records/search", {
        "q": query, "limit": max_results, "availableOnline": "true",
    })
    hits = data.get("body", {}).get("hits", {}).get("hits", [])
    out: list[str] = []
    for h in hits[:max_results]:
        nid = h.get("_id") or h.get("_source", {}).get("record", {}).get("naId")
        if nid:
            out.append(str(nid))
    return out


def _first_object_url(record: dict) -> str:
    for obj in record.get("digitalObjects", []) or []:
        u = obj.get("objectUrl") or obj.get("url")
        if u:
            return u
    return ""


def fetch(na_id: str) -> Optional[MediaResult]:
    """Fetch one NARA record by naId; admit if useRestriction is unrestricted."""
    data = _api_get("/records/search", {"naId": na_id, "limit": 1})
    hits = data.get("body", {}).get("hits", {}).get("hits", [])
    if not hits:
        return None
    record = hits[0].get("_source", {}).get("record", {})
    restriction = record.get("useRestriction", {})
    status = (restriction.get("status", {}) or {})
    status_val = status.get("value", status) if isinstance(status, dict) else status
    # Unrestricted federal records → U.S. Government public domain.
    if str(status_val).strip().lower() not in ("unrestricted", "", "none"):
        return None
    url = _first_object_url(record)
    if not url:
        return None
    code = "PD-USGov"   # unrestricted federal record → U.S. Government public domain
    title = record.get("title", na_id)
    return MediaResult(
        source="nara", source_id=str(na_id), title=title, url=url,
        license=code, creator="U.S. National Archives", license_url="",
        rights_statement="Unrestricted — U.S. Government record (public domain)",
        attribution_text=f"{title} — U.S. National Archives ({code})",
        source_url=f"https://catalog.archives.gov/id/{na_id}",
        kind="photo",
    )


def download(url, dest):
    return _download(url, dest)
