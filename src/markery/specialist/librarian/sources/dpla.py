"""Digital Public Library of America (DPLA) media source adapter (Phase 30 P1).

api.dp.la aggregates US digital collections. Records carry a ``rights`` field
(often a rightsstatements.org URI or a CC URL) and ``object`` (a media URL).
Requires an API key (env ``DPLA_API_KEY``); the adapter degrades gracefully —
``search``/``fetch`` raise ``DPLAKeyMissing`` which callers treat as "skip".
"""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from typing import Optional

from .common import MediaResult, normalize_license, download as _download

_BASE = "https://api.dp.la/v2"
_UA = "markery/1.0 (https://github.com/CosmoGSpacely/markery)"


class DPLAKeyMissing(RuntimeError):
    """Raised when DPLA_API_KEY is not configured (caller should skip DPLA)."""


def _key() -> str:
    key = os.environ.get("DPLA_API_KEY", "").strip()
    if not key:
        raise DPLAKeyMissing(
            "DPLA_API_KEY not set — request one at https://pro.dp.la/developers/api-codex "
            "(the discovery loop skips DPLA when absent).")
    return key


def _api_get(path: str, params: dict) -> dict:
    qs = urllib.parse.urlencode({**params, "api_key": _key()})
    req = urllib.request.Request(f"{_BASE}{path}?{qs}", headers={"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def search(query: str, max_results: int = 10) -> list[str]:
    """Return DPLA item ids matching the query (image type)."""
    data = _api_get("/items", {
        "q": query, "page_size": max_results, "sourceResource.type": "image",
    })
    return [doc.get("id", "") for doc in data.get("docs", [])[:max_results] if doc.get("id")]


def _rights_of(doc: dict) -> str:
    sr = doc.get("sourceResource", {})
    rights = sr.get("rights") or doc.get("rights") or ""
    if isinstance(rights, list):
        rights = " ".join(rights)
    return rights


def fetch(item_id: str) -> Optional[MediaResult]:
    """Fetch one DPLA item; admit if its rights resolve to a PD/permissive code."""
    data = _api_get(f"/items/{item_id}", {})
    docs = data.get("docs", [])
    if not docs:
        return None
    doc = docs[0]
    rights = _rights_of(doc)
    code = normalize_license(rights)
    if code is None:
        return None
    url = doc.get("object") or ""   # DPLA "object" is the media/thumbnail URL
    if not url:
        return None
    sr = doc.get("sourceResource", {})
    title = sr.get("title", item_id)
    if isinstance(title, list):
        title = title[0] if title else item_id
    provider = (doc.get("provider", {}) or {}).get("name", "DPLA")
    return MediaResult(
        source="dpla", source_id=item_id, title=title, url=url,
        license=code, creator=provider, license_url=rights if rights.startswith("http") else "",
        rights_statement=rights or code,
        attribution_text=f"{title} — via DPLA / {provider} ({code})",
        source_url=doc.get("isShownAt", f"https://dp.la/item/{item_id}"),
        kind="photo",
    )


def download(url, dest):
    return _download(url, dest)
