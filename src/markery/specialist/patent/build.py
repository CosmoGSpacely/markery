"""Build and populate patents.duckdb from EPO OPS.

Schema owns: patents, patent_classes, patent_inventors, patent_figures, fetch_log.
The patent_figures table stores drawing images as BLOBs (see figures.py).
fetch_log tracks completed CPC class/year windows to enable --resume.

Entry point: build(classes, resume, year_start, year_end, seed_only)
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import duckdb

from markery.common.auth import load_epo_credentials
from markery.common.config import DB
from markery.specialist.patent.epo_client import EPOClient

START_YEAR = 1900
END_YEAR   = 1939

RESULTS_PER_PAGE = 100
MAX_PER_QUERY    = 2000

CPC_CLASSES: dict[str, str] = {
    "B42F": "Filing appliances, card-index systems, loose-leaf binders",
    "B42D": "Books, printed matter, forms, index cards, ledger sheets",
    "B41J": "Typewriters, selective printing mechanisms",
    "B41L": "Addressing and duplicating machines for office use",
    "G06C": "Mechanical calculators, tabulating machines",
    "G06K": "Punched cards, record carriers, recognition of data",
    "G09F": "Displaying, advertising, visible record systems, signs",
}

# ---------------------------------------------------------------------------
# Schema DDL
# ---------------------------------------------------------------------------

DDL = """
CREATE TABLE IF NOT EXISTS patents (
    patent_no      VARCHAR PRIMARY KEY,
    title          VARCHAR,
    app_dt         DATE,
    grant_dt       DATE,
    abstract       VARCHAR,
    assignee_name  VARCHAR,
    assignee_city  VARCHAR,
    assignee_state VARCHAR
);

CREATE TABLE IF NOT EXISTS patent_classes (
    patent_no VARCHAR NOT NULL,
    cpc_class VARCHAR,
    cpc_full  VARCHAR
);

CREATE TABLE IF NOT EXISTS patent_inventors (
    patent_no     VARCHAR NOT NULL,
    inventor_name VARCHAR
);

CREATE TABLE IF NOT EXISTS patent_figures (
    patent_no    VARCHAR  NOT NULL,
    figure_no    INTEGER  NOT NULL,
    figure_data  BLOB,
    figure_format VARCHAR DEFAULT 'PNG',
    fetched_dt   DATE,
    PRIMARY KEY (patent_no, figure_no)
);

CREATE TABLE IF NOT EXISTS fetch_log (
    cpc_class     VARCHAR,
    year_start    INTEGER,
    year_end      INTEGER,
    fetch_dt      TIMESTAMP,
    patents_added INTEGER
);
"""

# ---------------------------------------------------------------------------
# Seed data — manually curated records with enriched abstracts
# ---------------------------------------------------------------------------

SEED_PATENTS: list[dict] = [
    {
        "patent_no":     "US1261167A",
        "title":         "Index",
        "app_dt":        "1917-10-25",
        "grant_dt":      "1918-04-02",
        "abstract":      "Phonetic indexing system that encodes surnames by consonant sound "
                         "into a letter-number code, enabling retrieval of records without "
                         "exact spelling. Known as the Soundex system.",
        "assignee_name": "Remington Typewriter Company",
        "cpc":           ["B42F17/00"],
        "inventors":     ["Russell Robert C"],
    },
    {
        "patent_no":     "US1435663A",
        "title":         "Index",
        "app_dt":        "1921-12-19",
        "grant_dt":      "1922-11-14",
        "abstract":      "Improved phonetic indexing system extending the Russell Soundex "
                         "method. Assigned to Remington Typewriter Company; commercialized "
                         "by Rand Kardex Bureau as the SOUNDEX product line.",
        "assignee_name": "Remington Typewriter Company",
        "cpc":           ["B42F17/00"],
        "inventors":     ["Odell Margaret K"],
    },
]

# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def open_db(db_path: str | Path | None = None) -> duckdb.DuckDBPyConnection:
    path = str(db_path or DB["patents"])
    conn = duckdb.connect(path)
    conn.execute(DDL)
    return conn


def insert_patent(conn: duckdb.DuckDBPyConnection, p: dict) -> bool:
    """Insert one patent record. Returns True if newly inserted."""
    if conn.execute(
        "SELECT 1 FROM patents WHERE patent_no = ?", [p["patent_no"]]
    ).fetchone():
        return False

    conn.execute(
        """INSERT INTO patents
           (patent_no, title, app_dt, grant_dt, abstract,
            assignee_name, assignee_city, assignee_state)
           VALUES (?,?,?,?,?,?,?,?)""",
        [p["patent_no"], p.get("title"),
         p.get("app_dt"), p.get("grant_dt"), p.get("abstract"),
         p.get("assignee_name"), p.get("assignee_city"), p.get("assignee_state")],
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


def load_seed(conn: duckdb.DuckDBPyConnection) -> int:
    added = sum(1 for s in SEED_PATENTS if insert_patent(conn, s))
    conn.commit()
    return added


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
) -> int:
    total = 0
    windows = [(y, min(y + 4, year_end)) for y in range(year_start, year_end + 1, 5)]
    for ys, ye in windows:
        if resume and conn.execute(
            "SELECT 1 FROM fetch_log WHERE cpc_class=? AND year_start=? AND year_end=?",
            [cpc_class, ys, ye],
        ).fetchone():
            print(f"    skipping {cpc_class} {ys}–{ye} (already in fetch_log)")
            continue
        added = _fetch_window(conn, client, cpc_class, ys, ye)
        total += added
        print(f"    {cpc_class} {ys}–{ye}  +{added}")
        conn.execute(
            "INSERT INTO fetch_log VALUES (?,?,?,?,?)",
            [cpc_class, ys, ye, datetime.now(), added],
        )
        conn.commit()
    return total


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def build(
    classes: list[str] | None = None,
    resume: bool = False,
    year_start: int = START_YEAR,
    year_end: int = END_YEAR,
    seed_only: bool = False,
    db_path: str | Path | None = None,
) -> None:
    conn = open_db(db_path)
    print(f"Database: {db_path or DB['patents']}")

    n = load_seed(conn)
    print(f"  {n} seed patent(s) added")

    if seed_only:
        conn.close()
        return

    key, secret = load_epo_credentials()
    client = EPOClient(key, secret)

    target = classes or list(CPC_CLASSES)
    print(f"\nFetching: {', '.join(target)}  ({year_start}–{year_end})")
    grand_total = 0
    for cls in target:
        print(f"\nCPC {cls}  {CPC_CLASSES.get(cls, '')}")
        grand_total += _fetch_class(conn, client, cls, resume, year_start, year_end)

    conn.close()
    print(f"\nDone. {grand_total:,} patents added.")
