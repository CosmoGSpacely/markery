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


def test_has_image_true_when_file_present():
    conn = _db()
    conn.execute(
        "INSERT INTO mark_images (serial_no, file) VALUES (?,?)",
        ["71165547", "marks/71165547.png"],
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
        "INSERT INTO extended_marks (serial_no, mark_text) VALUES (?,?)",
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


def test_get_goods_desc_falls_back_to_extended_marks():
    conn = _db()
    conn.execute(
        "INSERT INTO extended_marks (serial_no, goods_desc) VALUES (?,?)",
        ["71165547", "Filing equipment"],
    )
    assert get_goods_desc(conn, "71165547") == "Filing equipment"
    conn.close()


def test_get_goods_desc_prefers_statement_over_extended_marks():
    conn = _db()
    conn.execute(
        "INSERT INTO statement (serial_no, statement_type_cd, statement_text) VALUES (?,?,?)",
        ["71165547", "GS0001", "From statement table"],
    )
    conn.execute(
        "INSERT INTO extended_marks (serial_no, goods_desc) VALUES (?,?)",
        ["71165547", "From extended marks"],
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
        "INSERT INTO extended_marks (serial_no, goods_desc) VALUES (?,?)",
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


def test_get_missing_enrichment_covered_by_extended_marks():
    conn = _db()
    conn.execute(
        "INSERT INTO extended_marks (serial_no, goods_desc) VALUES (?,?)",
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
        "INSERT INTO extended_marks (serial_no, goods_desc) VALUES (?,?)",
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


# ---------------------------------------------------------------------------
# mark_status_report (D036)
# ---------------------------------------------------------------------------

def _db_with_mark_status_data():
    """In-memory DB with case_file + owner for mark_status_report tests."""
    conn = open_db(":memory:")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS case_file "
        "(serial_no BIGINT, mark_id_char VARCHAR, filing_dt DATE, "
        " mark_draw_cd VARCHAR, registration_no VARCHAR, cfh_status_cd VARCHAR)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS owner "
        "(serial_no BIGINT, own_name VARCHAR, own_seq BIGINT)"
    )
    # Live mark, filed 1929 (public domain as of 2026: 2026-95=1931, so yes)
    conn.execute(
        "INSERT INTO case_file VALUES (71040001, 'EAGLE BRAND', '1929-06-01', '1', NULL, '600')"
    )
    conn.execute(
        "INSERT INTO owner VALUES (71040001, 'Eagle Mfg Co.', 1)"
    )
    # Dead mark, filed 1935 (not public domain: 1935 > 1931)
    conn.execute(
        "INSERT INTO case_file VALUES (71040002, 'FALCON', '1935-03-10', '1', NULL, '800')"
    )
    conn.execute(
        "INSERT INTO owner VALUES (71040002, 'Falcon Industries', 1)"
    )
    # Live mark from different owner — not in variant set
    conn.execute(
        "INSERT INTO case_file VALUES (71040003, 'RAVEN', '1930-01-01', '1', NULL, '400')"
    )
    conn.execute(
        "INSERT INTO owner VALUES (71040003, 'Raven Co.', 1)"
    )
    return conn


def test_mark_status_live_classification():
    from markery.specialist.trademark.queries import mark_status_report
    conn = _db_with_mark_status_data()
    results = mark_status_report(conn, ["Eagle Mfg Co."])
    assert len(results) == 1
    assert results[0]["serial_no"] == 71040001
    assert results[0]["live_dead"] == "live"
    conn.close()


def test_mark_status_dead_classification():
    from markery.specialist.trademark.queries import mark_status_report
    conn = _db_with_mark_status_data()
    results = mark_status_report(conn, ["Falcon Industries"])
    assert len(results) == 1
    assert results[0]["live_dead"] == "dead"
    conn.close()


def test_mark_status_public_domain_flag():
    from markery.specialist.trademark.queries import mark_status_report
    conn = _db_with_mark_status_data()
    # Use explicit threshold so test is stable regardless of current year
    results = mark_status_report(conn, ["Eagle Mfg Co."], pd_threshold_year=1930)
    assert results[0]["public_domain"] is True

    results_not_pd = mark_status_report(conn, ["Eagle Mfg Co."], pd_threshold_year=1928)
    assert results_not_pd[0]["public_domain"] is False
    conn.close()


def test_mark_status_dead_only_filter():
    from markery.specialist.trademark.queries import mark_status_report
    conn = _db_with_mark_status_data()
    results = mark_status_report(conn, ["Eagle Mfg Co.", "Falcon Industries"], dead_only=True)
    assert all(r["live_dead"] == "dead" for r in results)
    serials = {r["serial_no"] for r in results}
    assert 71040001 not in serials
    assert 71040002 in serials
    conn.close()


def test_mark_status_pd_only_filter():
    from markery.specialist.trademark.queries import mark_status_report
    conn = _db_with_mark_status_data()
    # Threshold 1930: 1929 <= 1930 (Eagle PD=True), 1935 <= 1930 (Falcon PD=False)
    results = mark_status_report(
        conn, ["Eagle Mfg Co.", "Falcon Industries"],
        pd_only=True, pd_threshold_year=1930,
    )
    assert all(r["public_domain"] for r in results)
    assert any(r["serial_no"] == 71040001 for r in results)
    conn.close()


def test_mark_status_empty_variants_returns_empty():
    from markery.specialist.trademark.queries import mark_status_report
    conn = _db_with_mark_status_data()
    assert mark_status_report(conn, []) == []
    conn.close()


def test_mark_status_figurative_mark_label():
    from markery.specialist.trademark.queries import mark_status_report
    conn = _db_with_mark_status_data()
    conn.execute(
        "INSERT INTO case_file VALUES (71040099, NULL, '1928-06-01', '2', NULL, '600')"
    )
    conn.execute("INSERT INTO owner VALUES (71040099, 'Design Only Corp', 1)")
    results = mark_status_report(conn, ["Design Only Corp"])
    assert results[0]["mark_text"] == "(figurative)"
    conn.close()
