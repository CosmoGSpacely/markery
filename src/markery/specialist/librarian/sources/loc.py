"""Library of Congress media source adapter (Phase 30 P1 — closes D069).

loc.gov serves JSON with ``?fo=json``. Item records carry a ``rights`` /
``rights_advisory`` field (free text, commonly "No known restrictions on
publication.") and image URLs under ``image_url`` / ``resources``. We admit only
items whose rights resolve to a public-domain / permissive code.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Optional

from .common import MediaResult, normalize_license, download as _download

_BASE = "https://www.loc.gov"
_UA = "markery/1.0 (https://github.com/CosmoGSpacely/markery)"


def _api_get(url: str) -> dict:
    """GET a loc.gov JSON URL. Isolated so tests can monkeypatch it."""
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def search(query: str, max_results: int = 10) -> list[str]:
    """Return LoC item ids (the slug after /item/) matching the query."""
    url = (f"{_BASE}/search/?q={urllib.parse.quote(query)}"
           f"&fo=json&c={max_results}&fa=online-format:image")
    data = _api_get(url)
    ids: list[str] = []
    for r in data.get("results", [])[:max_results]:
        ident = r.get("id", "")
        # id is typically a full URL ending /item/<slug>/
        m = ident.rstrip("/").rsplit("/item/", 1)
        ids.append(m[1] if len(m) == 2 else ident)
    return ids


def _first_image_url(item: dict) -> str:
    for key in ("image_url", "resources"):
        v = item.get(key)
        if isinstance(v, list) and v:
            first = v[0]
            if isinstance(first, str):
                return first
            if isinstance(first, dict):
                return first.get("image") or first.get("url") or ""
    return ""


def fetch(item_id: str, fair_use: bool = False) -> Optional[MediaResult]:
    """Fetch one LoC item by id and resolve its rights. None if not admitted
    (strict); under fair_use, non-admitted items carry an honest rights tag."""
    url = f"{_BASE}/item/{item_id}/?fo=json"
    data = _api_get(url)
    item = data.get("item", {})
    if not item:
        return None
    rights = item.get("rights") or ""
    advisory = item.get("rights_advisory") or ""
    advisory = " ".join(advisory) if isinstance(advisory, list) else advisory
    code = normalize_license(f"{rights} {advisory}", fair_use=fair_use)
    if code is None:
        return None
    image_url = _first_image_url(data) or _first_image_url(item)
    if not image_url:
        return None
    creator = ""
    contribs = item.get("contributor_names") or item.get("contributors") or []
    if isinstance(contribs, list) and contribs:
        creator = contribs[0] if isinstance(contribs[0], str) else ""
    title = item.get("title", item_id)
    return MediaResult(
        source="loc", source_id=item_id, title=title, url=image_url,
        license=code, creator=creator or "Library of Congress",
        license_url="", rights_statement=(rights or advisory or code),
        attribution_text=f"{title} — Library of Congress ({code})",
        source_url=f"{_BASE}/item/{item_id}/",
        kind="photo",
    )


def download(url, dest):
    return _download(url, dest)
