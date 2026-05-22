"""Tests for specialist build modules: patent, trademark, publisher."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest


# ---------------------------------------------------------------------------
# patent/build.py
# ---------------------------------------------------------------------------

def _pat_conn():
    from markery.specialist.patent.build import open_db
    return open_db(":memory:")


_PATENT = {
    "patent_no":     "US1261167A",
    "title":         "Index",
    "app_dt":        "1917-10-25",
    "grant_dt":      "1918-04-02",
    "abstract":      "A method for indexing by phonetic code.",
    "assignee_name": "Odell Associates",
    "assignee_city": "New York",
    "assignee_state": "NY",
    "inventors":     ["Robert C. Russell"],
    "cpc":           ["G06F"],
}


def test_patent_open_db_creates_schema():
    conn = _pat_conn()
    tables = {r[0] for r in conn.execute("SHOW TABLES").fetchall()}
    assert "patents" in tables
    assert "patent_inventors" in tables
    assert "patent_classes" in tables
    conn.close()


def test_insert_patent_returns_true_on_new():
    from markery.specialist.patent.build import insert_patent
    conn = _pat_conn()
    result = insert_patent(conn, _PATENT)
    assert result is True
    conn.close()


def test_insert_patent_returns_false_on_duplicate():
    from markery.specialist.patent.build import insert_patent
    conn = _pat_conn()
    insert_patent(conn, _PATENT)
    result = insert_patent(conn, _PATENT)
    assert result is False
    conn.close()


def test_insert_patent_stores_inventors():
    from markery.specialist.patent.build import insert_patent
    conn = _pat_conn()
    insert_patent(conn, _PATENT)
    rows = conn.execute(
        "SELECT inventor_name FROM patent_inventors WHERE patent_no = ?",
        [_PATENT["patent_no"]]
    ).fetchall()
    names = [r[0] for r in rows]
    assert "Robert C. Russell" in names
    conn.close()


def test_insert_patent_stores_cpc_class():
    from markery.specialist.patent.build import insert_patent
    conn = _pat_conn()
    insert_patent(conn, _PATENT)
    rows = conn.execute(
        "SELECT cpc_class FROM patent_classes WHERE patent_no = ?",
        [_PATENT["patent_no"]]
    ).fetchall()
    classes = [r[0] for r in rows]
    assert "G06F" in classes
    conn.close()


def test_load_seed_skips_existing():
    from markery.specialist.patent.build import insert_patent, load_seed
    conn = _pat_conn()
    insert_patent(conn, _PATENT)
    added = load_seed(conn, [_PATENT])
    assert added == 0
    conn.close()


def test_load_seed_counts_new():
    from markery.specialist.patent.build import load_seed
    conn = _pat_conn()
    added = load_seed(conn, [_PATENT])
    assert added == 1
    conn.close()


# ---------------------------------------------------------------------------
# patent/signals.py — pure helper functions
# ---------------------------------------------------------------------------

def test_tokens_filters_stopwords():
    from markery.specialist.patent.signals import _tokens
    result = _tokens("a method for filing and indexing records")
    assert "method" in result
    assert "filing" in result
    assert "and" not in result
    assert "for" not in result


def test_tokens_empty_input():
    from markery.specialist.patent.signals import _tokens
    assert _tokens(None) == set()
    assert _tokens("") == set()


def test_jaccard_identical():
    from markery.specialist.patent.signals import _jaccard
    s = {"file", "index", "system"}
    assert _jaccard(s, s) == 1.0


def test_jaccard_disjoint():
    from markery.specialist.patent.signals import _jaccard
    assert _jaccard({"file"}, {"index"}) == 0.0


def test_jaccard_empty():
    from markery.specialist.patent.signals import _jaccard
    assert _jaccard(set(), {"index"}) == 0.0


def test_name_hit_returns_true_when_word_present():
    from markery.specialist.patent.signals import _name_hit
    assert _name_hit("A method for filing index cards", "SOUNDEX") is False
    assert _name_hit("The SOUNDEX method for indexing", "SOUNDEX") is True


def test_enrich_candidates_enriches_in_place(tmp_path):
    from markery.specialist.patent.build import open_db as pat_open_db, insert_patent
    from markery.specialist.trademark.build import open_db as tm_open_db
    from markery.specialist.patent.signals import enrich_candidates

    pat_path = tmp_path / "patents.duckdb"
    tm_path  = tmp_path / "trademarks.duckdb"

    pat_conn = pat_open_db(pat_path)
    insert_patent(pat_conn, {
        **_PATENT,
        "abstract": "A filing system for card index records.",
    })
    pat_conn.close()

    tm_conn = tm_open_db(tm_path)
    # Create minimal statement table (normally populated by trademark build from CSV)
    tm_conn.execute(
        "CREATE TABLE IF NOT EXISTS statement "
        "(serial_no BIGINT, statement_type_cd VARCHAR, statement_text VARCHAR)"
    )
    tm_conn.execute(
        "INSERT INTO extended_marks (serial_no, mark_text, goods_desc) VALUES (?,?,?)",
        [71246709, "VI-DEX", "Card filing systems and index card holders"],
    )
    tm_conn.close()

    candidates_path = tmp_path / "candidates.jsonl"
    candidates_path.write_text(json.dumps({
        "patent_no": "US1261167A",
        "trademark_serial": 71246709,
        "trademark": "VI-DEX",
        "score": 0.8,
    }) + "\n")

    n = enrich_candidates(candidates_path, patents_db=pat_path, trademarks_db=tm_path)
    assert n == 1

    result = json.loads(candidates_path.read_text().splitlines()[0])
    assert "title_name_hit" in result
    assert "goods_title_overlap" in result


def test_enrich_candidates_returns_zero_for_missing_file(tmp_path):
    from markery.specialist.patent.signals import enrich_candidates
    n = enrich_candidates(tmp_path / "nonexistent.jsonl")
    assert n == 0


# ---------------------------------------------------------------------------
# trademark/build.py
# ---------------------------------------------------------------------------

def _tm_conn():
    from markery.specialist.trademark.build import open_db
    return open_db(":memory:")


def test_trademark_open_db_creates_schema():
    conn = _tm_conn()
    tables = {r[0] for r in conn.execute("SHOW TABLES").fetchall()}
    assert "extended_marks" in tables
    assert "mark_images"     in tables
    conn.close()


def test_trademark_open_db_extended_marks_has_expected_columns():
    conn = _tm_conn()
    cols = {r[0] for r in conn.execute("DESCRIBE extended_marks").fetchall()}
    assert "serial_no"  in cols
    assert "mark_text"  in cols
    assert "goods_desc" in cols
    conn.close()


def test_trademark_build_raises_for_missing_csv_dir(tmp_path):
    from markery.specialist.trademark.build import build
    with pytest.raises(FileNotFoundError, match="CSV directory"):
        build(csv_dir=tmp_path / "nonexistent", db_path=":memory:")


# ---------------------------------------------------------------------------
# publisher/build.py — structural helpers
# ---------------------------------------------------------------------------

def test_collect_theme_slugs_finds_theme_files(tmp_path):
    from markery.specialist.publisher.build import _collect_theme_slugs
    from markery.common.project import Project
    import markery.common.project as proj_mod

    proj_root = tmp_path / "projects" / "test"
    content   = proj_root / "content"
    content.mkdir(parents=True)
    (content / "theme-card-index.md").write_text("# Theme")
    (content / "theme-filing-systems.md").write_text("# Theme")
    (content / "regular.md").write_text("not a theme")

    with patch.object(proj_mod, "ROOT", tmp_path):
        proj = Project("test")
        slugs = _collect_theme_slugs(proj)

    assert "card-index" in slugs
    assert "filing-systems" in slugs
    assert "regular" not in slugs
