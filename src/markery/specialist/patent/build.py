"""Build and populate patents.duckdb from EPO OPS.

Schema owns: patents, patent_classes, patent_inventors, patent_figures.
The patent_figures table stores drawing images as BLOBs (see figures.py).
Resume state is stored in a JSON file alongside patents.duckdb (see _fetch_log_path).

Entry point: build(classes, resume, year_start, year_end, seed_path, seed_only)
"""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

import duckdb

from markery.common.auth import load_epo_credentials
from markery.common.config import DB
from markery.specialist.patent.epo_client import EPOClient

RESULTS_PER_PAGE = 100
MAX_PER_QUERY    = 2000

# ---------------------------------------------------------------------------
# Schema DDL
# ---------------------------------------------------------------------------

DDL = """
CREATE TABLE IF NOT EXISTS patents (
    patent_no      VARCHAR PRIMARY KEY,  -- contract: VARCHAR, NOT NULL, guaranteed-present
    title          VARCHAR,              -- contract: VARCHAR, nullable
    app_dt         DATE,                 -- contract: DATE, nullable
    grant_dt       DATE,                 -- contract: DATE, nullable — primary scoring date
    abstract       VARCHAR,              -- contract: VARCHAR, nullable — populated by patent signals
    assignee_name  VARCHAR,              -- contract: VARCHAR, nullable — uppercase; may differ from entity canonical_name
    assignee_city  VARCHAR,
    assignee_state VARCHAR,
    fetched_dt     DATE,                 -- Markery load date (provenance) — when this row entered the corpus
    source         VARCHAR               -- Markery load source (provenance), e.g. 'epo_ops', 'seed', 'patentsview'
);

CREATE TABLE IF NOT EXISTS patent_classes (
    patent_no VARCHAR NOT NULL,  -- contract: VARCHAR, NOT NULL
    cpc_class VARCHAR,           -- contract: VARCHAR, nullable — 4-char CPC prefix used in scoring
    cpc_full  VARCHAR
);

CREATE TABLE IF NOT EXISTS patent_inventors (
    patent_no     VARCHAR NOT NULL,
    inventor_name VARCHAR
);

CREATE TABLE IF NOT EXISTS patent_figures (
    patent_no     VARCHAR  NOT NULL,
    figure_no     INTEGER  NOT NULL,
    file          VARCHAR,                 -- path relative to config.ASSETS_DIR (Phase 28 P3)
    sha256        VARCHAR,                 -- content hash of the asset file
    figure_format VARCHAR DEFAULT 'PNG',
    fetched_dt    DATE,
    PRIMARY KEY (patent_no, figure_no)
);
"""

# ---------------------------------------------------------------------------
# Fetch-log helpers (resume state stored in JSON, not in the research DB)
# ---------------------------------------------------------------------------

def _fetch_log_path(db_path: str) -> Path | None:
    """Return path to the JSON fetch-log file, or None for in-memory DBs."""
    p = Path(db_path)
    if str(p) == ":memory:":
        return None
    return p.with_name(p.stem + "_fetch_log.json")


def _load_fetch_log(log_path: Path | None) -> set[tuple]:
    """Return set of (cpc_class, year_start, year_end) tuples already fetched."""
    if log_path is None or not log_path.exists():
        return set()
    entries = json.loads(log_path.read_text())
    return {(e["cpc_class"], e["year_start"], e["year_end"]) for e in entries}


def _append_fetch_log(log_path: Path | None, entry: dict) -> None:
    """Append one fetch entry to the JSON log file."""
    if log_path is None:
        return
    entries: list[dict] = []
    if log_path.exists():
        entries = json.loads(log_path.read_text())
    entries.append(entry)
    log_path.write_text(json.dumps(entries, indent=2))


def _migrate_fetch_log(conn: duckdb.DuckDBPyConnection, db_path: str) -> None:
    """One-time migration: export fetch_log table to JSON and drop it from the DB."""
    tables = {r[0] for r in conn.execute("SHOW TABLES").fetchall()}
    if "fetch_log" not in tables:
        return
    rows = conn.execute(
        "SELECT cpc_class, year_start, year_end, fetch_dt, patents_added FROM fetch_log"
    ).fetchall()
    log_path = _fetch_log_path(db_path)
    if rows and log_path is not None:
        existing: list[dict] = []
        if log_path.exists():
            existing = json.loads(log_path.read_text())
        new_entries = [
            {
                "cpc_class":     r[0],
                "year_start":    r[1],
                "year_end":      r[2],
                "fetch_dt":      str(r[3]),
                "patents_added": r[4],
            }
            for r in rows
        ]
        seen = {(e["cpc_class"], e["year_start"], e["year_end"]) for e in existing}
        merged = existing + [e for e in new_entries
                             if (e["cpc_class"], e["year_start"], e["year_end"]) not in seen]
        log_path.write_text(json.dumps(merged, indent=2))
    conn.execute("DROP TABLE fetch_log")
    conn.commit()

# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def _migrate_provenance(conn: duckdb.DuckDBPyConnection) -> None:
    """Idempotently add the Markery provenance columns to an existing patents table.

    DuckDB applies ADD COLUMN IF NOT EXISTS as a no-op when the column is present,
    so pre-provenance DBs self-upgrade on the next writable open (existing rows
    keep NULL provenance until refreshed/rebuilt)."""
    conn.execute("ALTER TABLE patents ADD COLUMN IF NOT EXISTS fetched_dt DATE")
    conn.execute("ALTER TABLE patents ADD COLUMN IF NOT EXISTS source VARCHAR")


def _migrate_externalize_figures(conn: duckdb.DuckDBPyConnection) -> int:
    """Move patent_figures BLOBs out to files; add file/sha256; drop figure_data.

    Idempotent; self-runs on writable open. Returns the number exported."""
    conn.execute("ALTER TABLE patent_figures ADD COLUMN IF NOT EXISTS file VARCHAR")
    conn.execute("ALTER TABLE patent_figures ADD COLUMN IF NOT EXISTS sha256 VARCHAR")
    cols = {r[1] for r in conn.execute("PRAGMA table_info(patent_figures)").fetchall()}
    exported = 0
    if "figure_data" in cols:
        from markery.common.assets import patent_rel, write_asset
        rows = conn.execute(
            "SELECT patent_no, figure_no, figure_data FROM patent_figures "
            "WHERE figure_data IS NOT NULL AND file IS NULL"
        ).fetchall()
        for patent_no, figure_no, blob in rows:
            rel = patent_rel(patent_no, figure_no)
            sha = write_asset(rel, bytes(blob))
            conn.execute(
                "UPDATE patent_figures SET file = ?, sha256 = ? "
                "WHERE patent_no = ? AND figure_no = ?",
                [rel, sha, patent_no, figure_no],
            )
            exported += 1
        # DuckDB blocks DROP COLUMN on a PK table, so rebuild without figure_data.
        conn.execute("""
            CREATE TABLE patent_figures_new (
                patent_no     VARCHAR NOT NULL,
                figure_no     INTEGER NOT NULL,
                file          VARCHAR,
                sha256        VARCHAR,
                figure_format VARCHAR DEFAULT 'PNG',
                fetched_dt    DATE,
                PRIMARY KEY (patent_no, figure_no)
            )""")
        conn.execute(
            "INSERT INTO patent_figures_new "
            "(patent_no, figure_no, file, sha256, figure_format, fetched_dt) "
            "SELECT patent_no, figure_no, file, sha256, figure_format, fetched_dt "
            "FROM patent_figures"
        )
        conn.execute("DROP TABLE patent_figures")
        conn.execute("ALTER TABLE patent_figures_new RENAME TO patent_figures")
        conn.commit()
    return exported


def open_db(db_path: str | Path | None = None) -> duckdb.DuckDBPyConnection:
    path = str(db_path or DB["patents"])
    conn = duckdb.connect(path)
    conn.execute(DDL)
    _migrate_fetch_log(conn, path)
    _migrate_provenance(conn)
    _migrate_externalize_figures(conn)
    return conn


def insert_patent(conn: duckdb.DuckDBPyConnection, p: dict, source: str = "epo_ops") -> bool:
    """Insert one patent record. Returns True if newly inserted.

    Records Markery provenance: ``fetched_dt`` (today, unless the record carries
    its own) and ``source`` (the acquisition route; ``p['source']`` overrides the
    ``source`` argument)."""
    if conn.execute(
        "SELECT 1 FROM patents WHERE patent_no = ?", [p["patent_no"]]
    ).fetchone():
        return False

    conn.execute(
        """INSERT INTO patents
           (patent_no, title, app_dt, grant_dt, abstract,
            assignee_name, assignee_city, assignee_state, fetched_dt, source)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        [p["patent_no"], p.get("title"),
         p.get("app_dt"), p.get("grant_dt"), p.get("abstract"),
         p.get("assignee_name"), p.get("assignee_city"), p.get("assignee_state"),
         p.get("fetched_dt") or date.today(), p.get("source") or source],
    )
    for inv in p.get("inventors", []):
        conn.execute(
            "INSERT INTO patent_inventors (patent_no, inventor_name) VALUES (?,?)",
            [p["patent_no"], inv],
        )
    cpc_list = p.get("cpc", [])
    for sym in (cpc_list or [None]):
        conn.execute(
            "INSERT INTO patent_classes (patent_no, cpc_class, cpc_full) VALUES (?,?,?)",
            [p["patent_no"], sym[:4] if sym and len(sym) >= 4 else sym, sym],
        )
    return True


def load_seed(conn: duckdb.DuckDBPyConnection, seeds: list[dict]) -> int:
    """Insert seed patent records. Skips existing records. Returns count added."""
    added = sum(1 for s in seeds if insert_patent(conn, s))
    conn.commit()
    return added


def load_seed_from_file(conn: duckdb.DuckDBPyConnection, seed_path: str | Path) -> int:
    """Read seed patents from a JSON file and insert them. Returns count added."""
    seeds = json.loads(Path(seed_path).read_text())
    return load_seed(conn, seeds)


# ---------------------------------------------------------------------------
# Fetch logic
# ---------------------------------------------------------------------------

def _cql(cpc_class: str, year_start: int, year_end: int) -> str:
    return f'cpc={cpc_class} AND pd within "{year_start}0101,{year_end}1231" AND pn=US'


def _fetch_window(
    conn: duckdb.DuckDBPyConnection,
    client: EPOClient,
    cpc_class: str,
    year_start: int,
    year_end: int,
) -> int:
    """Fetch all pages for one CPC/year window. Subdivides if > MAX_PER_QUERY."""
    cql = _cql(cpc_class, year_start, year_end)
    total, first_page = client.search(cql, 1, RESULTS_PER_PAGE)
    if total == 0:
        return 0

    if total > MAX_PER_QUERY:
        print(f"    {cpc_class} {year_start}–{year_end}: {total} results — subdividing")
        return sum(
            _fetch_window(conn, client, cpc_class, yr, yr)
            for yr in range(year_start, year_end + 1)
        )

    added = sum(1 for p in first_page if insert_patent(conn, p))
    start = RESULTS_PER_PAGE + 1
    while start <= min(total, MAX_PER_QUERY):
        end = min(start + RESULTS_PER_PAGE - 1, total, MAX_PER_QUERY)
        _, page = client.search(cql, start, end)
        added += sum(1 for p in page if insert_patent(conn, p))
        start = end + 1

    conn.commit()
    return added


def _fetch_class(
    conn: duckdb.DuckDBPyConnection,
    client: EPOClient,
    cpc_class: str,
    resume: bool,
    year_start: int,
    year_end: int,
    log_path: Path | None,
) -> int:
    total = 0
    fetched = _load_fetch_log(log_path) if resume else set()
    windows = [(y, min(y + 4, year_end)) for y in range(year_start, year_end + 1, 5)]
    for ys, ye in windows:
        if resume and (cpc_class, ys, ye) in fetched:
            print(f"    skipping {cpc_class} {ys}–{ye} (already in fetch_log)")
            continue
        added = _fetch_window(conn, client, cpc_class, ys, ye)
        total += added
        print(f"    {cpc_class} {ys}–{ye}  +{added}")
        _append_fetch_log(log_path, {
            "cpc_class":     cpc_class,
            "year_start":    ys,
            "year_end":      ye,
            "fetch_dt":      datetime.now().isoformat(),
            "patents_added": added,
        })
    return total


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def build(
    classes:   list[str] | None = None,
    resume:    bool = False,
    year_start: int | None = None,
    year_end:   int | None = None,
    seed_path:  str | Path | None = None,
    seed_only:  bool = False,
    db_path:    str | Path | None = None,
) -> None:
    """Populate patents.duckdb from EPO OPS.

    seed_path: path to a JSON file of seed patent records. Omit to skip seeding.
    classes:   CPC class codes to fetch (required when not seed_only).
    year_start/year_end: date window (required when not seed_only).
    """
    db_path_str = str(db_path or DB["patents"])
    conn = open_db(db_path_str)
    print(f"Database: {db_path_str}")

    if seed_path:
        n = load_seed_from_file(conn, seed_path)
    else:
        n = 0
    print(f"  {n} seed patent(s) added")

    if seed_only:
        conn.close()
        return

    if not classes:
        raise ValueError("--classes is required (no default class list)")
    if year_start is None or year_end is None:
        raise ValueError("--year-start and --year-end are required")

    key, secret = load_epo_credentials()
    client = EPOClient(key, secret)
    log_path = _fetch_log_path(db_path_str)

    print(f"\nFetching: {', '.join(classes)}  ({year_start}–{year_end})")
    grand_total = 0
    for cls in classes:
        print(f"\nCPC {cls}")
        grand_total += _fetch_class(conn, client, cls, resume, year_start, year_end, log_path)

    conn.close()
    print(f"\nDone. {grand_total:,} patents added.")
