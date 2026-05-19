"""Single-patent fetch operations for patents.duckdb.

Used by `markery patent pull` and `markery patent citations` (Phase 6D).
Distinct from build.py, which handles bulk CPC-class/year-window ingestion.
All DB connections are accepted as arguments so callers control lifetime
and tests can pass in-memory connections.
"""

from __future__ import annotations

import duckdb

from markery.specialist.patent.epo_client import EPOClient


def upsert_patent(conn: duckdb.DuckDBPyConnection, record: dict) -> None:
    """Upsert one patent record into patents + patent_classes + patent_inventors.

    On insert: populates all three tables.
    On update: overwrites the patents row; deletes and re-inserts CPC and
    inventor rows so new data from EPO replaces stale data.
    """
    pno      = record["patent_no"]
    existing = conn.execute(
        "SELECT 1 FROM patents WHERE patent_no = ?", [pno]
    ).fetchone()

    if existing:
        conn.execute(
            """UPDATE patents
               SET title=?, app_dt=?, grant_dt=?, abstract=?,
                   assignee_name=?, assignee_city=?, assignee_state=?
               WHERE patent_no=?""",
            [
                record.get("title"),     record.get("app_dt"),
                record.get("grant_dt"),  record.get("abstract"),
                record.get("assignee_name"), record.get("assignee_city"),
                record.get("assignee_state"), pno,
            ],
        )
        conn.execute("DELETE FROM patent_classes   WHERE patent_no = ?", [pno])
        conn.execute("DELETE FROM patent_inventors WHERE patent_no = ?", [pno])
    else:
        conn.execute(
            """INSERT INTO patents
               (patent_no, title, app_dt, grant_dt, abstract,
                assignee_name, assignee_city, assignee_state)
               VALUES (?,?,?,?,?,?,?,?)""",
            [
                pno,                     record.get("title"),
                record.get("app_dt"),    record.get("grant_dt"),
                record.get("abstract"),  record.get("assignee_name"),
                record.get("assignee_city"), record.get("assignee_state"),
            ],
        )

    for inv in record.get("inventors", []):
        conn.execute(
            "INSERT INTO patent_inventors (patent_no, inventor_name) VALUES (?,?)",
            [pno, inv],
        )

    cpc_list = record.get("cpc", [])
    for sym in (cpc_list or [None]):
        conn.execute(
            "INSERT INTO patent_classes (patent_no, cpc_class, cpc_full) VALUES (?,?,?)",
            [pno, sym[:4] if sym and len(sym) >= 4 else sym, sym],
        )

    conn.commit()


def fetch_patent_record(
    patent_no: str,
    client: EPOClient,
    conn: duckdb.DuckDBPyConnection,
) -> bool:
    """Fetch biblio + abstract for patent_no from EPO and upsert.

    Returns True if the record was stored (found on EPO), False if not found.
    Abstract is fetched separately if the biblio response does not include it.
    """
    record = client.fetch_biblio(patent_no)
    if not record:
        return False
    if not record.get("abstract"):
        record["abstract"] = client.fetch_abstract(patent_no)
    upsert_patent(conn, record)
    return True


def fetch_citation_chain(
    patent_no: str,
    client: EPOClient,
    conn: duckdb.DuckDBPyConnection,
) -> int:
    """Fetch backward citations for patent_no; pull any not yet in patents.duckdb.

    Returns the count of new patents added. Patents already present in the DB
    are skipped without an API call.
    """
    cited_nos = client.fetch_citations(patent_no)
    if not cited_nos:
        return 0

    new_count = 0
    for cited_no in cited_nos:
        if conn.execute(
            "SELECT 1 FROM patents WHERE patent_no = ?", [cited_no]
        ).fetchone():
            continue
        ok = fetch_patent_record(cited_no, client, conn)
        if ok:
            new_count += 1
            print(f"  {cited_no}: fetched")
        else:
            print(f"  {cited_no}: not found on EPO")

    return new_count
