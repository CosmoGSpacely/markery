"""Small DuckDB query helpers shared across specialists.

`fetchone()` is typed ``tuple | None``, so ``conn.execute(...).fetchone()[0]`` on a
scalar aggregate (COUNT / COALESCE(MAX ...) / min-max) trips pyright's
reportOptionalSubscript even though such queries always return exactly one row.
These helpers centralise the guard so call sites stay clean and type-correct.
"""
from __future__ import annotations

from typing import Any


def scalar(conn, sql: str, params: list | None = None, default: Any = 0) -> Any:
    """First column of a single-row aggregate query (COUNT / MAX / min-max …).

    The ``row or (default,)`` guard satisfies the type checker; at runtime such
    aggregates always return exactly one row, so the default is not reached.
    """
    row = conn.execute(sql, params or []).fetchone()
    return (row or (default,))[0]


def next_id(conn, table: str, col: str) -> int:
    """Next free integer id for ``col`` in ``table``: MAX(col)+1, or 1 if empty.

    ``table``/``col`` are internal literals (not user input).
    """
    return scalar(conn, f"SELECT COALESCE(MAX({col}), 0) FROM {table}") + 1
