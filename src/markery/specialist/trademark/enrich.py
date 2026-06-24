"""TSDR enrichment: fetch mark images and case status into trademarks.duckdb.

Two entry points:

    store_mark_image(serial_no, client, conn)
        Fetch PNG from TSDR, upsert BLOB into mark_images. Idempotent.

    store_case_status(serial_no, client, conn)
        Fetch case status from TSDR, upsert into extended_marks. Idempotent.

    enrich_project(project, client, conn, source, min_score, force)
        Enrich all marks referenced in a project's confirmed or candidates file.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import duckdb

from markery.common.project import Project
from markery.specialist.trademark.tsdr_client import TSDRClient


def store_mark_image(
    serial_no: str,
    client: TSDRClient,
    conn: duckdb.DuckDBPyConnection,
    force: bool = False,
) -> bool:
    """Fetch PNG from TSDR and store as a file via the asset layer. Returns True if stored."""
    from markery.common.assets import store_mark_image as _store

    existing = conn.execute(
        "SELECT file FROM mark_images WHERE serial_no = ?", [serial_no]
    ).fetchone()

    if existing and existing[0] is not None and not force:
        return False  # already stored

    png_bytes = client.fetch_mark_image(serial_no)
    if png_bytes is None:
        return False

    _store(conn, serial_no, png_bytes, fetched_dt=date.today())
    return True


def store_case_status(
    serial_no: str,
    client: TSDRClient,
    conn: duckdb.DuckDBPyConnection,
    force: bool = False,
) -> bool:
    """Fetch case status from TSDR and upsert into extended_marks. Returns True if stored."""
    existing = conn.execute(
        "SELECT fetched_dt FROM extended_marks WHERE serial_no = ?", [serial_no]
    ).fetchone()

    if existing and not force:
        return False  # already stored

    parsed = client.fetch_case_status(serial_no)
    if parsed is None:
        return False

    today    = date.today()
    raw_json = parsed.get("raw_json") or ""

    if existing:
        conn.execute(
            """UPDATE extended_marks
               SET mark_text = ?, filing_dt = ?, registration_no = ?,
                   registration_dt = ?, status_cd = ?, goods_desc = ?,
                   intl_class = ?, first_use_dt = ?, first_use_comm_dt = ?,
                   raw_json = ?, fetched_dt = ?
               WHERE serial_no = ?""",
            [
                parsed["mark_text"], parsed["filing_dt"],
                parsed["registration_no"], parsed["registration_dt"],
                parsed["status_cd"], parsed["goods_desc"],
                parsed["intl_class"], parsed["first_use_dt"],
                parsed["first_use_comm_dt"], raw_json, today, serial_no,
            ],
        )
    else:
        conn.execute(
            """INSERT INTO extended_marks
               (serial_no, mark_text, filing_dt, registration_no,
                registration_dt, status_cd, goods_desc, intl_class,
                owner_name, first_use_dt, first_use_comm_dt, raw_json, fetched_dt)
               VALUES (?,?,?,?,?,?,?,?,NULL,?,?,?,?)""",
            [
                serial_no, parsed["mark_text"], parsed["filing_dt"],
                parsed["registration_no"], parsed["registration_dt"],
                parsed["status_cd"], parsed["goods_desc"],
                parsed["intl_class"], parsed["first_use_dt"],
                parsed["first_use_comm_dt"], raw_json, today,
            ],
        )
    conn.commit()
    return True


def enrich_project(
    project: str,
    client: TSDRClient,
    conn: duckdb.DuckDBPyConnection,
    source: str = "confirmed",
    min_score: float = 0.0,
    force: bool = False,
) -> dict[str, int]:
    """Fetch images and status for all marks referenced in a project.

    source: "confirmed" reads confirmed.jsonl; "candidates" reads candidates.jsonl
            filtered by min_score.
    Returns {"images": n_stored, "status": n_stored}.
    """
    proj = Project(project)
    if source == "from-variants":
        serial_nos = _collect_serials_from_variants(proj.root / "variants.csv", conn)
    else:
        serial_nos = _collect_serial_nos(proj, source, min_score)

    if not serial_nos:
        return {"images": 0, "status": 0}

    images_stored = 0
    status_stored = 0
    for sno in serial_nos:
        if store_mark_image(sno, client, conn, force=force):
            images_stored += 1
            print(f"  {sno}: image stored")
        if store_case_status(sno, client, conn, force=force):
            status_stored += 1
            print(f"  {sno}: status stored")

    return {"images": images_stored, "status": status_stored}


def backfill_structured_fields(conn: duckdb.DuckDBPyConnection) -> int:
    """Re-parse stored raw_json to populate NULL structured columns.

    Useful when _parse_case_status was updated after rows were already written.
    No API calls are made. Returns the count of rows updated.
    """
    from markery.specialist.trademark.tsdr_client import _parse_case_status

    rows = conn.execute(
        "SELECT serial_no, raw_json FROM extended_marks "
        "WHERE raw_json IS NOT NULL AND raw_json != '' "
        "AND mark_text IS NULL"
    ).fetchall()

    updated = 0
    for serial_no, raw_json_str in rows:
        try:
            data = json.loads(raw_json_str)
        except (json.JSONDecodeError, TypeError):
            continue
        parsed = _parse_case_status(data, serial_no)
        conn.execute(
            """UPDATE extended_marks
               SET mark_text = ?, filing_dt = ?, registration_no = ?,
                   registration_dt = ?, status_cd = ?, goods_desc = ?,
                   intl_class = ?, owner_name = ?, first_use_dt = ?,
                   first_use_comm_dt = ?
               WHERE serial_no = ?""",
            [
                parsed["mark_text"], parsed["filing_dt"],
                parsed["registration_no"], parsed["registration_dt"],
                parsed["status_cd"], parsed["goods_desc"],
                parsed["intl_class"], parsed["owner_name"],
                parsed["first_use_dt"], parsed["first_use_comm_dt"],
                serial_no,
            ],
        )
        updated += 1

    conn.commit()
    return updated


def _collect_serial_nos(
    proj: Project, source: str, min_score: float
) -> list[str]:
    if source == "confirmed":
        path = proj.confirmed
    else:
        path = proj.candidates

    if not path.exists():
        return []

    seen: set[str] = set()
    serial_nos: list[str] = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if source == "candidates" and row.get("score", 0) < min_score:
            continue
        sno = str(row.get("trademark_serial", ""))
        if sno and sno not in seen:
            seen.add(sno)
            serial_nos.append(sno)
    return serial_nos


def _collect_serials_from_variants(
    variants_path: Path,
    conn_tm: duckdb.DuckDBPyConnection,
) -> list[str]:
    """Return serial_nos for all owner names matching trademark variants.

    Reads trademark_owner and trademark_search variant names from variants_path,
    looks them up case-insensitively in the owner table, and returns the
    distinct serial_nos as strings. Returns [] if variants_path does not exist.
    """
    import csv as _csv

    if not variants_path.exists():
        return []

    with variants_path.open(newline="", encoding="utf-8") as f:
        rows = list(_csv.DictReader(f))

    variant_names = list({
        r["variant_name"] for r in rows
        if r.get("source") in ("trademark_owner", "trademark_search")
    })
    if not variant_names:
        return []

    placeholders = ",".join("?" * len(variant_names))
    upper_names = [v.upper() for v in variant_names]
    serial_rows = conn_tm.execute(
        f"SELECT DISTINCT CAST(serial_no AS VARCHAR) FROM owner "
        f"WHERE UPPER(own_name) IN ({placeholders})",
        upper_names,
    ).fetchall()
    return [r[0] for r in serial_rows]
