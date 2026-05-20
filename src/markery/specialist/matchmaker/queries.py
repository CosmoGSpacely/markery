"""Read-only query interface for the MATCHMAKER specialist.

Pure-read API over entities.duckdb. Other specialists and the orchestrator
should import from here rather than from entities.py or link.py when they
only need to read entity data.

Entry points:
    connect()                         Open entities.duckdb read-only.
    get_entity(conn, entity_id)       Look up one entity by primary key.
    find_entity(conn, canonical_name) Look up one entity by canonical name.
    list_entities(conn)               All entities ordered by entity_id.
    list_variants(conn, entity_id)    All name variants, optionally filtered.
    read_candidates(path)             Load candidates.jsonl as a list of dicts.
    read_confirmed(path)              Load confirmed.jsonl as a list of dicts.
    read_rejected(path)               Load rejected.jsonl as a set of key tuples.
    read_pipeline_state(path)         Load pipeline_state.json as a dict.
"""

from __future__ import annotations

import json
from pathlib import Path

import duckdb

from markery.common.config import DB


def connect(db_path: str | Path | None = None) -> duckdb.DuckDBPyConnection:
    """Open entities.duckdb in read-only mode."""
    return duckdb.connect(str(db_path or DB["entities"]), read_only=True)


def get_entity(
    conn: duckdb.DuckDBPyConnection,
    entity_id: int,
) -> dict | None:
    """Return one entity dict by primary key, or None if not found."""
    row = conn.execute(
        "SELECT entity_id, canonical_name, entity_type, industry "
        "FROM company_entity WHERE entity_id = ?",
        [entity_id],
    ).fetchone()
    if not row:
        return None
    return {
        "entity_id":      row[0],
        "canonical_name": row[1],
        "entity_type":    row[2],
        "industry":       row[3],
    }


def find_entity(
    conn: duckdb.DuckDBPyConnection,
    canonical_name: str,
) -> dict | None:
    """Case-insensitive lookup by canonical_name. Returns the first match or None."""
    row = conn.execute(
        "SELECT entity_id, canonical_name, entity_type, industry "
        "FROM company_entity WHERE LOWER(canonical_name) = LOWER(?)",
        [canonical_name],
    ).fetchone()
    if not row:
        return None
    return {
        "entity_id":      row[0],
        "canonical_name": row[1],
        "entity_type":    row[2],
        "industry":       row[3],
    }


def list_entities(conn: duckdb.DuckDBPyConnection) -> list[dict]:
    """Return all entities ordered by entity_id."""
    rows = conn.execute(
        "SELECT entity_id, canonical_name, entity_type, industry "
        "FROM company_entity ORDER BY entity_id"
    ).fetchall()
    return [
        {
            "entity_id":      r[0],
            "canonical_name": r[1],
            "entity_type":    r[2],
            "industry":       r[3],
        }
        for r in rows
    ]


def list_variants(
    conn: duckdb.DuckDBPyConnection,
    entity_id: int | None = None,
) -> list[dict]:
    """Return name variants, optionally filtered to one entity."""
    if entity_id is not None:
        rows = conn.execute(
            "SELECT variant_id, entity_id, variant_name, source "
            "FROM entity_name_variant WHERE entity_id = ? ORDER BY variant_id",
            [entity_id],
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT variant_id, entity_id, variant_name, source "
            "FROM entity_name_variant ORDER BY entity_id, variant_id"
        ).fetchall()
    return [
        {
            "variant_id":   r[0],
            "entity_id":    r[1],
            "variant_name": r[2],
            "source":       r[3],
        }
        for r in rows
    ]


def read_candidates(path: Path) -> list[dict]:
    """Load candidates.jsonl. Returns [] if the file does not exist."""
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def read_confirmed(path: Path) -> list[dict]:
    """Load confirmed.jsonl. Returns [] if the file does not exist."""
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def read_rejected(path: Path) -> set[tuple]:
    """Load rejected.jsonl as a set of (patent_no, trademark_serial) tuples."""
    if not path.exists():
        return set()
    pairs: set[tuple] = set()
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        pairs.add((row["patent_no"], str(row["trademark_serial"])))
    return pairs


def read_pipeline_state(path: Path) -> dict:
    """Load pipeline_state.json. Returns {} if the file does not exist."""
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}
