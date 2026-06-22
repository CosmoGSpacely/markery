"""Public-domain / free-licensed media acquisition for project enrichment (P2).

Stores each admitted item under ``projects/<name>/library/media/<slug>/`` with the
binary plus a ``metadata.json`` carrying source, license, and attribution, and
appends a row to ``library/media/index.jsonl``. Admission policy is enforced by the
source adapters (see ``sources/commons.py``); this module refuses to register an
item whose license does not resolve to an admitted code.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from pathlib import Path
from typing import Optional

from markery.common.project import Project
from markery.specialist.librarian.sources import commons

_ADMITTED = {"PD", "PD-US-expired", "PD-USGov", "CC0", "CC-BY", "CC-BY-SA"}


def media_dir(project: str) -> Path:
    return Project(project).root / "library" / "media"


def _index_path(project: str) -> Path:
    return media_dir(project) / "index.jsonl"


def _slugify(name: str) -> str:
    name = re.sub(r"^File:", "", name)
    name = re.sub(r"\.[A-Za-z0-9]+$", "", name)        # drop extension
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:60] or "item"


def _ext_from_url(url: str) -> str:
    m = re.search(r"\.([A-Za-z0-9]{2,4})(?:\?|$)", url)
    return m.group(1).lower() if m else "bin"


def list_media(project: str) -> list[dict]:
    idx = _index_path(project)
    if not idx.exists():
        return []
    return [json.loads(line) for line in idx.read_text().splitlines() if line.strip()]


def acquire_commons(project: str, file_title: str, kind: str = "photo") -> Optional[dict]:
    """Acquire one Wikimedia Commons file into the project's media library.

    Returns the stored metadata dict, or None if the file's license is not
    admitted (caller should report the rejection).
    """
    result = commons.fetch(file_title)
    if result is None or result.license not in _ADMITTED:
        return None

    slug = _slugify(file_title)
    ext = _ext_from_url(result.url)
    item_dir = media_dir(project) / slug
    file_path = item_dir / f"{slug}.{ext}"
    commons.download(result.url, file_path)
    data = file_path.read_bytes()

    meta = {
        "slug": slug,
        "kind": kind,
        "source": "wikimedia_commons",
        "source_url": f"https://commons.wikimedia.org/wiki/{file_title.replace(' ', '_')}",
        "file_url": result.url,
        "file": file_path.name,
        "title": re.sub(r"\.[A-Za-z0-9]+$", "", re.sub(r"^File:", "", file_title)),
        "creator": result.creator,
        "license": result.license,
        "license_url": result.license_url,
        "rights_statement": result.rights_statement,
        "attribution_text": result.attribution_text,
        "acquired_at": date.today().isoformat(),
        "sha256": hashlib.sha256(data).hexdigest(),
        "format": ext,
        "bytes": len(data),
    }
    (item_dir / "metadata.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    idx = _index_path(project)
    existing = [m for m in list_media(project) if m.get("slug") != slug]
    with idx.open("w", encoding="utf-8") as fh:
        for m in existing + [meta]:
            fh.write(json.dumps(m, ensure_ascii=False) + "\n")
    return meta
