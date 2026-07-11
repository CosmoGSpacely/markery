"""Dedup merge vs. succession/M&A — kept strictly separate (Phase 35, hermetic)."""

from __future__ import annotations

import pytest

from markery.common.focus import LinkResolver, registry_link_maps
from markery.specialist.matchmaker import entities
from markery.specialist.matchmaker.entities import (
    add_relation,
    merge_entities,
    open_db,
)


def _seed(conn):
    """Two duplicate Westinghouse rows + one distinct successor (the Corporation)."""
    conn.execute(
        "INSERT INTO company_entity (entity_id, canonical_name, slug) VALUES "
        "(9, 'Westinghouse Electric and Manufacturing Company', 'westinghouse-mfg'),"
        "(9003, 'WESTINGHOUSE ELECTRIC & MANUFACTURING COMPANY', 'westinghouse-old'),"
        "(50, 'Westinghouse Electric Corporation', 'westinghouse-corp')"
    )
    conn.execute(
        "INSERT INTO entity_name_variant VALUES "
        "(1, 9,    'WESTINGHOUSE ELECTRIC & MFG CO',  'patent_assignee'),"
        "(2, 9003, 'WESTINGHOUSE ELECTRIC & MFG CO',  'patent_assignee'),"   # dup with 9
        "(3, 9003, 'WESTINGHOUSE ELECTRIC & MFG CORP', 'patent_assignee')"    # unique to 9003
    )
    conn.commit()


def test_merge_moves_variants_and_dedups(tmp_path):
    conn = open_db(tmp_path / "entities.duckdb")
    _seed(conn)
    report = merge_entities(conn, retired_id=9003, survivor_id=9)

    assert report["variants_moved"] == 1     # the unique CORP string
    assert report["variants_deduped"] == 1    # the MFG CO string already on 9

    # 9003 is gone; survivor 9 now carries both distinct variants.
    assert entities._entity_row(conn, 9003) is None
    names = {r[0] for r in conn.execute(
        "SELECT variant_name FROM entity_name_variant WHERE entity_id = 9").fetchall()}
    assert names == {"WESTINGHOUSE ELECTRIC & MFG CO", "WESTINGHOUSE ELECTRIC & MFG CORP"}
    conn.close()


def test_merge_records_alias_with_retired_slug(tmp_path):
    conn = open_db(tmp_path / "entities.duckdb")
    _seed(conn)
    merge_entities(conn, retired_id=9003, survivor_id=9)

    alias = conn.execute(
        "SELECT retired_id, retired_slug, survivor_id FROM entity_alias").fetchall()
    assert alias == [(9003, "westinghouse-old", 9)]
    conn.close()


def test_merge_retired_slug_redirects(tmp_path):
    conn = open_db(tmp_path / "entities.duckdb")
    _seed(conn)
    merge_entities(conn, retired_id=9003, survivor_id=9)

    url_for, aliases = registry_link_maps(conn)
    conn.close()
    r = LinkResolver(url_for=url_for, aliases=aliases)
    # Old slug still resolves — to the survivor's URL.
    assert r.resolve("entity", "westinghouse-old") == "focus/entity/westinghouse-mfg/"


def test_merge_dry_run_writes_nothing(tmp_path):
    conn = open_db(tmp_path / "entities.duckdb")
    _seed(conn)
    report = merge_entities(conn, retired_id=9003, survivor_id=9, dry_run=True)
    assert report["variants_moved"] == 1
    # Nothing changed.
    assert entities._entity_row(conn, 9003) is not None
    assert conn.execute("SELECT count(*) FROM entity_alias").fetchone()[0] == 0
    conn.close()


def test_merge_rejects_identical_and_unknown(tmp_path):
    conn = open_db(tmp_path / "entities.duckdb")
    _seed(conn)
    with pytest.raises(ValueError):
        merge_entities(conn, 9, 9)
    with pytest.raises(ValueError):
        merge_entities(conn, 9999, 9)
    conn.close()


def test_merge_repoints_prior_alias_chain(tmp_path):
    conn = open_db(tmp_path / "entities.duckdb")
    _seed(conn)
    # Something was already merged into 9003; merging 9003→9 must repoint it to 9.
    conn.execute("INSERT INTO entity_alias VALUES (9004, 'westinghouse-x', 9003)")
    conn.commit()
    merge_entities(conn, retired_id=9003, survivor_id=9)
    survivors = {r[0]: r[1] for r in conn.execute(
        "SELECT retired_id, survivor_id FROM entity_alias").fetchall()}
    assert survivors[9004] == 9   # repointed off the now-deleted 9003
    assert survivors[9003] == 9
    conn.close()


# --- succession / M&A — the OTHER operation, never a merge -------------------

def test_relate_keeps_both_entities_distinct(tmp_path):
    conn = open_db(tmp_path / "entities.duckdb")
    _seed(conn)
    # The 1945 succession: the Manufacturing Company was renamed to the Corporation.
    result = add_relation(conn, from_entity=9, to_entity=50,
                          kind="renamed_to", effective_date="1945-03-01")
    assert result["created"] is True

    # Neither entity is removed — both keep their identity.
    assert entities._entity_row(conn, 9) is not None
    assert entities._entity_row(conn, 50) is not None
    rel = conn.execute(
        "SELECT from_entity, to_entity, kind, effective_date FROM entity_relation").fetchall()
    assert rel == [(9, 50, "renamed_to", "1945-03-01")]
    conn.close()


def test_next_entity_id_never_reuses_retired(tmp_path):
    conn = open_db(tmp_path / "entities.duckdb")
    _seed(conn)
    merge_entities(conn, retired_id=9003, survivor_id=9)  # burns id 9003
    # A new registration must not reuse 9003 (it is aliased for redirects).
    nid = entities.next_entity_id(conn)
    assert nid > 9003
    conn.close()


def test_relate_idempotent_and_validates(tmp_path):
    conn = open_db(tmp_path / "entities.duckdb")
    _seed(conn)
    add_relation(conn, 9, 50, "renamed_to")
    again = add_relation(conn, 9, 50, "renamed_to")
    assert again["created"] is False
    assert conn.execute("SELECT count(*) FROM entity_relation").fetchone()[0] == 1

    with pytest.raises(ValueError):
        add_relation(conn, 9, 50, "not-a-kind")
    with pytest.raises(ValueError):
        add_relation(conn, 9, 9, "renamed_to")
    conn.close()
