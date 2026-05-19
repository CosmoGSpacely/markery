"""Unit tests for trademark queries module."""

from __future__ import annotations

from markery.specialist.trademark.build import open_db
from markery.specialist.trademark.queries import (
    get_mark,
    has_image,
    has_case_status,
    get_goods_desc,
    get_missing_enrichment,
)


_CASE_FILE_DDL = """
CREATE TABLE IF NOT EXISTS case_file (
    serial_no       VARCHAR PRIMARY KEY,
    mark_id_char    VARCHAR,
    filing_dt       DATE,
    mark_draw_cd    VARCHAR,
    registration_no VARCHAR,
    cfh_status_cd   VARCHAR
)
"""

_STATEMENT_DDL = """
CREATE TABLE IF NOT EXISTS statement (
    serial_no         VARCHAR,
    statement_type_cd VARCHAR,
    statement_text    VARCHAR
)
"""


def _db():
    conn = open_db(":memory:")
    conn.execute(_CASE_FILE_DDL)
    conn.execute(_STATEMENT_DDL)
    return conn


def _insert_mark(conn, serial_no="71165547", mark_name="VI-DEX",
                 filing_dt="1927-01-15", status_cd="700"):
    conn.execute(
        "INSERT INTO case_file (serial_no, mark_id_char, filing_dt, cfh_status_cd) "
        "VALUES (?,?,?,?)",
        [serial_no, mark_name, filing_dt, status_cd],
    )


# ---------------------------------------------------------------------------
# get_mark
# ---------------------------------------------------------------------------

def test_get_mark_returns_none_for_missing():
    conn = _db()
    assert get_mark(conn, "99999999") is None
    conn.close()


def test_get_mark_returns_dict_for_found():
    conn = _db()
    _insert_mark(conn)
    result = get_mark(conn, "71165547")
    assert result is not None
    assert result["serial_no"] == "71165547"
    assert result["mark_name"] == "VI-DEX"
    assert result["status_cd"] == "700"
    conn.close()


def test_get_mark_serial_no_is_string():
    conn = _db()
    _insert_mark(conn)
    result = get_mark(conn, "71165547")
    assert isinstance(result["serial_no"], str)
    conn.close()


# ---------------------------------------------------------------------------
# has_image
# ---------------------------------------------------------------------------

def test_has_image_false_when_no_row():
    conn = _db()
    assert has_image(conn, "71165547") is False
    conn.close()


def test_has_image_false_when_null_data():
    conn = _db()
    conn.execute("INSERT INTO mark_images (serial_no) VALUES ('71165547')")
    assert has_image(conn, "71165547") is False
    conn.close()


def test_has_image_true_when_blob_present():
    conn = _db()
    conn.execute(
        "INSERT INTO mark_images (serial_no, image_data) VALUES (?,?)",
        ["71165547", b"\x89PNG\r\n"],
    )
    assert has_image(conn, "71165547") is True
    conn.close()


# ---------------------------------------------------------------------------
# has_case_status
# ---------------------------------------------------------------------------

def test_has_case_status_false_when_no_row():
    conn = _db()
    assert has_case_status(conn, "71165547") is False
    conn.close()


def test_has_case_status_true_when_row_exists():
    conn = _db()
    conn.execute(
        "INSERT INTO mark_case_status (serial_no, mark_text) VALUES (?,?)",
        ["71165547", "VI-DEX"],
    )
    assert has_case_status(conn, "71165547") is True
    conn.close()


# ---------------------------------------------------------------------------
# get_goods_desc
# ---------------------------------------------------------------------------

def test_get_goods_desc_none_when_missing():
    conn = _db()
    assert get_goods_desc(conn, "71165547") is None
    conn.close()


def test_get_goods_desc_from_statement():
    conn = _db()
    conn.execute(
        "INSERT INTO statement (serial_no, statement_type_cd, statement_text) VALUES (?,?,?)",
        ["71165547", "GS0001", "Card filing systems"],
    )
    assert get_goods_desc(conn, "71165547") == "Card filing systems"
    conn.close()


def test_get_goods_desc_falls_back_to_mark_case_status():
    conn = _db()
    conn.execute(
        "INSERT INTO mark_case_status (serial_no, goods_desc) VALUES (?,?)",
        ["71165547", "Filing equipment"],
    )
    assert get_goods_desc(conn, "71165547") == "Filing equipment"
    conn.close()


def test_get_goods_desc_prefers_statement_over_case_status():
    conn = _db()
    conn.execute(
        "INSERT INTO statement (serial_no, statement_type_cd, statement_text) VALUES (?,?,?)",
        ["71165547", "GS0001", "From statement table"],
    )
    conn.execute(
        "INSERT INTO mark_case_status (serial_no, goods_desc) VALUES (?,?)",
        ["71165547", "From case status"],
    )
    assert get_goods_desc(conn, "71165547") == "From statement table"
    conn.close()


def test_get_goods_desc_falls_back_when_statement_is_null():
    conn = _db()
    conn.execute(
        "INSERT INTO statement (serial_no, statement_type_cd, statement_text) VALUES (?,?,?)",
        ["71165547", "GS0001", None],
    )
    conn.execute(
        "INSERT INTO mark_case_status (serial_no, goods_desc) VALUES (?,?)",
        ["71165547", "Fallback goods"],
    )
    assert get_goods_desc(conn, "71165547") == "Fallback goods"
    conn.close()


# ---------------------------------------------------------------------------
# get_missing_enrichment
# ---------------------------------------------------------------------------

def test_get_missing_enrichment_empty_list():
    conn = _db()
    assert get_missing_enrichment(conn, []) == []
    conn.close()


def test_get_missing_enrichment_all_missing():
    conn = _db()
    result = get_missing_enrichment(conn, ["71111111", "71222222"])
    assert set(result) == {"71111111", "71222222"}
    conn.close()


def test_get_missing_enrichment_covered_by_statement():
    conn = _db()
    conn.execute(
        "INSERT INTO statement (serial_no, statement_type_cd, statement_text) VALUES (?,?,?)",
        ["71111111", "GS0001", "Filing systems"],
    )
    result = get_missing_enrichment(conn, ["71111111", "71222222"])
    assert "71111111" not in result
    assert "71222222" in result
    conn.close()


def test_get_missing_enrichment_covered_by_mark_case_status():
    conn = _db()
    conn.execute(
        "INSERT INTO mark_case_status (serial_no, goods_desc) VALUES (?,?)",
        ["71111111", "Office equipment"],
    )
    result = get_missing_enrichment(conn, ["71111111", "71222222"])
    assert "71111111" not in result
    assert "71222222" in result
    conn.close()


def test_get_missing_enrichment_all_covered():
    conn = _db()
    conn.execute(
        "INSERT INTO statement (serial_no, statement_type_cd, statement_text) VALUES (?,?,?)",
        ["71111111", "GS0001", "Card systems"],
    )
    conn.execute(
        "INSERT INTO mark_case_status (serial_no, goods_desc) VALUES (?,?)",
        ["71222222", "Filing equipment"],
    )
    result = get_missing_enrichment(conn, ["71111111", "71222222"])
    assert result == []
    conn.close()


def test_get_missing_enrichment_preserves_input_order():
    conn = _db()
    serials = ["71333333", "71444444", "71555555"]
    result = get_missing_enrichment(conn, serials)
    assert result == serials
    conn.close()
