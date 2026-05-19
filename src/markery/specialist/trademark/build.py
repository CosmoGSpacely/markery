"""Build and populate trademarks.duckdb from USPTO CSV source files.

Source: 2011 USPTO Trademark Case Files Dataset (csv/ directory).
This is a destructive rebuild -- existing data is replaced on each run.
Run once when the CSV source is updated; the dataset does not change often.

Entry point: build(csv_dir, db_path, date_start, date_end)
"""

from __future__ import annotations

import time
from pathlib import Path

import duckdb

from markery.common.config import DB, ROOT

# Tables loaded from CSV companion files (joined to case_file's serial_no set)
_COMPANION_TABLES = [
    "owner",
    "owner_name_change",
    "classification",
    "intl_class",
    "us_class",
    "design_search",
    "prior_mark",
    "statement",
]

# Tables added by TSDR enrichment (enrich.py) and single-fetch (fetch.py).
# Created on open_db() so they survive across CSV rebuilds.
# Note: events and foreign_app are on-demand — created by load_events() and
# load_foreign_app() respectively. They do not appear until explicitly loaded.
_ENRICHMENT_DDL = """
CREATE TABLE IF NOT EXISTS mark_images (
    serial_no    VARCHAR PRIMARY KEY,
    image_data   BLOB,
    image_format VARCHAR DEFAULT 'PNG',
    image_size   INTEGER,
    fetched_dt   DATE
);

CREATE TABLE IF NOT EXISTS extended_marks (
    serial_no         VARCHAR PRIMARY KEY,
    mark_text         VARCHAR,
    filing_dt         DATE,
    registration_no   VARCHAR,
    registration_dt   DATE,
    status_cd         VARCHAR,
    goods_desc        VARCHAR,
    intl_class        VARCHAR,
    owner_name        VARCHAR,   -- NULL for bulk-enrichment rows; set for standalone TSDR fetches
    first_use_dt      VARCHAR,
    first_use_comm_dt VARCHAR,
    raw_json          VARCHAR,
    fetched_dt        DATE
);
"""


def _migrate_mark_case_status(conn: duckdb.DuckDBPyConnection) -> None:
    """One-time migration: copy mark_case_status rows into extended_marks and drop it."""
    tables = {r[0] for r in conn.execute("SHOW TABLES").fetchall()}
    if "mark_case_status" not in tables:
        return
    conn.execute("""
        INSERT INTO extended_marks
            (serial_no, mark_text, filing_dt, registration_no, registration_dt,
             status_cd, goods_desc, intl_class, owner_name,
             first_use_dt, first_use_comm_dt, raw_json, fetched_dt)
        SELECT serial_no, mark_text, filing_dt, registration_no, registration_dt,
               status_cd, goods_desc, intl_class, NULL,
               first_use_dt, first_use_comm_dt, raw_json, fetched_dt
        FROM mark_case_status
        ON CONFLICT DO NOTHING
    """)
    conn.execute("DROP TABLE mark_case_status")
    conn.commit()


def load_events(
    csv_dir: str | Path,
    conn: duckdb.DuckDBPyConnection | None = None,
    db_path: str | Path | None = None,
) -> int:
    """Load event.csv into the events table (filtered to case_file serial numbers).

    Drops and recreates the events table from CSV each call.
    Returns the row count loaded.
    """
    csv_dir = Path(csv_dir)
    _own = conn is None
    if _own:
        conn = open_db(db_path)
    try:
        conn.execute("DROP TABLE IF EXISTS events")
        conn.execute(f"""
            CREATE TABLE events AS
            SELECT o.*
            FROM {_rc(csv_dir, 'event')} o
            JOIN (SELECT serial_no FROM case_file) t USING (serial_no)
        """)
        conn.execute("CREATE INDEX idx_ev_serial ON events(serial_no)")
        n = conn.execute("SELECT count(*) FROM events").fetchone()[0]
    finally:
        if _own:
            conn.close()
    return n


def load_foreign_app(
    csv_dir: str | Path,
    conn: duckdb.DuckDBPyConnection | None = None,
    db_path: str | Path | None = None,
) -> int:
    """Load foreign_application.csv into the foreign_app table (filtered to case_file serials).

    Drops and recreates the foreign_app table from CSV each call.
    Returns the row count loaded.
    """
    csv_dir = Path(csv_dir)
    _own = conn is None
    if _own:
        conn = open_db(db_path)
    try:
        conn.execute("DROP TABLE IF EXISTS foreign_app")
        conn.execute(f"""
            CREATE TABLE foreign_app AS
            SELECT o.*
            FROM {_rc(csv_dir, 'foreign_application')} o
            JOIN (SELECT serial_no FROM case_file) t USING (serial_no)
        """)
        conn.execute("CREATE INDEX idx_fa_serial ON foreign_app(serial_no)")
        n = conn.execute("SELECT count(*) FROM foreign_app").fetchone()[0]
    finally:
        if _own:
            conn.close()
    return n


def _rc(csv_dir: Path, name: str) -> str:
    """Return a read_csv_auto() expression for the named CSV file."""
    path = csv_dir / f"{name}.csv"
    return (
        f"read_csv_auto('{path}', header=true, nullstr='', "
        f"quote='\"', sample_size=-1)"
    )


def open_db(db_path: str | Path | None = None) -> duckdb.DuckDBPyConnection:
    """Open (or create) trademarks.duckdb and ensure enrichment tables exist."""
    path = str(db_path or DB["trademarks"])
    conn = duckdb.connect(path)
    conn.execute(_ENRICHMENT_DDL)
    _migrate_mark_case_status(conn)
    return conn


def build(
    csv_dir:    str | Path | None = None,
    db_path:    str | Path | None = None,
    date_start: str | None = None,
    date_end:   str | None = None,
) -> dict[str, int]:
    """Drop and recreate all CSV-sourced tables in trademarks.duckdb.

    Enrichment tables (mark_images, extended_marks) are preserved.
    Supply date_start/date_end to restrict case_file rows by filing_dt;
    omit both to load the full dataset.
    Returns a dict of table → row count.
    """
    csv_dir = Path(csv_dir or ROOT / "csv")
    db_path = Path(db_path or DB["trademarks"])

    if not csv_dir.is_dir():
        raise FileNotFoundError(f"CSV directory not found: {csv_dir}")

    conn = duckdb.connect(str(db_path))
    conn.execute("PRAGMA threads=4")

    def _log(msg: str) -> None:
        print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

    # Ensure enrichment tables survive the rebuild
    conn.execute(_ENRICHMENT_DDL)

    # ── case_file ─────────────────────────────────────────────────────────────
    _log("Loading case_file ...")
    conn.execute("DROP TABLE IF EXISTS case_file")
    _conds = []
    if date_start:
        _conds.append(f"filing_dt >= '{date_start}'")
    if date_end:
        _conds.append(f"filing_dt <= '{date_end}'")
    _where = ("WHERE " + " AND ".join(_conds)) if _conds else ""
    conn.execute(f"""
        CREATE TABLE case_file AS
        SELECT *
        FROM {_rc(csv_dir, 'case_file')}
        {_where}
    """)
    conn.execute("CREATE INDEX idx_cf_serial ON case_file(serial_no)")
    conn.execute("CREATE INDEX idx_cf_filing  ON case_file(filing_dt)")
    conn.execute("CREATE INDEX idx_cf_draw    ON case_file(mark_draw_cd)")

    # Build serial number filter for companion tables
    _log("Building serial number filter ...")
    conn.execute("""
        CREATE OR REPLACE TEMP TABLE target_serials AS
        SELECT serial_no FROM case_file
    """)

    # ── companion tables ──────────────────────────────────────────────────────
    index_map = {
        "owner":             "idx_own_serial",
        "owner_name_change": "idx_onc_serial",
        "classification":    "idx_cls_serial",
        "intl_class":        "idx_ic_serial",
        "us_class":          "idx_uc_serial",
        "design_search":     "idx_ds_serial",
        "prior_mark":        "idx_pm_serial",
        "statement":         "idx_stmt_serial",
    }

    for table in _COMPANION_TABLES:
        _log(f"Loading {table} ...")
        conn.execute(f"DROP TABLE IF EXISTS {table}")
        conn.execute(f"""
            CREATE TABLE {table} AS
            SELECT o.*
            FROM {_rc(csv_dir, table)} o
            JOIN target_serials t USING (serial_no)
        """)
        idx = index_map[table]
        conn.execute(f"CREATE INDEX {idx} ON {table}(serial_no)")

    conn.commit()

    # ── row counts ────────────────────────────────────────────────────────────
    counts: dict[str, int] = {}
    for t in ["case_file"] + _COMPANION_TABLES:
        counts[t] = conn.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
        _log(f"  {t:<22} {counts[t]:>8,} rows")

    conn.close()
    return counts
