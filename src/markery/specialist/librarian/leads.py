"""The discovery log (Phase 30 P3) — ``library/leads.jsonl``.

Every item the discovery loop *considers* is logged here as a provenance-tracked
research lead, whether or not it was acquired: free items the loop auto-acquired,
items queued for a human (ILL/purchase), and items judged irrelevant/dropped. The
log is the loop's memory (dedup by source+source_id) and the human's audit trail.

Flat JSONL, loop-safe like the catalog: in-memory load, dedup by (source,
source_id), atomic rewrite (temp + rename), last-write-wins per lead key.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from markery.common import config

STATUSES = {"logged", "scored", "acquired", "queued", "dropped"}


def leads_path() -> Path:
    return config.ROOT / "library" / "leads.jsonl"


def _key(source: str, source_id: str) -> str:
    return f"{source}:{source_id}"


def read_leads() -> list[dict]:
    p = leads_path()
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_atomic(leads: list[dict]) -> None:
    p = leads_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(p.parent), prefix=".leads-", suffix=".jsonl")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            for ld in leads:
                fh.write(json.dumps(ld, ensure_ascii=False) + "\n")
        os.replace(tmp, p)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def add_lead(source: str, source_id: str, *, title: str = "", url: str = "",
             kind: str = "", project: str = "", relevance=None,
             status: str = "logged", note: str = "") -> bool:
    """Append a lead (dedup by source+source_id). Returns True if newly added.

    A repeated (source, source_id) is a no-op — use update_lead to change status."""
    key = _key(source, source_id)
    leads = read_leads()
    if any(_key(l["source"], l["source_id"]) == key for l in leads):
        return False
    leads.append({
        "key": key, "source": source, "source_id": source_id,
        "title": title, "url": url, "kind": kind, "project": project,
        "relevance": relevance, "status": status, "note": note,
        "discovered_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    })
    _write_atomic(leads)
    return True


def update_lead(source: str, source_id: str, **fields) -> bool:
    """Update fields (e.g. status, relevance) of an existing lead. Returns success."""
    key = _key(source, source_id)
    leads = read_leads()
    found = False
    for l in leads:
        if _key(l["source"], l["source_id"]) == key:
            l.update(fields)
            found = True
            break
    if found:
        _write_atomic(leads)
    return found


def has_lead(source: str, source_id: str) -> bool:
    key = _key(source, source_id)
    return any(_key(l["source"], l["source_id"]) == key for l in read_leads())
