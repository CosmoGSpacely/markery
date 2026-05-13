#!/usr/bin/env python3
"""
build_patents_db.py

Build patents.duckdb from the EPO Open Patent Services (OPS) API.

Fetches US patents granted 1900–1939 in CPC classes relevant to
pre-computer information systems, then loads them into a local DuckDB
database for cross-referencing against trademarks.duckdb.

Requirements:
  pip install duckdb requests python-dotenv  (all in requirements.txt)
  EPO_CONSUMER_KEY and EPO_CONSUMER_SECRET in .env
  (Register free at https://developers.epo.org)

Usage:
  python build_patents_db.py                       # full build, all classes
  python build_patents_db.py --classes B42F B42D   # specific classes only
  python build_patents_db.py --resume              # skip already-fetched classes
  python build_patents_db.py --seed-only           # load seed patents, skip API
"""

from __future__ import annotations

import argparse
import base64
import os
import sys
import time
from datetime import date, datetime
from pathlib import Path

import duckdb
import requests
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DB_PATH    = "patents.duckdb"
START_YEAR = 1900
END_YEAR   = 1939

# CPC classes for pre-computer information systems.
# Replaces the old USPC classes — EPO OPS uses CPC as its primary system
# and has retroactively classified historical patents.
CPC_CLASSES: dict[str, str] = {
    "B42F": "Filing appliances, card-index systems, loose-leaf binders",
    "B42D": "Books, printed matter, forms, index cards, ledger sheets",
    "B41J": "Typewriters, selective printing mechanisms",
    "B41L": "Addressing and duplicating machines for office use",
    "G06C": "Mechanical calculators, tabulating machines",
    "G06K": "Punched cards, record carriers, recognition of data",
    "G09F": "Displaying, advertising, visible record systems, signs",
}

AUTH_URL   = "https://ops.epo.org/3.2/auth/accesstoken"
SEARCH_URL = "https://ops.epo.org/3.2/rest-services/published-data/search/biblio"

RESULTS_PER_PAGE = 100   # EPO OPS maximum per range request
MAX_PER_QUERY    = 2000  # EPO OPS hard cap per CQL query
RATE_SLEEP       = 0.5   # seconds between requests (fair use)
RETRY_DELAYS     = [5, 15, 30]  # backoff on 503 throttle

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
    assignee_name  VARCHAR,
    assignee_city  VARCHAR,
    assignee_state VARCHAR
);

CREATE TABLE IF NOT EXISTS patent_classes (
    patent_no      VARCHAR NOT NULL,
    cpc_class      VARCHAR,   -- e.g. B42F
    cpc_full       VARCHAR    -- full CPC symbol e.g. B42F17/00
);

CREATE TABLE IF NOT EXISTS patent_inventors (
    patent_no      VARCHAR NOT NULL,
    inventor_name  VARCHAR
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
# Seed data
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
# EPO OPS client (OAuth2 client-credentials with auto-refresh)
# ---------------------------------------------------------------------------

class EPOClient:
    def __init__(self, key: str, secret: str) -> None:
        self._key     = key
        self._secret  = secret
        self._token   = ""
        self._expiry  = 0.0
        self._session = requests.Session()
        self._session.headers["Accept"] = "application/json"

    def _refresh(self) -> None:
        creds = base64.b64encode(f"{self._key}:{self._secret}".encode()).decode()
        r = self._session.post(
            AUTH_URL,
            headers={"Authorization": f"Basic {creds}",
                     "Content-Type": "application/x-www-form-urlencoded"},
            data="grant_type=client_credentials",
            timeout=20,
        )
        if r.status_code != 200:
            print(f"\n  ERROR: EPO authentication failed: {r.status_code} {r.text[:200]}")
            sys.exit(1)
        payload      = r.json()
        self._token  = payload["access_token"]
        self._expiry = time.time() + int(payload.get("expires_in", 1200)) - 60
        self._session.headers["Authorization"] = f"Bearer {self._token}"

    def get(self, url: str, **kwargs) -> requests.Response:
        if time.time() >= self._expiry:
            self._refresh()
        for attempt, delay in enumerate([0] + RETRY_DELAYS):
            if delay:
                time.sleep(delay)
            r = self._session.get(url, **kwargs)
            if r.status_code != 503:
                return r
            if attempt < len(RETRY_DELAYS):
                print(f"  throttled, retrying in {RETRY_DELAYS[attempt]}s ...")
        return r


# ---------------------------------------------------------------------------
# OPS response helpers
# ---------------------------------------------------------------------------

def _text(v) -> str:
    """Extract text from an OPS JSON value (text lives in '$' key)."""
    if isinstance(v, dict):
        return v.get("$", "")
    return str(v) if v else ""


def _list(v) -> list:
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


def _first_date(doc_ids) -> date | None:
    for d in _list(doc_ids):
        if isinstance(d, dict) and d.get("date"):
            raw = _text(d["date"]).replace("-", "")
            try:
                return datetime.strptime(raw[:8], "%Y%m%d").date()
            except ValueError:
                pass
    return None


def _parse_exchange_doc(doc: dict) -> dict | None:
    """Parse one exchange-document into a flat dict for insert_patent()."""
    country    = doc.get("@country", "")
    doc_number = doc.get("@doc-number", "")
    kind       = doc.get("@kind", "")
    if not doc_number or country != "US":
        return None

    patent_no = f"{country}{doc_number}{kind}"
    bib       = doc.get("bibliographic-data", {})

    # Title — prefer English when multiple language variants
    title_raw = bib.get("invention-title")
    if isinstance(title_raw, list):
        en = next((t for t in title_raw
                   if isinstance(t, dict) and t.get("@lang") == "en"), title_raw[0])
        title_raw = en
    title = _text(title_raw).strip().title() if title_raw else None

    # Dates
    pub_ref  = bib.get("publication-reference", {})
    app_ref  = bib.get("application-reference", {})
    grant_dt = _first_date(_list(pub_ref.get("document-id")))
    app_dt   = _first_date(_list(app_ref.get("document-id")))

    # Applicant / assignee (first epodoc-format entry)
    assignee_name = None
    parties       = bib.get("parties", {})
    applicant_list = _list(parties.get("applicants", {}).get("applicant"))
    for ap in applicant_list:
        if isinstance(ap, dict) and ap.get("@data-format") == "epodoc":
            assignee_name = _text(ap.get("applicant-name", {}).get("name")).strip() or None
            break
    if not assignee_name and applicant_list:
        ap = applicant_list[0]
        if isinstance(ap, dict):
            assignee_name = _text(
                ap.get("applicant-name", {}).get("name")
            ).strip() or None

    # Inventors
    inventors = []
    for inv in _list(parties.get("inventors", {}).get("inventor")):
        if isinstance(inv, dict) and inv.get("@data-format") == "epodoc":
            name = _text(inv.get("inventor-name", {}).get("name")).strip()
            if name:
                inventors.append(name)

    # CPC classifications
    cpc_symbols = []
    for pc in _list(bib.get("patent-classifications", {}).get("patent-classification")):
        if isinstance(pc, dict):
            scheme = pc.get("classification-scheme", {})
            if isinstance(scheme, dict) and scheme.get("@scheme", "").upper() in ("CPC", "CPCI"):
                section   = _text(pc.get("section"))
                cls       = _text(pc.get("class"))
                subclass  = _text(pc.get("subclass"))
                maingroup = _text(pc.get("main-group"))
                subgroup  = _text(pc.get("subgroup"))
                symbol    = f"{section}{cls}{subclass}{maingroup}/{subgroup}".strip("/")
                if symbol:
                    cpc_symbols.append(symbol)

    # Abstract (present with full-cycle constituent; absent in biblio-only — stored NULL)
    abstract = None
    abs_raw  = doc.get("abstract")
    if abs_raw:
        p = abs_raw.get("p") if isinstance(abs_raw, dict) else None
        if p:
            abstract = _text(p).strip() or None

    return {
        "patent_no":      patent_no,
        "title":          title,
        "app_dt":         str(app_dt)   if app_dt   else None,
        "grant_dt":       str(grant_dt) if grant_dt else None,
        "abstract":       abstract,
        "assignee_name":  assignee_name,
        "assignee_city":  None,
        "assignee_state": None,
        "inventors":      inventors,
        "cpc":            cpc_symbols,
    }


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def init_db(db_path: str) -> duckdb.DuckDBPyConnection:
    conn = duckdb.connect(db_path)
    conn.execute(DDL)
    return conn


def insert_patent(conn: duckdb.DuckDBPyConnection, p: dict) -> bool:
    """Insert one patent. Returns True if newly inserted."""
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
    if cpc_list:
        for sym in cpc_list:
            conn.execute(
                "INSERT INTO patent_classes (patent_no, cpc_class, cpc_full) VALUES (?,?,?)",
                [p["patent_no"], sym[:4] if len(sym) >= 4 else sym, sym],
            )
    else:
        conn.execute(
            "INSERT INTO patent_classes (patent_no, cpc_class, cpc_full) VALUES (?,?,?)",
            [p["patent_no"], None, None],
        )

    return True


def load_seed(conn: duckdb.DuckDBPyConnection) -> int:
    added = 0
    for s in SEED_PATENTS:
        if insert_patent(conn, s):
            added += 1
            print(f"  seeded  {s['patent_no']}  {s['title']!r}")
    conn.commit()
    return added


# ---------------------------------------------------------------------------
# EPO OPS fetch
# ---------------------------------------------------------------------------

def _cql(cpc_class: str, year_start: int, year_end: int) -> str:
    return f'cpc={cpc_class} AND pd within "{year_start}0101,{year_end}1231" AND pn=US'


def _search_page(
    client: EPOClient,
    cql:    str,
    start:  int,
    end:    int,
) -> tuple[int, list[dict]]:
    """Fetch one page of biblio search results. Returns (total, patents)."""
    r = client.get(
        SEARCH_URL,
        params={"q": cql},
        headers={"X-OPS-Range": f"{start}-{end}"},
        timeout=30,
    )
    time.sleep(RATE_SLEEP)

    if r.status_code == 404:
        return 0, []
    if r.status_code != 200:
        print(f"  HTTP {r.status_code}: {r.text[:200]}")
        return 0, []

    data   = r.json()
    search = data.get("ops:world-patent-data", {}).get("ops:biblio-search", {})
    total  = int(search.get("@total-result-count", 0))

    patents = []
    docs_container = (
        search
        .get("ops:search-result", {})
        .get("exchange-documents", {})
    )
    # exchange-documents is a list of {"exchange-document": doc_or_list} wrappers,
    # or a single such dict when only one result is returned
    for item in _list(docs_container):
        if isinstance(item, dict):
            inner = item.get("exchange-document", item)
        else:
            inner = item
        # inner may itself be a list (patent-family members); take first US match
        for doc in (_list(inner) if isinstance(inner, list) else [inner]):
            parsed = _parse_exchange_doc(doc)
            if parsed:
                patents.append(parsed)
                break

    return total, patents


def fetch_class_window(
    conn:       duckdb.DuckDBPyConnection,
    client:     EPOClient,
    cpc_class:  str,
    year_start: int,
    year_end:   int,
) -> int:
    """Fetch all pages for one CPC class + year window. Returns patents added."""
    cql = _cql(cpc_class, year_start, year_end)

    total, first_page = _search_page(client, cql, 1, RESULTS_PER_PAGE)
    if total == 0:
        return 0

    if total > MAX_PER_QUERY:
        print(f"    {cpc_class} {year_start}–{year_end}: {total} results — subdividing by year")
        added = 0
        for yr in range(year_start, year_end + 1):
            added += fetch_class_window(conn, client, cpc_class, yr, yr)
        return added

    added = sum(1 for p in first_page if insert_patent(conn, p))

    page_start = RESULTS_PER_PAGE + 1
    while page_start <= min(total, MAX_PER_QUERY):
        page_end = min(page_start + RESULTS_PER_PAGE - 1, total, MAX_PER_QUERY)
        _, page_patents = _search_page(client, cql, page_start, page_end)
        added += sum(1 for p in page_patents if insert_patent(conn, p))
        page_start = page_end + 1

    conn.commit()
    return added


def fetch_class(
    conn:       duckdb.DuckDBPyConnection,
    client:     EPOClient,
    cpc_class:  str,
    resume:     bool = False,
    year_start: int  = START_YEAR,
    year_end:   int  = END_YEAR,
) -> int:
    """Fetch all patents for one CPC class across the given year range. Returns total added."""
    grand_total = 0
    # 5-year windows keep each query well under the 2000-result cap
    windows = [
        (y, min(y + 4, year_end))
        for y in range(year_start, year_end + 1, 5)
    ]

    for year_start, year_end in windows:
        if resume:
            if conn.execute(
                "SELECT 1 FROM fetch_log WHERE cpc_class=? AND year_start=? AND year_end=?",
                [cpc_class, year_start, year_end],
            ).fetchone():
                print(f"    skipping {cpc_class} {year_start}–{year_end} (already fetched)")
                continue

        added = fetch_class_window(conn, client, cpc_class, year_start, year_end)
        grand_total += added
        print(f"    {cpc_class} {year_start}–{year_end}  +{added}")

        conn.execute(
            "INSERT INTO fetch_log (cpc_class, year_start, year_end, fetch_dt, patents_added) "
            "VALUES (?,?,?,?,?)",
            [cpc_class, year_start, year_end, datetime.now(), added],
        )
        conn.commit()

    return grand_total


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build patents.duckdb from EPO OPS API "
                    "(US patents 1900–1939, pre-computer information system CPC classes)"
    )
    parser.add_argument("--db", default=DB_PATH,
                        help=f"Output database path (default: {DB_PATH})")
    parser.add_argument("--classes", nargs="+", default=list(CPC_CLASSES),
                        metavar="CLASS",
                        help=f"CPC classes to fetch (default: {' '.join(CPC_CLASSES)})")
    parser.add_argument("--resume", action="store_true",
                        help="Skip class/year windows already recorded in fetch_log")
    parser.add_argument("--seed-only", action="store_true",
                        help="Load seed patents only, skip API calls")
    parser.add_argument("--year-start", type=int, default=START_YEAR,
                        metavar="YEAR", help=f"First grant year to fetch (default: {START_YEAR})")
    parser.add_argument("--year-end", type=int, default=END_YEAR,
                        metavar="YEAR", help=f"Last grant year to fetch (default: {END_YEAR})")
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

    key    = os.getenv("EPO_CONSUMER_KEY")
    secret = os.getenv("EPO_CONSUMER_SECRET")
    if not key or not secret:
        print("\nERROR: EPO_CONSUMER_KEY and EPO_CONSUMER_SECRET must be set in .env")
        print("Register free at https://developers.epo.org")
        sys.exit(1)

    client = EPOClient(key, secret)

    print(f"\nFetching CPC classes: {', '.join(args.classes)}")
    print(f"Date range: {args.year_start}–{args.year_end}\n")

    grand_total = 0
    for cls in args.classes:
        desc = CPC_CLASSES.get(cls, "")
        print(f"CPC {cls}  {desc}")
        grand_total += fetch_class(conn, client, cls,
                                   resume=args.resume,
                                   year_start=args.year_start,
                                   year_end=args.year_end)

    conn.close()
    print(f"\nDone. {grand_total:,} patents added.")
    print(f"Database: {Path(args.db).resolve()}")


if __name__ == "__main__":
    main()
