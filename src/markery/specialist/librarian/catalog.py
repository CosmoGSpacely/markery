"""The library card catalog (Phase 29) — one global, rights-curated item index.

`library/catalog.jsonl` is the union of every library ITEM, both kinds:
  - **works**  — acquired bibliographic items (text; excerpts are the durable part)
  - **media**  — public-domain / free-licensed photos, maps, drawings, clippings

Flat JSONL by deliberate choice (LIBRARY_REVIEW §9 / D073): the autonomous loops
load it into an in-memory dict once per run for O(1) dedup (by id, by source_url,
by sha256) and write it back with an **atomic rewrite** (temp file + rename),
last-row-wins per id. No DuckDB catalog until D073's trigger.

The per-item `metadata.json` under each `works/<slug>/` and `media/<slug>/` is the
source of truth; `rebuild()` regenerates the catalog from them.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from markery.common import config

# Item kinds.
WORK_KINDS = {"work"}
MEDIA_KINDS = {"photo", "map", "drawing", "clipping", "book", "media"}


def library_dir() -> Path:
    return config.ROOT / "library"


def catalog_path() -> Path:
    return library_dir() / "catalog.jsonl"


# ---------------------------------------------------------------------------
# Load / write
# ---------------------------------------------------------------------------

def load() -> dict[str, dict]:
    """Return the catalog as {id: item}, last-row-wins for duplicate ids."""
    path = catalog_path()
    items: dict[str, dict] = {}
    if not path.exists():
        return items
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            items[row["id"]] = row
    return items


def _write_atomic(items: dict[str, dict]) -> None:
    """Rewrite catalog.jsonl atomically (temp file + rename), sorted by id."""
    path = catalog_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".catalog-", suffix=".jsonl")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            for _id in sorted(items):
                fh.write(json.dumps(items[_id], ensure_ascii=False) + "\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def upsert(item: dict) -> None:
    """Add or replace one item (keyed by id); atomic rewrite, last-wins."""
    if "id" not in item:
        raise ValueError("catalog item requires an 'id'")
    items = load()
    items[item["id"]] = item
    _write_atomic(items)


# ---------------------------------------------------------------------------
# Dedup lookups (what the loops consult before acquiring)
# ---------------------------------------------------------------------------

def find_by_sha256(sha: str, items: dict[str, dict] | None = None) -> dict | None:
    for it in (items or load()).values():
        if sha and it.get("sha256") == sha:
            return it
    return None


def find_by_source_url(url: str, items: dict[str, dict] | None = None) -> dict | None:
    for it in (items or load()).values():
        if url and it.get("source_url") == url:
            return it
    return None


# ---------------------------------------------------------------------------
# Item builders (per-item metadata.json → catalog row)
# ---------------------------------------------------------------------------

def work_item(meta: dict) -> dict:
    """Catalog row for a text work from its works/<slug>/metadata.json."""
    src = meta.get("source", "")
    ident = meta.get("ia_identifier") or meta.get("gutenberg_id")
    source_url = None
    if meta.get("ia_identifier"):
        source_url = f"https://archive.org/details/{meta['ia_identifier']}"
    elif meta.get("gutenberg_id"):
        source_url = f"https://www.gutenberg.org/ebooks/{meta['gutenberg_id']}"
    return {
        "id": meta["slug"],
        "kind": "work",
        "title": meta.get("title", ""),
        "creator": meta.get("author", ""),
        "date": meta.get("year"),
        "source": src,
        "source_id": str(ident) if ident else None,
        "source_url": source_url,
        "acquired_at": meta.get("acquired_at"),
    }


def media_item(meta: dict) -> dict:
    """Catalog row for a media item from its media/<slug>/metadata.json."""
    return {
        "id": meta["slug"],
        "kind": meta.get("kind", "media"),
        "title": meta.get("title", ""),
        "creator": meta.get("creator", ""),
        "date": meta.get("date"),
        "source": meta.get("source", ""),
        "source_id": meta.get("source_id"),
        "source_url": meta.get("source_url"),
        "license": meta.get("license"),
        "license_url": meta.get("license_url"),
        "rights_statement": meta.get("rights_statement"),
        "attribution_text": meta.get("attribution_text"),
        "acquired_at": meta.get("acquired_at"),
        "sha256": meta.get("sha256"),
        "file": meta.get("file"),
        "format": meta.get("format"),
    }


def rebuild() -> dict[str, int]:
    """Regenerate catalog.jsonl from every works/ and media/ metadata.json.

    Returns {"works": n, "media": n}."""
    lib = library_dir()
    items: dict[str, dict] = {}
    n_works = n_media = 0
    works_dir = lib / "works"
    if works_dir.is_dir():
        for d in sorted(works_dir.iterdir()):
            mp = d / "metadata.json"
            if mp.is_file():
                items_row = work_item(json.loads(mp.read_text(encoding="utf-8")))
                items[items_row["id"]] = items_row
                n_works += 1
    media_root = lib / "media"
    if media_root.is_dir():
        for d in sorted(media_root.iterdir()):
            mp = d / "metadata.json"
            if mp.is_file():
                row = media_item(json.loads(mp.read_text(encoding="utf-8")))
                items[row["id"]] = row
                n_media += 1
    _write_atomic(items)
    return {"works": n_works, "media": n_media}
