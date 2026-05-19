"""Unit tests for entity registry build and query."""

from __future__ import annotations

from pathlib import Path

from markery.specialist.matchmaker.entities import (
    open_db,
    build,
    list_entities,
)


def _write_csvs(data_dir: Path, entities: list[dict], variants: list[dict]) -> None:
    import csv
    with (data_dir / "entities.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["entity_id", "canonical_name", "entity_type", "industry"])
        w.writeheader()
        w.writerows(entities)
    with (data_dir / "variants.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["entity_id", "variant_name", "source"])
        w.writeheader()
        w.writerows(variants)


_ENTITIES = [
    {"entity_id": 1, "canonical_name": "Remington Rand", "entity_type": "manufacturer", "industry": "office-systems"},
    {"entity_id": 2, "canonical_name": "Wilson Jones",   "entity_type": "manufacturer", "industry": "office-systems"},
]

_VARIANTS = [
    {"entity_id": 1, "variant_name": "Remington Typewriter Company", "source": "patent_assignee"},
    {"entity_id": 1, "variant_name": "REMINGTON RAND INC",           "source": "patent_assignee"},
    {"entity_id": 2, "variant_name": "WILSON JONES CO",              "source": "patent_assignee"},
]


def test_open_db_creates_schema():
    conn = open_db(":memory:")
    tables = {r[0] for r in conn.execute("SHOW TABLES").fetchall()}
    assert "company_entity"      in tables
    assert "entity_name_variant" in tables
    conn.close()


def test_open_db_schema_has_no_notes_column():
    conn = open_db(":memory:")
    cols = {r[0] for r in conn.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = 'company_entity'"
    ).fetchall()}
    assert "notes" not in cols
    conn.close()


def test_build_inserts_all_rows(tmp_path):
    _write_csvs(tmp_path, _ENTITIES, _VARIANTS)
    counts = build(tmp_path, tmp_path / "entities.duckdb")
    assert counts["entities"] == len(_ENTITIES)
    assert counts["variants"] == len(_VARIANTS)


def test_build_is_idempotent(tmp_path):
    _write_csvs(tmp_path, _ENTITIES, _VARIANTS)
    db_path = tmp_path / "entities.duckdb"
    first  = build(tmp_path, db_path)
    second = build(tmp_path, db_path)
    assert first["entities"]  == len(_ENTITIES)
    assert second["entities"] == 0
    assert second["variants"] == 0


def test_list_entities_returns_all_ordered(tmp_path):
    _write_csvs(tmp_path, _ENTITIES, _VARIANTS)
    db_path = tmp_path / "entities.duckdb"
    build(tmp_path, db_path)
    conn     = open_db(db_path)
    entities = list_entities(conn)
    conn.close()

    assert len(entities) == len(_ENTITIES)
    ids = [e["entity_id"] for e in entities]
    assert ids == sorted(ids)


def test_list_entities_has_expected_fields(tmp_path):
    _write_csvs(tmp_path, _ENTITIES, _VARIANTS)
    db_path = tmp_path / "entities.duckdb"
    build(tmp_path, db_path)
    conn     = open_db(db_path)
    entities = list_entities(conn)
    conn.close()

    first = entities[0]
    assert set(first.keys()) == {"entity_id", "canonical_name", "entity_type", "industry"}
    assert first["canonical_name"] == "Remington Rand"
    assert first["industry"] == "office-systems"


def test_migrate_drops_notes_column(tmp_path):
    """open_db() should drop a legacy notes column if present."""
    db_path = str(tmp_path / "entities.duckdb")
    import duckdb
    conn = duckdb.connect(db_path)
    conn.execute("""
        CREATE TABLE company_entity (
            entity_id      INTEGER PRIMARY KEY,
            canonical_name VARCHAR NOT NULL,
            entity_type    VARCHAR,
            industry       VARCHAR,
            notes          VARCHAR
        )
    """)
    conn.execute("""
        CREATE TABLE entity_name_variant (
            variant_id   INTEGER PRIMARY KEY,
            entity_id    INTEGER NOT NULL,
            variant_name VARCHAR NOT NULL,
            source       VARCHAR NOT NULL
        )
    """)
    conn.close()

    conn = open_db(db_path)
    cols = {r[0] for r in conn.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = 'company_entity'"
    ).fetchall()}
    conn.close()
    assert "notes" not in cols
