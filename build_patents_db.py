#!/usr/bin/env python3
"""
build_patents_db.py

Build patents.duckdb from the PatentsView API (search.patentsview.org).

Fetches patents granted 1900–1939 in the USPC classes relevant to
pre-computer information systems, then loads them into a local DuckDB
database for cross-referencing against trademarks.duckdb.

Requirements:
  - Internet access to search.patentsview.org
  - pip install duckdb requests  (already in requirements.txt)

Usage:
  python build_patents_db.py                     # full build, all classes
  python build_patents_db.py --classes 235 40    # specific classes only
  python build_patents_db.py --resume            # skip already-fetched classes
  python build_patents_db.py --seed-only         # load seed patents, skip API

Network note:
  The PatentsView API lives at search.patentsview.org. Some sandboxed
  environments cannot resolve this host. Run from a normal internet
  connection. Use --seed-only to load the manually-curated seed patents
  in any environment.
"""

from __future__ import annotations

import argparse
import sys
import time
from datetime import date, datetime
from pathlib import Path

import duckdb
import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DB_PATH = "patents.duckdb"

START_DATE = "1900-01-01"
END_DATE   = "1939-12-31"

# USPC classes relevant to pre-computer information systems
USPC_CLASSES: dict[str, str] = {
    "235": "Registers — tabulating, calculating, punched card machines",
    "40":  "Card, picture, or sign exhibiting — visible record systems",
    "281": "Books, strips, and leaves — loose-leaf binders, filing systems",
    "101": "Printing — typewriters, duplicating, addressing machines",
    "283": "Printed matter — forms, index cards, ledger sheets",
}

API_BASE   = "https://search.patentsview.org/api/v1/patent/"
PER_PAGE   = 1000   # PatentsView maximum
RATE_SLEEP = 0.25   # seconds between requests

# Fields to request from PatentsView
FIELDS = [
    "patent_id",
    "patent_title",
    "grant_date",
    "app_date",
    "patent_abstract",
    "assignees.assignee_organization",
    "assignees.assignee_city",
    "assignees.assignee_state",
    "inventors.inventor_name_first",
    "inventors.inventor_name_last",
    "inventors.inventor_city",
    "inventors.inventor_state",
    "uspc_primary_class.mainclass_id",
    "uspc_primary_class.subclass_id",
    "ipc_classes.ipc_action_date",
    "ipc_classes.ipc_main_group",
    "ipc_classes.ipc_section",
    "ipc_classes.ipc_class",
    "ipc_classes.ipc_subclass",
]

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

DDL = """
CREATE TABLE IF NOT EXISTS patents (
    patent_no      VARCHAR PRIMARY KEY,
    title          VARCHAR,
    app_dt         DATE,
    grant_dt       DATE,
    abstract       VARCHAR,
    assignee_name  VARCHAR,   -- first / primary assignee
    assignee_city  VARCHAR,
    assignee_state VARCHAR
);

CREATE TABLE IF NOT EXISTS patent_classes (
    patent_no      VARCHAR NOT NULL,
    uspc_mainclass VARCHAR,
    uspc_subclass  VARCHAR,
    ipc_section    VARCHAR,
    ipc_class      VARCHAR,
    ipc_subclass   VARCHAR,
    ipc_main_group VARCHAR
);

CREATE TABLE IF NOT EXISTS patent_inventors (
    patent_no      VARCHAR NOT NULL,
    inventor_name  VARCHAR,
    inventor_city  VARCHAR,
    inventor_state VARCHAR
);

CREATE TABLE IF NOT EXISTS fetch_log (
    uspc_class    VARCHAR,
    fetch_dt      TIMESTAMP,
    pages_fetched INTEGER,
    patents_added INTEGER
);
"""

# ---------------------------------------------------------------------------
# Seed data
#
# Manually curated patents known to be relevant. Loaded by --seed-only and
# also during a full build to ensure these are always present regardless of
# API pagination edge cases.
# ---------------------------------------------------------------------------

SEED_PATENTS: list[dict] = [
    {
        "patent_no":      "1261167",
        "title":          "Index",
        "app_dt":         "1916-08-01",
        "grant_dt":       "1918-04-02",
        "abstract":       "Phonetic indexing system that encodes surnames by consonant sound "
                          "into a letter-number code, enabling retrieval of records without "
                          "exact spelling. Known as the Soundex system.",
        "assignee_name":  "Remington Typewriter Company",
        "assignee_city":  "New York",
        "assignee_state": "NY",
        "inventors":      [("Robert C.", "Russell", None, None)],
        "uspc_mainclass": "40",
        "uspc_subclass":  None,
        "ipc":            [],
    },
    {
        "patent_no":      "1435663",
        "title":          "Index",
        "app_dt":         "1921-12-19",
        "grant_dt":       "1922-11-14",
        "abstract":       "Improved phonetic indexing system extending the Russell Soundex "
                          "method. Assigned to Remington Typewriter Company; commercialized "
                          "by Rand Kardex Bureau as the SOUNDEX product line.",
        "assignee_name":  "Remington Typewriter Company",
        "assignee_city":  "New York",
        "assignee_state": "NY",
        "inventors":      [("Margaret K.", "Odell", None, None)],
        "uspc_mainclass": "40",
        "uspc_subclass":  None,
        "ipc":            [],
    },
]

# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def init_db(db_path: str) -> duckdb.DuckDBPyConnection:
    conn = duckdb.connect(db_path)
    conn.execute(DDL)
    return conn


def _parse_date(s: str | None) -> date | None:
    if not s:
        return None
    try:
        return datetime.strptime(s[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def insert_patent(conn: duckdb.DuckDBPyConnection, p: dict) -> bool:
    """Insert one patent record. Returns True if inserted, False if already exists."""
    existing = conn.execute(
        "SELECT 1 FROM patents WHERE patent_no = ?", [p["patent_no"]]
    ).fetchone()
    if existing:
        return False

    conn.execute(
        """INSERT INTO patents
           (patent_no, title, app_dt, grant_dt, abstract,
            assignee_name, assignee_city, assignee_state)
           VALUES (?,?,?,?,?,?,?,?)""",
        [
            p["patent_no"],
            p.get("title"),
            _parse_date(p.get("app_dt")),
            _parse_date(p.get("grant_dt")),
            p.get("abstract"),
            p.get("assignee_name"),
            p.get("assignee_city"),
            p.get("assignee_state"),
        ],
    )

    for name, city, state in p.get("inventors", []):
        conn.execute(
            "INSERT INTO patent_inventors (patent_no, inventor_name, inventor_city, inventor_state) VALUES (?,?,?,?)",
            [p["patent_no"], name, city, state],
        )

    for ipc in p.get("ipc", []):
        conn.execute(
            """INSERT INTO patent_classes
               (patent_no, uspc_mainclass, uspc_subclass,
                ipc_section, ipc_class, ipc_subclass, ipc_main_group)
               VALUES (?,?,?,?,?,?,?)""",
            [
                p["patent_no"],
                p.get("uspc_mainclass"),
                p.get("uspc_subclass"),
                ipc.get("ipc_section"),
                ipc.get("ipc_class"),
                ipc.get("ipc_subclass"),
                ipc.get("ipc_main_group"),
            ],
        )
    if not p.get("ipc"):
        conn.execute(
            """INSERT INTO patent_classes
               (patent_no, uspc_mainclass, uspc_subclass,
                ipc_section, ipc_class, ipc_subclass, ipc_main_group)
               VALUES (?,?,?,NULL,NULL,NULL,NULL)""",
            [p["patent_no"], p.get("uspc_mainclass"), p.get("uspc_subclass")],
        )

    return True


def load_seed(conn: duckdb.DuckDBPyConnection) -> int:
    added = 0
    for s in SEED_PATENTS:
        p = dict(s)
        p["inventors"] = [
            (f"{fn} {ln}".strip(), city, state)
            for fn, ln, city, state in s["inventors"]
        ]
        if insert_patent(conn, p):
            added += 1
            print(f"  seeded  US{p['patent_no']}  {p['title']!r}")
    conn.commit()
    return added


# ---------------------------------------------------------------------------
# PatentsView API fetch
# ---------------------------------------------------------------------------

def _build_query(uspc_class: str) -> dict:
    return {
        "_and": [
            {"_gte": {"grant_date": START_DATE}},
            {"_lte": {"grant_date": END_DATE}},
            {"uspc_primary_class.mainclass_id": uspc_class},
        ]
    }


def _parse_hit(hit: dict, uspc_class: str) -> dict:
    assignees = hit.get("assignees") or []
    primary = assignees[0] if assignees else {}

    inventors_raw = hit.get("inventors") or []
    inventors = [
        (
            f"{inv.get('inventor_name_first','')} {inv.get('inventor_name_last','')}".strip(),
            inv.get("inventor_city"),
            inv.get("inventor_state"),
        )
        for inv in inventors_raw
    ]

    uspc = hit.get("uspc_primary_class") or {}
    ipc_list = hit.get("ipc_classes") or []

    return {
        "patent_no":      hit.get("patent_id", "").lstrip("US"),
        "title":          hit.get("patent_title"),
        "app_dt":         hit.get("app_date"),
        "grant_dt":       hit.get("grant_date"),
        "abstract":       hit.get("patent_abstract"),
        "assignee_name":  primary.get("assignee_organization"),
        "assignee_city":  primary.get("assignee_city"),
        "assignee_state": primary.get("assignee_state"),
        "inventors":      inventors,
        "uspc_mainclass": uspc.get("mainclass_id") or uspc_class,
        "uspc_subclass":  uspc.get("subclass_id"),
        "ipc":            [
            {
                "ipc_section":    i.get("ipc_section"),
                "ipc_class":      i.get("ipc_class"),
                "ipc_subclass":   i.get("ipc_subclass"),
                "ipc_main_group": i.get("ipc_main_group"),
            }
            for i in ipc_list
        ],
    }


def fetch_class(
    conn: duckdb.DuckDBPyConnection,
    uspc_class: str,
    resume: bool = False,
) -> int:
    if resume:
        done = conn.execute(
            "SELECT 1 FROM fetch_log WHERE uspc_class = ?", [uspc_class]
        ).fetchone()
        if done:
            print(f"  skipping class {uspc_class} (already fetched)")
            return 0

    session = requests.Session()
    session.headers.update({"Accept": "application/json"})

    q = _build_query(uspc_class)
    page = 1
    total_added = 0
    pages_fetched = 0
    total_hits = None

    while True:
        params = {
            "q":        str(q).replace("'", '"'),
            "f":        str(FIELDS).replace("'", '"'),
            "s":        '[{"grant_date":"asc"}]',
            "per_page": PER_PAGE,
            "page":     page,
        }

        try:
            resp = session.get(API_BASE, params=params, timeout=30)
        except requests.exceptions.ConnectionError as e:
            print(f"\n  ERROR: Cannot reach {API_BASE}")
            print(f"  {e}")
            print("  Run from a network with access to search.patentsview.org")
            print("  Use --seed-only to load manually-curated seed patents instead.")
            sys.exit(1)

        if resp.status_code != 200:
            print(f"  HTTP {resp.status_code} on page {page}: {resp.text[:200]}")
            break

        data = resp.json()
        if total_hits is None:
            total_hits = data.get("total_hits", 0)
            print(f"  class {uspc_class}: {total_hits:,} patents total")

        hits = data.get("hits", [])
        if not hits:
            break

        batch_added = 0
        for hit in hits:
            p = _parse_hit(hit, uspc_class)
            if p["patent_no"] and insert_patent(conn, p):
                batch_added += 1

        conn.commit()
        pages_fetched += 1
        total_added += batch_added
        print(f"    page {page:4d}  +{batch_added:4d}  total {total_added:,}", end="\r")

        if len(hits) < PER_PAGE:
            break
        page += 1
        time.sleep(RATE_SLEEP)

    print(f"    class {uspc_class}: {total_added:,} patents added ({pages_fetched} pages)        ")

    conn.execute(
        "INSERT INTO fetch_log (uspc_class, fetch_dt, pages_fetched, patents_added) VALUES (?,?,?,?)",
        [uspc_class, datetime.now(), pages_fetched, total_added],
    )
    conn.commit()
    return total_added


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build patents.duckdb from PatentsView API (1900–1939, information-system USPC classes)"
    )
    parser.add_argument(
        "--db", default=DB_PATH, help=f"Output database path (default: {DB_PATH})"
    )
    parser.add_argument(
        "--classes",
        nargs="+",
        default=list(USPC_CLASSES),
        metavar="CLASS",
        help=f"USPC classes to fetch (default: {' '.join(USPC_CLASSES)})",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Skip classes already recorded in fetch_log",
    )
    parser.add_argument(
        "--seed-only",
        action="store_true",
        help="Load seed patents only, skip API calls (works without network access)",
    )
    args = parser.parse_args()

    conn = init_db(args.db)
    print(f"Database: {args.db}")

    print("\nLoading seed patents ...")
    n = load_seed(conn)
    print(f"  {n} seed patents added")

    if args.seed_only:
        print("\n--seed-only: skipping API fetch.")
        conn.close()
        return

    print(f"\nFetching classes: {', '.join(args.classes)}")
    print(f"Date range: {START_DATE} – {END_DATE}")
    print(f"API: {API_BASE}\n")

    grand_total = 0
    for cls in args.classes:
        desc = USPC_CLASSES.get(cls, "")
        print(f"USPC {cls}  {desc}")
        grand_total += fetch_class(conn, cls, resume=args.resume)

    conn.close()

    print(f"\nDone. {grand_total:,} patents added.")
    print(f"Database: {Path(args.db).resolve()}")


if __name__ == "__main__":
    main()
