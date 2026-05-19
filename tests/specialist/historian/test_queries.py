"""Tests for historian/queries.py — G1 cross-specialist query wrapper.

All tests use monkey-patching or in-memory connections so that no real
database files are required.
"""

from __future__ import annotations

import duckdb
import pytest

from markery.specialist.historian import queries as hq


# ---------------------------------------------------------------------------
# Helpers: minimal in-memory DBs matching the schemas each specialist uses
# ---------------------------------------------------------------------------

_PATENT_DDL = """
CREATE TABLE patents (
    patent_no   VARCHAR PRIMARY KEY,
    title       VARCHAR,
    app_dt      DATE,
    grant_dt    DATE,
    abstract    VARCHAR,
    assignee_name VARCHAR
);
CREATE TABLE patent_classes (
    patent_no VARCHAR,
    cpc_class VARCHAR,
    cpc_full  VARCHAR
);
CREATE TABLE patent_inventors (
    patent_no     VARCHAR,
    inventor_name VARCHAR
);
CREATE TABLE patent_figures (
    patent_no   VARCHAR,
    figure_data BLOB
);
"""

_TRADEMARK_DDL = """
CREATE TABLE statement (
    serial_no      VARCHAR,
    statement_type_cd VARCHAR,
    statement_text VARCHAR
);
CREATE TABLE mark_case_status (
    serial_no  VARCHAR PRIMARY KEY,
    goods_desc VARCHAR
);
"""


def _pat_conn():
    conn = duckdb.connect(":memory:")
    conn.execute(_PATENT_DDL)
    return conn


def _tm_conn():
    conn = duckdb.connect(":memory:")
    conn.execute(_TRADEMARK_DDL)
    return conn


# ---------------------------------------------------------------------------
# patent_has_abstract
# ---------------------------------------------------------------------------

def test_patent_has_abstract_true():
    conn = _pat_conn()
    conn.execute("INSERT INTO patents VALUES ('US1A','T','2000-01-01','2001-01-01','Some text','Acme')")
    assert hq.patent_has_abstract(conn, "US1A") is True


def test_patent_has_abstract_false_when_null():
    conn = _pat_conn()
    conn.execute("INSERT INTO patents VALUES ('US1A','T','2000-01-01','2001-01-01',NULL,'Acme')")
    assert hq.patent_has_abstract(conn, "US1A") is False


def test_patent_has_abstract_false_when_missing():
    conn = _pat_conn()
    assert hq.patent_has_abstract(conn, "US9999A") is False


# ---------------------------------------------------------------------------
# patent_has_figure
# ---------------------------------------------------------------------------

def test_patent_has_figure_true():
    conn = _pat_conn()
    conn.execute("INSERT INTO patent_figures VALUES ('US1A', X'89504E47')")
    assert hq.patent_has_figure(conn, "US1A") is True


def test_patent_has_figure_false():
    conn = _pat_conn()
    assert hq.patent_has_figure(conn, "US9999A") is False


# ---------------------------------------------------------------------------
# trademark_goods_available
# ---------------------------------------------------------------------------

def test_trademark_goods_available_via_statement():
    conn = _tm_conn()
    conn.execute("INSERT INTO statement VALUES ('71000001','GS001','Filing systems.')")
    assert hq.trademark_goods_available(conn, "71000001") is True


def test_trademark_goods_available_via_case_status():
    conn = _tm_conn()
    conn.execute("INSERT INTO mark_case_status VALUES ('71000002','Filing systems.')")
    assert hq.trademark_goods_available(conn, "71000002") is True


def test_trademark_goods_not_available():
    conn = _tm_conn()
    assert hq.trademark_goods_available(conn, "00000000") is False
