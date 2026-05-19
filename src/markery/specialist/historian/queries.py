"""Historian's own query layer — wraps cross-specialist reads via deferred imports.

historian/prepare.py imports from here exclusively.  No historian module imports
directly from patent, trademark, or publisher specialist packages — per G5 policy,
all cross-specialist reads route through this module.
"""

from __future__ import annotations

import duckdb


def connect_patents() -> duckdb.DuckDBPyConnection:
    from markery.specialist.patent.queries import connect
    return connect()


def connect_trademarks() -> duckdb.DuckDBPyConnection:
    from markery.specialist.trademark.queries import connect
    return connect()


def patent_has_abstract(conn: duckdb.DuckDBPyConnection, patent_no: str) -> bool:
    from markery.specialist.patent.queries import has_abstract
    return has_abstract(conn, patent_no)


def patent_has_figure(conn: duckdb.DuckDBPyConnection, patent_no: str) -> bool:
    from markery.specialist.patent.queries import has_figure
    return has_figure(conn, patent_no)


def trademark_goods_available(conn: duckdb.DuckDBPyConnection, serial_no: str) -> bool:
    from markery.specialist.trademark.queries import get_goods_desc
    return get_goods_desc(conn, serial_no) is not None


def content_gaps(project: str) -> list[dict]:
    from markery.specialist.publisher.queries import get_content_gaps
    return get_content_gaps(project)
