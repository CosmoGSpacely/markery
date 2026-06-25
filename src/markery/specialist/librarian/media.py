"""Public-domain / free-licensed media acquisition into the GLOBAL library (Phase 29).

Acquisition is global (not per-project): each admitted item lands once under
``library/media/<slug>/`` (binary + ``metadata.json``) and is registered in the
global ``library/catalog.jsonl``. Projects later *reference* items via
``librarian use`` (see ``references`` / Phase 29 P2). One acquire → many project
references, no duplication.

Dedup (what the discovery loop relies on): before acquiring, the catalog is
checked by ``source_url`` and ``sha256`` so the same item is never fetched twice.
Admission policy is enforced by the source adapters; this module refuses any item
whose license does not resolve to an admitted code.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from pathlib import Path
from typing import Optional

from markery.common import config
from markery.specialist.librarian import catalog
from markery.specialist.librarian.sources import commons, loc, nara, dpla, ia_media

_ADMITTED = {"PD", "PD-US-expired", "PD-USGov", "CC0", "CC-BY", "CC-BY-SA"}

# MediaResult-returning PD source adapters (commons has its own CommonsResult path).
_ADAPTERS = {"loc": loc, "nara": nara, "dpla": dpla, "ia": ia_media}


def media_dir() -> Path:
    return config.ROOT / "library" / "media"


def _slugify(name: str) -> str:
    name = re.sub(r"^File:", "", name)
    name = re.sub(r"\.[A-Za-z0-9]+$", "", name)        # drop extension
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:60] or "item"


def _ext_from_url(url: str) -> str:
    m = re.search(r"\.([A-Za-z0-9]{2,4})(?:\?|$)", url)
    return m.group(1).lower() if m else "bin"


def list_media() -> list[dict]:
    """Return all media items from the global catalog (kind != work)."""
    return [it for it in catalog.load().values() if it.get("kind") not in catalog.WORK_KINDS]


def acquire_commons(file_title: str, kind: str = "photo") -> Optional[dict]:
    """Acquire one Wikimedia Commons file into the global library.

    Returns the stored metadata dict (the existing catalog row if already acquired
    — dedup by source_url), or None if the file's license is not admitted.
    """
    source_url = f"https://commons.wikimedia.org/wiki/{file_title.replace(' ', '_')}"

    existing = catalog.find_by_source_url(source_url)
    if existing is not None:
        return existing

    result = commons.fetch(file_title)
    if result is None or result.license not in _ADMITTED:
        return None

    slug = _slugify(file_title)
    ext = _ext_from_url(result.url)
    item_dir = media_dir() / slug
    file_path = item_dir / f"{slug}.{ext}"
    commons.download(result.url, file_path)
    data = file_path.read_bytes()
    sha = hashlib.sha256(data).hexdigest()

    meta = {
        "slug": slug,
        "kind": kind,
        "source": "wikimedia_commons",
        "source_id": file_title,
        "source_url": source_url,
        "file_url": result.url,
        "file": file_path.name,
        "title": re.sub(r"\.[A-Za-z0-9]+$", "", re.sub(r"^File:", "", file_title)),
        "creator": result.creator,
        "license": result.license,
        "license_url": result.license_url,
        "rights_statement": result.rights_statement,
        "attribution_text": result.attribution_text,
        "acquired_at": date.today().isoformat(),
        "sha256": sha,
        "format": ext,
        "bytes": len(data),
    }
    (item_dir / "metadata.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    catalog.upsert(catalog.media_item(meta))
    return meta


def _store_media_result(result, kind: str | None = None) -> dict:
    """Download a resolved MediaResult into the global library + catalog. Deduped."""
    existing = catalog.find_by_source_url(result.source_url)
    if existing is not None:
        return existing

    slug = _slugify(f"{result.source}-{result.title or result.source_id}")
    ext = _ext_from_url(result.url)
    item_dir = media_dir() / slug
    file_path = item_dir / f"{slug}.{ext}"
    _download_adapter = _ADAPTERS[result.source]
    _download_adapter.download(result.url, file_path)
    data = file_path.read_bytes()

    meta = {
        "slug": slug,
        "kind": kind or result.kind,
        "source": result.source,
        "source_id": result.source_id,
        "source_url": result.source_url,
        "file_url": result.url,
        "file": file_path.name,
        "title": result.title,
        "creator": result.creator,
        "license": result.license,
        "license_url": result.license_url,
        "rights_statement": result.rights_statement,
        "attribution_text": result.attribution_text,
        "date": result.date,
        "acquired_at": date.today().isoformat(),
        "sha256": hashlib.sha256(data).hexdigest(),
        "format": ext,
        "bytes": len(data),
    }
    (item_dir / "metadata.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    catalog.upsert(catalog.media_item(meta))
    return meta


def acquire(source: str, identifier: str, kind: str | None = None) -> Optional[dict]:
    """Acquire one item from any PD source into the global library.

    source ∈ {commons, loc, nara, dpla, ia}. Returns the stored metadata dict
    (existing row if already acquired — dedup by source_url), or None if the item
    is rejected (license not admitted) or not found. Adapters that need a missing
    key (e.g. DPLA) raise; the caller decides whether to skip."""
    if source == "commons":
        return acquire_commons(identifier, kind=kind or "photo")
    adapter = _ADAPTERS.get(source)
    if adapter is None:
        raise ValueError(f"Unknown media source '{source}'. "
                         f"Choose from: commons, {', '.join(_ADAPTERS)}")
    result = adapter.fetch(identifier)
    if result is None or result.license not in _ADMITTED:
        return None
    return _store_media_result(result, kind=kind)
