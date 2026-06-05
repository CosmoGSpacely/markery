"""Entity registry for MATCHMAKER specialist.

Owns entities.duckdb: company_entity and entity_name_variant tables.
Entity data lives in per-project CSV files (entities.csv, variants.csv).
Running `markery matchmaker build --data-dir <project-dir>` reads those files
and inserts any new rows.

Entry points:
    open_db(db_path)              Open entities.duckdb and ensure schema exists.
    build(data_dir, db_path)      Idempotent seed insert from CSV; returns counts.
    list_entities(conn)           Return all entities ordered by entity_id.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import duckdb

from markery.common.config import DB

DDL = """
CREATE TABLE IF NOT EXISTS company_entity (
    entity_id      INTEGER PRIMARY KEY,
    canonical_name VARCHAR NOT NULL,
    entity_type    VARCHAR,
    industry       VARCHAR
);

CREATE TABLE IF NOT EXISTS entity_name_variant (
    variant_id   INTEGER PRIMARY KEY,
    entity_id    INTEGER NOT NULL REFERENCES company_entity(entity_id),
    variant_name VARCHAR NOT NULL,
    source       VARCHAR NOT NULL
);
"""


def _migrate_drop_notes(conn: duckdb.DuckDBPyConnection) -> None:
    """One-time migration: remove the notes column from company_entity.

    The FK on entity_name_variant blocks ALTER TABLE DROP COLUMN, so we rebuild
    both tables: save rows, drop both, recreate without notes, re-insert.
    """
    try:
        cols = {r[0] for r in conn.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'company_entity'"
        ).fetchall()}
        if "notes" not in cols:
            return

        entities = conn.execute(
            "SELECT entity_id, canonical_name, entity_type, industry FROM company_entity"
        ).fetchall()
        variants = conn.execute(
            "SELECT variant_id, entity_id, variant_name, source FROM entity_name_variant"
        ).fetchall()

        conn.execute("DROP TABLE entity_name_variant")
        conn.execute("DROP TABLE company_entity")
        conn.execute(DDL)

        for row in entities:
            conn.execute(
                "INSERT INTO company_entity VALUES (?, ?, ?, ?)", list(row)
            )
        for row in variants:
            conn.execute(
                "INSERT INTO entity_name_variant VALUES (?, ?, ?, ?)", list(row)
            )
        conn.commit()
    except Exception:
        pass


def open_db(db_path: str | Path | None = None) -> duckdb.DuckDBPyConnection:
    """Open entities.duckdb and ensure schema exists."""
    path = str(db_path or DB["entities"])
    conn = duckdb.connect(path)
    # Migration must run before DDL: DuckDB 1.5.x registers REFERENCES clauses from
    # CREATE TABLE IF NOT EXISTS even when the table already exists, which would make
    # the subsequent DROP TABLE fail with a dependency error.
    _migrate_drop_notes(conn)
    conn.execute(DDL)
    return conn


def _read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def build(data_dir: str | Path, db_path: str | Path | None = None) -> dict[str, int]:
    """Insert entities and variants from CSV files in data_dir. Idempotent.

    Reads entities.csv (entity_id, canonical_name, entity_type, industry) and
    variants.csv (entity_id, variant_name, source). Skips existing rows.
    Returns {"entities": n_added, "variants": n_added}.
    """
    data_dir = Path(data_dir)
    entities = _read_csv(data_dir / "entities.csv")
    variants = _read_csv(data_dir / "variants.csv")

    conn = open_db(db_path)

    added_entities = 0
    for row in entities:
        eid = int(row["entity_id"])
        existing = conn.execute(
            "SELECT canonical_name FROM company_entity WHERE entity_id = ?", [eid]
        ).fetchone()
        if existing:
            if existing[0] != row["canonical_name"]:
                conn.close()
                raise ValueError(
                    f"entity_id {eid} is already registered as '{existing[0]}' — "
                    f"cannot overwrite with '{row['canonical_name']}'. "
                    f"Assign a different entity_id in {Path(data_dir) / 'entities.csv'}."
                )
            # Same name — idempotent skip
        else:
            conn.execute(
                "INSERT INTO company_entity (entity_id, canonical_name, entity_type, industry) "
                "VALUES (?, ?, ?, ?)",
                [eid, row["canonical_name"], row.get("entity_type"), row.get("industry")],
            )
            added_entities += 1

    _VALID_SOURCES = {"patent_assignee", "trademark_owner", "trademark_search"}
    for i, row in enumerate(variants, start=2):
        source = row.get("source", "")
        if source not in _VALID_SOURCES:
            conn.close()
            print(
                f"ERROR: variants.csv row {i}: source={source!r} is not in "
                f"{sorted(_VALID_SOURCES)}. "
                f"If variant_name contains a comma, quote the field.",
                file=sys.stderr,
            )
            sys.exit(1)

    added_variants = 0
    next_id = (
        conn.execute(
            "SELECT COALESCE(MAX(variant_id), 0) FROM entity_name_variant"
        ).fetchone()[0]
        + 1
    )
    for row in variants:
        eid = int(row["entity_id"])
        vname = row["variant_name"]
        source = row["source"]
        if not conn.execute(
            """SELECT 1 FROM entity_name_variant
               WHERE entity_id = ? AND variant_name = ? AND source = ?""",
            [eid, vname, source],
        ).fetchone():
            conn.execute(
                "INSERT INTO entity_name_variant VALUES (?, ?, ?, ?)",
                [next_id, eid, vname, source],
            )
            next_id += 1
            added_variants += 1

    conn.commit()
    conn.close()
    return {"entities": added_entities, "variants": added_variants}


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
