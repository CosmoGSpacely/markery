"""Corpus coverage + freshness manifest (Phase 28 P1).

A read-only view of *what the corpus holds* and *how fresh it is*, computed from
the Markery provenance columns (`fetched_dt`, `source`) added to the core record
tables. The autonomous loops (Phases 30–32) will consult a richer queryable model
(P4); this is the human-facing manifest that surfaces provenance and staleness.
"""

from __future__ import annotations

from datetime import date

import duckdb


def _columns(conn: duckdb.DuckDBPyConnection, table: str) -> set[str]:
    return {r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}


def _freshness(conn: duckdb.DuckDBPyConnection, table: str) -> dict:
    """Return {total, with_provenance, null_provenance, oldest, newest, migrated}.

    Degrades gracefully when the provenance column is absent (a pre-Phase-28 DB
    opened read-only cannot self-migrate): everything counts as unmigrated."""
    total = conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
    if "fetched_dt" not in _columns(conn, table):
        return {"total": total, "with_provenance": 0, "null_provenance": total,
                "oldest": None, "newest": None, "migrated": False}
    nn, oldest, newest = conn.execute(
        f"SELECT count(fetched_dt), min(fetched_dt), max(fetched_dt) FROM {table}"
    ).fetchone()
    return {
        "total": total,
        "with_provenance": nn,
        "null_provenance": total - nn,
        "oldest": str(oldest) if oldest else None,
        "newest": str(newest) if newest else None,
        "migrated": True,
    }


def _by_source(conn: duckdb.DuckDBPyConnection, table: str) -> list[tuple[str, int]]:
    if "source" not in _columns(conn, table):
        total = conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
        return [("(unmigrated — rebuild for provenance)", total)]
    rows = conn.execute(
        f"SELECT coalesce(source, '(none)') AS s, count(*) "
        f"FROM {table} GROUP BY s ORDER BY count(*) DESC"
    ).fetchall()
    return [(r[0], r[1]) for r in rows]


def patent_coverage(conn: duckdb.DuckDBPyConnection, fetch_log_windows: int = 0) -> dict:
    fresh = _freshness(conn, "patents")
    classes = conn.execute(
        "SELECT count(DISTINCT cpc_class) FROM patent_classes WHERE cpc_class IS NOT NULL"
    ).fetchone()[0]
    grant_lo, grant_hi = conn.execute(
        "SELECT min(grant_dt), max(grant_dt) FROM patents"
    ).fetchone()
    return {
        "freshness": fresh,
        "by_source": _by_source(conn, "patents"),
        "cpc_classes": classes,
        "grant_range": [str(grant_lo) if grant_lo else None,
                        str(grant_hi) if grant_hi else None],
        "fetch_log_windows": fetch_log_windows,
    }


def trademark_coverage(conn: duckdb.DuckDBPyConnection) -> dict:
    fresh = _freshness(conn, "case_file")
    dead = conn.execute(
        "SELECT count(*) FROM case_file WHERE cfh_status_cd >= 700"
    ).fetchone()[0]
    filing_lo, filing_hi = conn.execute(
        "SELECT min(filing_dt), max(filing_dt) FROM case_file"
    ).fetchone()
    return {
        "freshness": fresh,
        "by_source": _by_source(conn, "case_file"),
        "dead_marks": dead,
        "live_marks": fresh["total"] - dead,
        "filing_range": [str(filing_lo) if filing_lo else None,
                         str(filing_hi) if filing_hi else None],
    }


def format_coverage(kind: str, cov: dict) -> str:
    """Render a coverage dict (patent|trademark) as a human-readable report."""
    f = cov["freshness"]
    lines = [f"=== {kind} coverage — {date.today()} ==="]
    lines.append(f"records:        {f['total']:,}")
    if kind == "patent":
        lines.append(f"cpc classes:    {cov['cpc_classes']:,}")
        lo, hi = cov["grant_range"]
        lines.append(f"grant range:    {lo or '?'} … {hi or '?'}")
        if cov["fetch_log_windows"]:
            lines.append(f"fetch windows:  {cov['fetch_log_windows']:,} (class×year, logged)")
    else:
        lo, hi = cov["filing_range"]
        lines.append(f"filing range:   {lo or '?'} … {hi or '?'}")
        lines.append(f"live / dead:    {cov['live_marks']:,} / {cov['dead_marks']:,}"
                     f"  (dead = cfh_status_cd ≥ 700, eligible for merch)")
    lines.append("")
    lines.append("provenance (Markery load):")
    lines.append(f"  with fetched_dt: {f['with_provenance']:,}  ·  "
                 f"missing: {f['null_provenance']:,}")
    lines.append(f"  load dates:      {f['oldest'] or '—'} … {f['newest'] or '—'}")
    lines.append("")
    lines.append("by source:")
    for src, n in cov["by_source"]:
        lines.append(f"  {src:<20} {n:,}")
    return "\n".join(lines)
