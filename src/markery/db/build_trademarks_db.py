#!/usr/bin/env python3
"""
Build DuckDB database of USPTO trademark applications filed 1900-1939.
Loads: case_file, owner, owner_name_change, classification, intl_class,
       us_class, design_search, prior_mark
Source: /csv directory (2011 USPTO Trademark Case Files Dataset)
"""

import duckdb
import os
import time

CSV_DIR    = "csv"
DB_PATH    = "data/trademarks.duckdb"
START_DATE = "1900-01-01"
END_DATE   = "1939-12-31"


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def rc(name):
    """Return a read_csv_auto() expression with consistent settings."""
    path = os.path.join(CSV_DIR, f"{name}.csv")
    return f"read_csv_auto('{path}', header=true, nullstr='', quote='\"', sample_size=-1)"


def main():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        log(f"Removed existing {DB_PATH}")

    con = duckdb.connect(DB_PATH)
    con.execute("PRAGMA threads=4")

    # ── case_file ────────────────────────────────────────────────────────────
    log("Loading case_file ...")
    con.execute(f"""
        CREATE TABLE case_file AS
        SELECT *
        FROM {rc('case_file')}
        WHERE filing_dt >= '{START_DATE}'
          AND filing_dt <= '{END_DATE}'
    """)
    count = con.execute("SELECT COUNT(*) FROM case_file").fetchone()[0]
    log(f"  {count:,} rows")
    con.execute("CREATE INDEX idx_cf_serial ON case_file(serial_no)")
    con.execute("CREATE INDEX idx_cf_filing  ON case_file(filing_dt)")
    con.execute("CREATE INDEX idx_cf_draw    ON case_file(mark_draw_cd)")

    # Build serial number filter for companion tables
    log("Building serial number filter ...")
    con.execute("""
        CREATE TEMP TABLE target_serials AS
        SELECT serial_no FROM case_file
    """)

    # ── companion tables ─────────────────────────────────────────────────────
    companions = [
        ("owner",             "idx_own_serial", "owner"),
        ("owner_name_change", "idx_onc_serial", "owner_name_change"),
        ("classification",    "idx_cls_serial", "classification"),
        ("intl_class",        "idx_ic_serial",  "intl_class"),
        ("us_class",          "idx_uc_serial",  "us_class"),
        ("design_search",     "idx_ds_serial",  "design_search"),
        ("prior_mark",        "idx_pm_serial",  "prior_mark"),
    ]

    for table, idx, _ in companions:
        log(f"Loading {table} ...")
        con.execute(f"""
            CREATE TABLE {table} AS
            SELECT o.*
            FROM {rc(table)} o
            JOIN target_serials t USING (serial_no)
        """)
        count = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        log(f"  {count:,} rows")
        con.execute(f"CREATE INDEX {idx} ON {table}(serial_no)")

    # ── summary ──────────────────────────────────────────────────────────────
    log("Done. Table summary:")
    all_tables = ["case_file"] + [t for t, _, _ in companions]
    for t in all_tables:
        n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t:<22} {n:>8,} rows")

    con.close()
    size_mb = os.path.getsize(DB_PATH) / 1_048_576
    log(f"Database: {DB_PATH} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
