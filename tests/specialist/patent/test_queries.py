"""Unit tests for patent queries module."""

from __future__ import annotations

from markery.specialist.patent.build import open_db, insert_patent
from markery.specialist.patent.queries import (
    get_patent,
    has_abstract,
    has_figure,
    get_cpc_classes,
    get_missing_signals,
)


_PATENT = {
    "patent_no":     "US1261167A",
    "title":         "Index",
    "app_dt":        "1917-10-25",
    "grant_dt":      "1918-04-02",
    "abstract":      "Phonetic indexing system for surnames.",
    "assignee_name": "Remington Typewriter Company",
    "cpc":           ["B42F17/00", "G06C99/00"],
    "inventors":     ["Russell Robert C"],
}


def _db():
    return open_db(":memory:")


# ---------------------------------------------------------------------------
# get_patent
# ---------------------------------------------------------------------------

def test_get_patent_returns_none_for_missing():
    conn = _db()
    assert get_patent(conn, "USNOPE") is None
    conn.close()


def test_get_patent_returns_dict_for_found():
    conn = _db()
    insert_patent(conn, _PATENT)
    result = get_patent(conn, "US1261167A")
    assert result is not None
    assert result["patent_no"]     == "US1261167A"
    assert result["title"]         == "Index"
    assert result["assignee_name"] == "Remington Typewriter Company"
    assert "abstract" in result
    conn.close()


def test_get_patent_includes_cpc_classes():
    conn = _db()
    insert_patent(conn, _PATENT)
    result = get_patent(conn, "US1261167A")
    assert set(result["cpc_classes"]) == {"B42F", "G06C"}
    conn.close()


def test_get_patent_includes_inventors():
    conn = _db()
    insert_patent(conn, _PATENT)
    result = get_patent(conn, "US1261167A")
    assert result["inventors"] == ["Russell Robert C"]
    conn.close()


# ---------------------------------------------------------------------------
# has_abstract
# ---------------------------------------------------------------------------

def test_has_abstract_false_for_missing():
    conn = _db()
    assert has_abstract(conn, "USNOPE") is False
    conn.close()


def test_has_abstract_true_when_present():
    conn = _db()
    insert_patent(conn, _PATENT)
    assert has_abstract(conn, "US1261167A") is True
    conn.close()


def test_has_abstract_false_when_null():
    conn = _db()
    no_abstract = dict(_PATENT, patent_no="US9999999A", abstract=None)
    insert_patent(conn, no_abstract)
    assert has_abstract(conn, "US9999999A") is False
    conn.close()


def test_has_abstract_false_when_empty_string():
    conn = _db()
    empty = dict(_PATENT, patent_no="US8888888A", abstract="")
    insert_patent(conn, empty)
    assert has_abstract(conn, "US8888888A") is False
    conn.close()


# ---------------------------------------------------------------------------
# has_figure
# ---------------------------------------------------------------------------

def test_has_figure_false_when_no_row():
    conn = _db()
    insert_patent(conn, _PATENT)
    assert has_figure(conn, "US1261167A") is False
    conn.close()


def test_has_figure_true_when_file_present():
    conn = _db()
    insert_patent(conn, _PATENT)
    conn.execute(
        "INSERT INTO patent_figures (patent_no, figure_no, file) VALUES (?,?,?)",
        ["US1261167A", 1, "patents/US1261167A.png"],
    )
    assert has_figure(conn, "US1261167A") is True
    conn.close()


def test_has_figure_false_when_null_file():
    conn = _db()
    insert_patent(conn, _PATENT)
    conn.execute(
        "INSERT INTO patent_figures (patent_no, figure_no, file) VALUES (?,?,?)",
        ["US1261167A", 1, None],
    )
    assert has_figure(conn, "US1261167A") is False
    conn.close()


# ---------------------------------------------------------------------------
# get_cpc_classes
# ---------------------------------------------------------------------------

def test_get_cpc_classes_returns_empty_for_missing():
    conn = _db()
    assert get_cpc_classes(conn, "USNOPE") == []
    conn.close()


def test_get_cpc_classes_returns_distinct_four_char_codes():
    conn = _db()
    insert_patent(conn, _PATENT)
    classes = get_cpc_classes(conn, "US1261167A")
    assert set(classes) == {"B42F", "G06C"}
    conn.close()


def test_get_cpc_classes_deduplicates():
    conn = _db()
    dupe = dict(_PATENT, patent_no="US7777777A", cpc=["B42F17/00", "B42F99/00"])
    insert_patent(conn, dupe)
    classes = get_cpc_classes(conn, "US7777777A")
    assert classes.count("B42F") == 1
    conn.close()


# ---------------------------------------------------------------------------
# get_missing_signals
# ---------------------------------------------------------------------------

def test_get_missing_signals_empty_list():
    conn = _db()
    assert get_missing_signals(conn, []) == []
    conn.close()


def test_get_missing_signals_returns_no_abstract_patents():
    conn = _db()
    insert_patent(conn, _PATENT)
    null_abstract = dict(_PATENT, patent_no="US2000000A", abstract=None)
    empty_abstract = dict(_PATENT, patent_no="US3000000A", abstract="")
    insert_patent(conn, null_abstract)
    insert_patent(conn, empty_abstract)

    missing = get_missing_signals(
        conn, ["US1261167A", "US2000000A", "US3000000A"]
    )
    assert set(missing) == {"US2000000A", "US3000000A"}
    assert "US1261167A" not in missing
    conn.close()


def test_get_missing_signals_all_present():
    conn = _db()
    insert_patent(conn, _PATENT)
    missing = get_missing_signals(conn, ["US1261167A"])
    assert missing == []
    conn.close()


def test_get_missing_signals_ignores_unknown_ids():
    conn = _db()
    missing = get_missing_signals(conn, ["USNOPE"])
    assert missing == []
    conn.close()
