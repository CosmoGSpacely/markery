"""Keyword index and search for the LIBRARIAN specialist.

index_works()  — parses excerpts.md files; writes library/index.jsonl (incremental or full)
search_index() — keyword mode: case-insensitive substring match across passage/section/context
list_works()   — one line per work with excerpt count
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from markery.common.config import ROOT

_LIBRARY = ROOT / "library"
_INDEX_PATH = _LIBRARY / "index.jsonl"


# ---------------------------------------------------------------------------
# excerpts.md parser
# ---------------------------------------------------------------------------

def _load_meta(work_dir: Path) -> dict:
    meta_path = work_dir / "metadata.json"
    if not meta_path.exists():
        return {}
    return json.loads(meta_path.read_text(encoding="utf-8"))


def _parse_excerpts(work_dir: Path) -> list[dict]:
    """Parse library/works/<slug>/excerpts.md into a list of passage dicts."""
    excerpts_path = work_dir / "excerpts.md"
    if not excerpts_path.exists():
        return []

    meta = _load_meta(work_dir)
    slug = work_dir.name
    author = meta.get("author", "")
    title = meta.get("title", slug)
    year = meta.get("year")
    indexed_at = datetime.now(timezone.utc).isoformat()

    text = excerpts_path.read_text(encoding="utf-8")
    records: list[dict] = []

    # Split on ### headings; each block is one passage candidate
    blocks = re.split(r"\n(?=### )", text)
    for block in blocks:
        if not block.startswith("###"):
            continue
        block = block.strip()

        # Extract heading (first line)
        heading_m = re.match(r"### (.+)", block)
        if not heading_m:
            continue
        section = heading_m.group(1).strip()

        # Collect all blockquote lines (lines starting with >)
        bq_lines = re.findall(r"^> (.+)", block, re.MULTILINE)
        if not bq_lines:
            continue

        raw_quote = " ".join(bq_lines).strip()

        # Extract page reference: last (...) group in the raw quote block
        page_m = re.search(r"\(([^)]+)\)\s*$", raw_quote)
        if page_m:
            page = page_m.group(1).strip()
            # Remove page ref from quote text
            raw_quote = raw_quote[: page_m.start()].strip()
        else:
            page = "?"

        # Strip surrounding quotes from passage text
        passage = raw_quote.strip('"').strip("'").strip()

        if len(passage) < 20:
            continue

        # Context note: line(s) following "Context note:" or "Context:"
        context_m = re.search(
            r"Context\s+(?:note\s*)?:\s*(.+?)(?=\n### |\Z)",
            block,
            re.DOTALL | re.IGNORECASE,
        )
        context = context_m.group(1).strip() if context_m else ""
        # Collapse internal newlines to spaces for index storage
        context = re.sub(r"\s+", " ", context)

        records.append({
            "work_slug": slug,
            "author": author,
            "title": title,
            "year": year,
            "section": section,
            "passage": passage,
            "page": page,
            "context": context,
            "indexed_at": indexed_at,
        })

    return records


# ---------------------------------------------------------------------------
# index.jsonl I/O
# ---------------------------------------------------------------------------

def _read_index() -> list[dict]:
    if not _INDEX_PATH.exists():
        return []
    return [json.loads(ln) for ln in _INDEX_PATH.read_text(encoding="utf-8").splitlines() if ln.strip()]


def _write_index(records: list[dict]) -> None:
    _LIBRARY.mkdir(parents=True, exist_ok=True)
    _INDEX_PATH.write_text(
        "\n".join(json.dumps(r) for r in records) + ("\n" if records else ""),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Public: index
# ---------------------------------------------------------------------------

def index_works(rebuild: bool = False) -> tuple[int, int]:
    """Parse excerpts.md files and write library/index.jsonl.

    Returns (indexed_count, skipped_count).
    In incremental mode, works whose excerpts.md is older than the last
    index entry for that slug are skipped.
    """
    works_dir = _LIBRARY / "works"
    if not works_dir.exists():
        print("No library/works/ directory found.", file=sys.stderr)
        return 0, 0

    # Load existing index to determine what's fresh
    existing: list[dict] = [] if rebuild else _read_index()

    # Build a map: slug → latest indexed_at ISO string
    latest_indexed: dict[str, str] = {}
    for rec in existing:
        slug = rec.get("work_slug", "")
        ts = rec.get("indexed_at", "")
        if slug and ts > latest_indexed.get(slug, ""):
            latest_indexed[slug] = ts

    new_records: list[dict] = []
    indexed_count = 0
    skipped_count = 0

    for work_dir in sorted(works_dir.iterdir()):
        if not work_dir.is_dir():
            continue
        excerpts_path = work_dir / "excerpts.md"
        if not excerpts_path.exists():
            continue

        slug = work_dir.name

        if not rebuild and slug in latest_indexed:
            # Compare excerpts.md mtime against last indexed timestamp
            mtime_iso = datetime.fromtimestamp(
                excerpts_path.stat().st_mtime, tz=timezone.utc
            ).isoformat()
            if mtime_iso <= latest_indexed[slug]:
                # Carry forward existing records for this slug
                for rec in existing:
                    if rec.get("work_slug") == slug:
                        new_records.append(rec)
                skipped_count += 1
                continue

        parsed = _parse_excerpts(work_dir)
        new_records.extend(parsed)
        indexed_count += 1

    # For skipped slugs already carried above; for rebuilt ones they're in new_records.
    # Re-add any existing records for slugs not visited (no excerpts.md any more)
    if not rebuild:
        visited = {r["work_slug"] for r in new_records}
        for rec in existing:
            if rec.get("work_slug") not in visited:
                new_records.append(rec)

    _write_index(new_records)
    return indexed_count, skipped_count


# ---------------------------------------------------------------------------
# Public: search (keyword mode)
# ---------------------------------------------------------------------------

def search_keyword(query: str, top: int = 10) -> list[dict]:
    """Case-insensitive substring match across passage + section + context."""
    records = _read_index()
    if not records:
        return []

    query_lower = query.lower()
    # Multi-word: each word must match somewhere in the searchable text
    terms = query_lower.split()

    scored: list[tuple[int, dict]] = []
    for rec in records:
        searchable = " ".join([
            rec.get("passage", ""),
            rec.get("section", ""),
            rec.get("context", ""),
        ]).lower()
        hits = sum(1 for t in terms if t in searchable)
        if hits == len(terms):  # all terms must be present
            scored.append((hits, rec))

    scored.sort(key=lambda x: -x[0])
    return [r for _, r in scored[:top]]


# ---------------------------------------------------------------------------
# Public: list
# ---------------------------------------------------------------------------

def list_works(verbose: bool = False) -> list[dict]:
    """Return one summary dict per work in library/works/."""
    works_dir = _LIBRARY / "works"
    if not works_dir.exists():
        return []

    # Count passages per slug from index.jsonl
    records = _read_index()
    excerpt_counts: dict[str, int] = {}
    for rec in records:
        slug = rec.get("work_slug", "")
        excerpt_counts[slug] = excerpt_counts.get(slug, 0) + 1

    summaries = []
    for work_dir in sorted(works_dir.iterdir()):
        if not work_dir.is_dir():
            continue
        meta = _load_meta(work_dir)
        slug = work_dir.name
        has_raw = (work_dir / "raw_text.txt").exists()
        has_excerpts = (work_dir / "excerpts.md").exists()
        summaries.append({
            "slug": slug,
            "author": meta.get("author", "?"),
            "title": meta.get("title", slug),
            "year": meta.get("year"),
            "source": meta.get("source", "?"),
            "excerpt_count": excerpt_counts.get(slug, 0),
            "has_raw_text": has_raw,
            "has_excerpts": has_excerpts,
        })
    return summaries
