"""Pure read queries for patents.duckdb.

All functions accept an open DuckDB connection as their first argument so
callers control connection lifetime and tests can pass in-memory connections.
Use connect() to obtain a connection from the configured database path.
"""

from __future__ import annotations

import duckdb

from markery.common.config import DB


def connect() -> duckdb.DuckDBPyConnection:
    """Open a read-only connection to patents.duckdb."""
    return duckdb.connect(str(DB["patents"]), read_only=True)


def get_patent(conn: duckdb.DuckDBPyConnection, patent_no: str) -> dict | None:
    """Return a single patent record, or None if not found."""
    row = conn.execute(
        "SELECT patent_no, title, app_dt, grant_dt, abstract, assignee_name "
        "FROM patents WHERE patent_no = ?",
        [patent_no],
    ).fetchone()
    if not row:
        return None
    cpc = [r[0] for r in conn.execute(
        "SELECT DISTINCT cpc_class FROM patent_classes "
        "WHERE patent_no = ? AND cpc_class IS NOT NULL",
        [patent_no],
    ).fetchall()]
    inventors = [r[0] for r in conn.execute(
        "SELECT inventor_name FROM patent_inventors WHERE patent_no = ?",
        [patent_no],
    ).fetchall()]
    return {
        "patent_no":     row[0],
        "title":         row[1],
        "app_dt":        row[2],
        "grant_dt":      row[3],
        "abstract":      row[4],
        "assignee_name": row[5],
        "cpc_classes":   cpc,
        "inventors":     inventors,
    }


def has_abstract(conn: duckdb.DuckDBPyConnection, patent_no: str) -> bool:
    """True if the patent has a non-empty abstract."""
    row = conn.execute(
        "SELECT abstract FROM patents WHERE patent_no = ?", [patent_no]
    ).fetchone()
    return bool(row and row[0])


def has_figure(conn: duckdb.DuckDBPyConnection, patent_no: str) -> bool:
    """True if a figure blob exists in patent_figures for this patent."""
    row = conn.execute(
        "SELECT 1 FROM patent_figures "
        "WHERE patent_no = ? AND figure_data IS NOT NULL LIMIT 1",
        [patent_no],
    ).fetchone()
    return row is not None


def get_cpc_classes(conn: duckdb.DuckDBPyConnection, patent_no: str) -> list[str]:
    """Return the list of distinct 4-char CPC class codes for a patent."""
    rows = conn.execute(
        "SELECT DISTINCT cpc_class FROM patent_classes "
        "WHERE patent_no = ? AND cpc_class IS NOT NULL",
        [patent_no],
    ).fetchall()
    return [r[0] for r in rows]


def get_missing_signals(
    conn: duckdb.DuckDBPyConnection,
    patent_nos: list[str],
) -> list[str]:
    """Return patent numbers from the list that have no abstract text.

    Used by the prepare command to identify which confirmed patents need
    signal enrichment before a historian session.
    """
    if not patent_nos:
        return []
    placeholders = ",".join("?" * len(patent_nos))
    rows = conn.execute(
        f"SELECT patent_no FROM patents "
        f"WHERE patent_no IN ({placeholders}) "
        f"AND (abstract IS NULL OR abstract = '')",
        patent_nos,
    ).fetchall()
    return [r[0] for r in rows]
