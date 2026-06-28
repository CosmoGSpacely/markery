"""Internet Archive media (image) source adapter (Phase 30 P1 — closes D069).

Distinct from ``ia.py`` (which handles text/OCR). Uses archive.org's metadata API
(``/metadata/<id>``): admit when ``licenseurl`` / ``possible-copyright-status``
resolves to a PD/permissive code; pick the first image file; download from
``/download/<id>/<file>``.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Optional

from .common import MediaResult, normalize_license, download as _download

_META = "https://archive.org/metadata"
_SEARCH = "https://archive.org/advancedsearch.php"
_DL = "https://archive.org/download"
_UA = "markery/1.0 (https://github.com/CosmoGSpacely/markery)"
_IMAGE_EXT = (".jpg", ".jpeg", ".png", ".tif", ".tiff", ".gif")


def _get(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def search(query: str, max_results: int = 10) -> list[str]:
    """Return IA identifiers for image items matching the query."""
    qs = urllib.parse.urlencode({
        "q": f"({query}) AND mediatype:image",
        "fl[]": "identifier", "rows": max_results, "output": "json",
    })
    data = _get(f"{_SEARCH}?{qs}")
    docs = data.get("response", {}).get("docs", [])
    return [d["identifier"] for d in docs if d.get("identifier")]


def _first_image(files: list[dict]) -> str:
    # Prefer original (non-derivative) images.
    for f in files:
        name = (f.get("name") or "")
        if name.lower().endswith(_IMAGE_EXT) and f.get("source") == "original":
            return name
    for f in files:
        name = (f.get("name") or "")
        if name.lower().endswith(_IMAGE_EXT):
            return name
    return ""


def fetch(identifier: str, fair_use: bool = False) -> Optional[MediaResult]:
    """Fetch IA item metadata; admit if rights resolve to a PD/permissive code
    (strict); under fair_use, non-admitted items carry an honest rights tag."""
    data = _get(f"{_META}/{identifier}")
    meta = data.get("metadata", {})
    if not meta:
        return None
    rights = " ".join(
        str(meta.get(k, "")) for k in ("licenseurl", "possible-copyright-status", "rights")
    )
    code = normalize_license(rights, url=str(meta.get("licenseurl", "")), fair_use=fair_use)
    if code is None:
        return None
    fname = _first_image(data.get("files", []))
    if not fname:
        return None
    title = meta.get("title", identifier)
    if isinstance(title, list):
        title = title[0] if title else identifier
    creator = meta.get("creator", "Internet Archive")
    if isinstance(creator, list):
        creator = creator[0] if creator else "Internet Archive"
    return MediaResult(
        source="ia", source_id=identifier, title=title,
        url=f"{_DL}/{identifier}/{urllib.parse.quote(fname)}",
        license=code, creator=creator,
        license_url=str(meta.get("licenseurl", "")),
        rights_statement=str(meta.get("possible-copyright-status", "") or code),
        attribution_text=f"{title} — via Internet Archive ({code})",
        source_url=f"https://archive.org/details/{identifier}",
        kind="photo",
    )


def download(url, dest):
    return _download(url, dest)
