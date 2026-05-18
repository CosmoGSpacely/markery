"""Unit tests for entity registry build and query."""

from __future__ import annotations

from markery.specialist.matchmaker.entities import (
    ENTITIES,
    VARIANTS,
    open_db,
    build,
    list_entities,
)


def test_open_db_creates_schema():
    conn = open_db(":memory:")
    tables = {r[0] for r in conn.execute("SHOW TABLES").fetchall()}
    assert "company_entity"      in tables
    assert "entity_name_variant" in tables
    conn.close()


def test_build_inserts_all_seed_data():
    conn = open_db(":memory:")
    conn.close()
    counts = build(":memory:")
    # Each call on a fresh in-memory DB inserts all seed rows
    # (build() opens its own connection, so we verify via a second open)
    # For :memory: we can only verify counts returned
    assert counts["entities"] == len(ENTITIES)
    assert counts["variants"] == len(VARIANTS)


def test_build_is_idempotent(tmp_path):
    path   = tmp_path / "entities.duckdb"
    first  = build(path)
    second = build(path)
    assert first["entities"]  == len(ENTITIES)
    assert second["entities"] == 0
    assert second["variants"] == 0


def test_list_entities_returns_all_ordered(tmp_path):
    path = tmp_path / "entities.duckdb"
    build(path)
    conn     = open_db(path)
    entities = list_entities(conn)
    conn.close()

    assert len(entities) == len(ENTITIES)
    ids = [e["entity_id"] for e in entities]
    assert ids == sorted(ids)


def test_list_entities_has_expected_fields(tmp_path):
    path = tmp_path / "entities.duckdb"
    build(path)
    conn     = open_db(path)
    entities = list_entities(conn)
    conn.close()

    first = entities[0]
    assert set(first.keys()) == {
        "entity_id", "canonical_name", "entity_type", "industry", "notes"
    }
    assert first["canonical_name"] == "Remington Rand"
    assert first["industry"] == "office-systems"
