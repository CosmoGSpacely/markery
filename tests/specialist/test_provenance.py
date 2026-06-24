"""Phase 28 P1 — record provenance + coverage manifest (hermetic)."""

from __future__ import annotations

from datetime import date

import duckdb

from markery.specialist.patent import open_db as pat_open_db, insert_patent
from markery.specialist.trademark import open_db as tm_open_db
from markery.common.coverage import (
    patent_coverage, trademark_coverage, format_coverage,
    window_covered, missing_year_spans, coverage_query,
)


# ---------------------------------------------------------------------------
# patents — provenance on insert + migration
# ---------------------------------------------------------------------------

def test_insert_patent_stamps_provenance(tmp_path):
    db = tmp_path / "patents.duckdb"
    conn = pat_open_db(db)
    insert_patent(conn, {
        "patent_no": "US9000001A", "title": "Test", "grant_dt": "1930-01-01",
        "assignee_name": "ACME", "cpc": ["G01B"],
    })
    row = conn.execute(
        "SELECT fetched_dt, source FROM patents WHERE patent_no = 'US9000001A'"
    ).fetchone()
    conn.close()
    assert row[0] == date.today()
    assert row[1] == "epo_ops"


def test_insert_patent_respects_explicit_source(tmp_path):
    conn = pat_open_db(tmp_path / "p.duckdb")
    insert_patent(conn, {"patent_no": "US9000002A"}, source="seed")
    src = conn.execute(
        "SELECT source FROM patents WHERE patent_no = 'US9000002A'"
    ).fetchone()[0]
    conn.close()
    assert src == "seed"


def test_patent_provenance_migration_adds_columns(tmp_path):
    # Simulate a pre-provenance DB: a patents table without fetched_dt/source.
    db = tmp_path / "old.duckdb"
    conn = duckdb.connect(str(db))
    conn.execute("CREATE TABLE patents (patent_no VARCHAR PRIMARY KEY, title VARCHAR)")
    conn.execute("INSERT INTO patents VALUES ('US1A', 'Legacy')")
    conn.close()
    # open_db must self-migrate (ADD COLUMN IF NOT EXISTS).
    conn = pat_open_db(db)
    cols = [r[1] for r in conn.execute("PRAGMA table_info(patents)").fetchall()]
    legacy = conn.execute("SELECT fetched_dt, source FROM patents WHERE patent_no='US1A'").fetchone()
    conn.close()
    assert "fetched_dt" in cols and "source" in cols
    assert legacy == (None, None)  # legacy rows keep NULL provenance until rebuild


# ---------------------------------------------------------------------------
# trademarks — provenance migration
# ---------------------------------------------------------------------------

def test_trademark_provenance_migration_adds_columns(tmp_path):
    db = tmp_path / "tm.duckdb"
    conn = duckdb.connect(str(db))
    conn.execute("CREATE TABLE case_file (serial_no BIGINT, filing_dt DATE)")
    conn.execute("INSERT INTO case_file VALUES (71000001, DATE '1930-01-01')")
    conn.close()
    conn = tm_open_db(db)
    cols = [r[1] for r in conn.execute("PRAGMA table_info(case_file)").fetchall()]
    conn.close()
    assert "fetched_dt" in cols and "source" in cols


# ---------------------------------------------------------------------------
# coverage helpers
# ---------------------------------------------------------------------------

def test_patent_coverage_report(tmp_path):
    conn = pat_open_db(tmp_path / "p.duckdb")
    insert_patent(conn, {"patent_no": "US1A", "grant_dt": "1930-01-01",
                                   "cpc": ["G01B"]}, source="epo_ops")
    insert_patent(conn, {"patent_no": "US2A", "grant_dt": "1931-02-02",
                                   "cpc": ["H04N"]}, source="seed")
    cov = patent_coverage(conn, fetch_log_windows=3)
    conn.close()
    assert cov["freshness"]["total"] == 2
    assert cov["freshness"]["null_provenance"] == 0
    assert cov["cpc_classes"] == 2
    assert dict(cov["by_source"]) == {"epo_ops": 1, "seed": 1}
    assert cov["fetch_log_windows"] == 3
    text = format_coverage("patent", cov)
    assert "patent coverage" in text and "epo_ops" in text


# ---------------------------------------------------------------------------
# queryable coverage model (P4)
# ---------------------------------------------------------------------------

def test_window_covered_and_missing_spans():
    windows = [("G01B", 1920, 1924), ("G01B", 1925, 1929), ("H04N", 1930, 1934)]
    assert window_covered(windows, "G01B", 1921, 1928) is True
    assert window_covered(windows, "G01B", 1921, 1932) is False
    # 1930–1932 unlogged for G01B → reported as the gap to fetch.
    assert missing_year_spans(windows, "G01B", 1921, 1932) == [(1930, 1932)]
    # disjoint gaps coalesce correctly.
    assert missing_year_spans(windows, "G01B", 1918, 1931) == [(1918, 1919), (1930, 1931)]
    # an entirely unlogged class is one big span.
    assert missing_year_spans(windows, "Z99Z", 1920, 1922) == [(1920, 1922)]


def test_coverage_query_reads_log_and_local_count(tmp_path):
    db = tmp_path / "patents.duckdb"
    conn = pat_open_db(db)
    insert_patent(conn, {"patent_no": "US1A", "grant_dt": "1925-06-01", "cpc": ["G01B"]})
    insert_patent(conn, {"patent_no": "US2A", "grant_dt": "1927-06-01", "cpc": ["G01B"]})
    conn.close()
    # Log a fetch window covering 1925–1929 for G01B.
    import json
    (tmp_path / "patents_fetch_log.json").write_text(json.dumps([
        {"cpc_class": "G01B", "year_start": 1925, "year_end": 1929, "patents_added": 2}
    ]))
    q = coverage_query(db, "G01B", 1925, 1930)
    assert q["covered"] is False           # 1930 not logged
    assert q["missing_spans"] == [(1930, 1930)]
    assert q["local_count"] == 2
    q2 = coverage_query(db, "G01B", 1925, 1929)
    assert q2["covered"] is True and q2["missing_spans"] == []


def test_coverage_degrades_without_provenance_columns(tmp_path):
    # A pre-Phase-28 patents table (no fetched_dt/source), opened read-only.
    db = tmp_path / "legacy.duckdb"
    conn = duckdb.connect(str(db))
    conn.execute("CREATE TABLE patents (patent_no VARCHAR, grant_dt DATE)")
    conn.execute("CREATE TABLE patent_classes (patent_no VARCHAR, cpc_class VARCHAR)")
    conn.execute("INSERT INTO patents VALUES ('US1A', DATE '1930-01-01')")
    conn.close()
    conn = duckdb.connect(str(db), read_only=True)
    cov = patent_coverage(conn)
    conn.close()
    assert cov["freshness"]["migrated"] is False
    assert cov["freshness"]["total"] == 1
    assert "unmigrated" in cov["by_source"][0][0]


def test_trademark_coverage_report(tmp_path):
    db = tmp_path / "tm.duckdb"
    conn = duckdb.connect(str(db))
    conn.execute(
        "CREATE TABLE case_file (serial_no BIGINT, filing_dt DATE, cfh_status_cd INTEGER, "
        "fetched_dt DATE, source VARCHAR)"
    )
    conn.execute("INSERT INTO case_file VALUES (71000001, DATE '1930-01-01', 630, DATE '2026-06-01', 'uspto_bulk_csv')")
    conn.execute("INSERT INTO case_file VALUES (71000002, DATE '1931-01-01', 710, DATE '2026-06-01', 'uspto_bulk_csv')")
    cov = trademark_coverage(conn)
    conn.close()
    assert cov["freshness"]["total"] == 2
    assert cov["dead_marks"] == 1 and cov["live_marks"] == 1
    text = format_coverage("trademark", cov)
    assert "live / dead" in text
